from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from .config import BokConfig
from .markdown import parse_frontmatter, render_frontmatter
from .storage import VaultStorage
from .util import atomic_write_json, canonical_json, read_json, sha256_text, utc_now


OPERATIONAL_ROOT = "06-Business/Projects"
ONTOLOGY_CATALOG_PATH = "06-Business/Operational-Ontology.md"
ONTOLOGY_PROJECTION_RELATIVE_PATH = "state/operational-ontology/projection.json"
ONTOLOGY_PROJECTION_SCHEMA_VERSION = 1

LEGACY_EXACT_PATHS = {
    "02-Projects/codex-experience-vault.md",
    "02-Projects/welcome-to-bok.md",
    "03-Knowledge/knowledge-card-example.md",
}
LEGACY_PREFIXES = ("03-Knowledge/Codex-Experience/",)


def _list_value(value) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if not isinstance(value, str):
        return []
    raw = value.strip().strip("[]")
    return [item.strip().strip("\"'") for item in re.split(r"[,，;；\n]+", raw) if item.strip()]


def _title(body: str, fallback: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", body)
    return match.group(1).strip() if match else fallback


def _section(body: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)",
        body,
    )
    return match.group(1).strip() if match else ""


def _statement(value: str) -> str:
    text = str(value or "").strip()
    text = re.sub(r"\s*_?\(来源：.*?\)_?\s*$", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _bullets(body: str, heading: str) -> List[str]:
    values = []
    for raw in _section(body, heading).splitlines():
        match = re.match(r"^\s*[-*+]\s+(.+?)\s*$", raw)
        if not match:
            continue
        value = _statement(match.group(1))
        if value and value != "—":
            values.append(value)
    return list(dict.fromkeys(values))


def _steps(body: str) -> List[dict]:
    section = _section(body, "闭环步骤")
    matches = list(re.finditer(r"(?m)^###\s+\d+[.)、]?\s*(.+?)\s*$", section))
    values = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        block = section[match.end():end]
        action_lines = []
        for raw in block.strip().splitlines():
            line = raw.strip()
            if not line:
                if action_lines:
                    break
                continue
            if line.startswith("-"):
                break
            action_lines.append(line)
        refs_match = re.search(r"(?m)^-\s*来源：\s*(.+?)\s*$", block)
        refs = _list_value(refs_match.group(1)) if refs_match else []
        values.append({
            "title": match.group(1).strip(),
            "action": " ".join(action_lines).strip(),
            "source_refs": refs,
        })
    return values


class OperationalOntologyProjector:
    """Builds disposable navigation/search/graph views from canonical loops."""

    def __init__(self, config: BokConfig, storage: VaultStorage):
        self.config = config
        self.storage = storage
        self.projection_path = config.state_dir / ONTOLOGY_PROJECTION_RELATIVE_PATH

    @staticmethod
    def _is_canonical_path(relative: str) -> bool:
        return bool(
            relative.startswith(OPERATIONAL_ROOT + "/")
            and (relative.endswith("/Project.md") or "/Scenarios/" in relative)
            and relative.endswith(".md")
        )

    def canonical_documents(self) -> List[dict]:
        documents = []
        for path in self.storage.markdown_files():
            relative = self.storage.relative(path)
            if not self._is_canonical_path(relative):
                continue
            try:
                text = path.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                continue
            frontmatter, body = parse_frontmatter(text)
            document_type = str(frontmatter.get("type", ""))
            if document_type not in {"project-context", "operational-loop"}:
                continue
            documents.append({
                "path": relative,
                "frontmatter": frontmatter,
                "body": body,
                "title": _title(body, Path(relative).stem),
                "content_hash": self.storage.content_hash(relative) or "",
            })
        return sorted(documents, key=lambda item: item["path"])

    @staticmethod
    def _add_node(nodes: Dict[str, dict], node_id: str, **value) -> str:
        existing = nodes.get(node_id)
        if existing is None:
            nodes[node_id] = {"id": node_id, **value}
        else:
            for key, item in value.items():
                if item and not existing.get(key):
                    existing[key] = item
        return node_id

    @staticmethod
    def _add_edge(edges: Dict[str, dict], source: str, target: str, kind: str) -> None:
        if not source or not target or source == target:
            return
        edge_id = sha256_text(f"{source}\n{target}\n{kind}")[:24]
        edges.setdefault(edge_id, {"id": edge_id, "source": source, "target": target, "kind": kind})

    def build_projection(self, documents: Optional[List[dict]] = None) -> dict:
        documents = documents if documents is not None else self.canonical_documents()
        nodes: Dict[str, dict] = {}
        edges: Dict[str, dict] = {}
        root_id = self._add_node(
            nodes,
            "ontology:operational",
            kind="ontology",
            label="FDE 业务本体",
            path=ONTOLOGY_CATALOG_PATH,
            status="generated",
        )
        project_nodes: Dict[str, str] = {}
        project_paths: Dict[str, str] = {}
        for document in documents:
            frontmatter = document["frontmatter"]
            if frontmatter.get("type") != "project-context":
                continue
            project_id = str(frontmatter.get("project_id") or Path(document["path"]).parent.name)
            node_id = f"project:{project_id}"
            project_nodes[project_id] = self._add_node(
                nodes,
                node_id,
                kind="project",
                label=str(frontmatter.get("project_name") or document["title"]).removesuffix(" 项目上下文"),
                path=document["path"],
                project_id=project_id,
                status=str(frontmatter.get("status") or "active"),
            )
            project_paths[project_id] = document["path"]
            self._add_edge(edges, root_id, node_id, "contains")

        for document in documents:
            frontmatter = document["frontmatter"]
            if frontmatter.get("type") != "operational-loop":
                continue
            project_id = str(frontmatter.get("project_id") or Path(document["path"]).parents[1].name)
            scenario_id = str(frontmatter.get("scenario_id") or Path(document["path"]).stem)
            project_node = project_nodes.get(project_id)
            if not project_node:
                project_node = self._add_node(
                    nodes,
                    f"project:{project_id}",
                    kind="project",
                    label=str(frontmatter.get("project_name") or project_id),
                    path=f"{OPERATIONAL_ROOT}/{project_id}/Project.md",
                    project_id=project_id,
                    status="active",
                )
                project_nodes[project_id] = project_node
                project_paths[project_id] = f"{OPERATIONAL_ROOT}/{project_id}/Project.md"
                self._add_edge(edges, root_id, project_node, "contains")
            scenario_node = self._add_node(
                nodes,
                f"scenario:{project_id}:{scenario_id}",
                kind="scenario",
                label=document["title"],
                path=document["path"],
                project_id=project_id,
                scenario_id=scenario_id,
                status=str(frontmatter.get("status") or "draft"),
            )
            self._add_edge(edges, project_node, scenario_node, "contains")

            for object_name in _bullets(document["body"], "业务对象"):
                object_id = f"object:{project_id}:{sha256_text(object_name)[:16]}"
                self._add_node(
                    nodes,
                    object_id,
                    kind="business-object",
                    label=object_name,
                    document_path=document["path"],
                    project_id=project_id,
                    scenario_id=scenario_id,
                    status="derived",
                )
                self._add_edge(edges, scenario_node, object_id, "operates-on")

            for index, step in enumerate(_steps(document["body"]), start=1):
                action_id = f"action:{project_id}:{scenario_id}:{sha256_text(step['title'])[:16]}"
                self._add_node(
                    nodes,
                    action_id,
                    kind="action",
                    label=step["title"],
                    description=step["action"],
                    document_path=document["path"],
                    project_id=project_id,
                    scenario_id=scenario_id,
                    ordinal=index,
                    status="derived",
                )
                self._add_edge(edges, scenario_node, action_id, "has-action")
                for source_ref in step["source_refs"]:
                    source_id = f"source:{source_ref}"
                    self._add_node(nodes, source_id, kind="source", label=source_ref, document_path=document["path"], status="evidence")
                    self._add_edge(edges, action_id, source_id, "evidenced-by")

            for gate in _bullets(document["body"], "验证门"):
                gate_id = f"gate:{project_id}:{scenario_id}:{sha256_text(gate)[:16]}"
                self._add_node(
                    nodes,
                    gate_id,
                    kind="verification-gate",
                    label=gate,
                    document_path=document["path"],
                    project_id=project_id,
                    scenario_id=scenario_id,
                    status="derived",
                )
                self._add_edge(edges, scenario_node, gate_id, "verified-by")

            for source_ref in _list_value(frontmatter.get("source_sessions")):
                source_id = f"source:{source_ref}"
                self._add_node(nodes, source_id, kind="source", label=source_ref, document_path=document["path"], status="evidence")
                self._add_edge(edges, scenario_node, source_id, "evidenced-by")

        fingerprint = sha256_text(canonical_json([
            {"path": item["path"], "content_hash": item["content_hash"]}
            for item in documents
        ]))
        node_values = sorted(nodes.values(), key=lambda item: item["id"])
        edge_values = sorted(edges.values(), key=lambda item: item["id"])
        return {
            "schema_version": ONTOLOGY_PROJECTION_SCHEMA_VERSION,
            "generated_at": utc_now(),
            "canonical_fingerprint": fingerprint,
            "canonical_documents": [item["path"] for item in documents],
            "counts": {
                "documents": len(documents),
                "nodes": len(node_values),
                "edges": len(edge_values),
                "by_kind": dict(sorted(Counter(item["kind"] for item in node_values).items())),
            },
            "nodes": node_values,
            "edges": edge_values,
        }

    def _catalog_document(self, projection: dict, documents: List[dict]) -> str:
        existing_hash = self.storage.content_hash(ONTOLOGY_CATALOG_PATH)
        created_at = ""
        if existing_hash:
            frontmatter, _ = parse_frontmatter(self.storage.read_text(ONTOLOGY_CATALOG_PATH))
            created_at = str(frontmatter.get("created", ""))
        projects = [item for item in documents if item["frontmatter"].get("type") == "project-context"]
        loops = [item for item in documents if item["frontmatter"].get("type") == "operational-loop"]
        loops_by_project: Dict[str, List[dict]] = defaultdict(list)
        for loop in loops:
            loops_by_project[str(loop["frontmatter"].get("project_id") or "unknown")].append(loop)
        now = projection["generated_at"]
        frontmatter = render_frontmatter({
            "id": "operational-ontology",
            "type": "ontology-projection",
            "role": "navigation-index",
            "status": "generated",
            "source": OPERATIONAL_ROOT,
            "canonical_fingerprint": projection["canonical_fingerprint"],
            "schema_version": ONTOLOGY_PROJECTION_SCHEMA_VERSION,
            "created": created_at or now,
            "updated": now,
            "tags": ["operational-ontology", "fde", "agent-runtime"],
        })
        project_blocks = []
        for project in projects:
            project_id = str(project["frontmatter"].get("project_id") or Path(project["path"]).parent.name)
            project_name = str(project["frontmatter"].get("project_name") or project["title"]).removesuffix(" 项目上下文")
            items = loops_by_project.get(project_id, [])
            statuses = Counter(str(item["frontmatter"].get("status") or "draft") for item in items)
            project_blocks.append(
                f"### [[{project['path'].removesuffix('.md')}|{project_name}]]\n\n"
                f"- 可执行闭环：{len(items)}\n"
                f"- 状态：{', '.join(f'{key} {value}' for key, value in sorted(statuses.items())) or '—'}\n"
                + "\n".join(f"- [[{item['path'].removesuffix('.md')}|{item['title']}]] · `{item['frontmatter'].get('status', 'draft')}`" for item in items)
            )
        by_kind = projection["counts"]["by_kind"]
        body = (
            "# FDE 业务本体\n\n"
            "本页是由项目上下文和可执行闭环重建的全局入口；事实仍以项目与场景 Markdown 为准。\n\n"
            "## 系统一致性\n\n"
            f"- 项目：{by_kind.get('project', 0)}\n"
            f"- 业务场景：{by_kind.get('scenario', 0)}\n"
            f"- 业务对象：{by_kind.get('business-object', 0)}\n"
            f"- 业务动作：{by_kind.get('action', 0)}\n"
            f"- 验证门：{by_kind.get('verification-gate', 0)}\n"
            f"- 来源会话：{by_kind.get('source', 0)}\n"
            f"- 图谱：{projection['counts']['nodes']} 个节点 / {projection['counts']['edges']} 条关系\n"
            f"- 本体指纹：`{projection['canonical_fingerprint']}`\n\n"
            "## 项目基线\n\n"
            + ("\n\n".join(project_blocks) if project_blocks else "- 尚无已物化项目。")
            + "\n"
        )
        return frontmatter + body

    def purge_legacy(self) -> dict:
        candidates = []
        for path in self.storage.markdown_files():
            relative = self.storage.relative(path)
            if relative in LEGACY_EXACT_PATHS or any(relative.startswith(prefix) for prefix in LEGACY_PREFIXES):
                candidates.append(relative)
        if not candidates:
            return {"removed": 0, "paths": [], "backup": None, "recoverable": True}
        backup = self.storage.create_backup()
        removed = []
        for relative in sorted(candidates):
            content_hash = self.storage.content_hash(relative)
            if not content_hash:
                continue
            self.storage.delete(relative, expected_hash=content_hash)
            removed.append(relative)
        return {"removed": len(removed), "paths": removed, "backup": backup, "recoverable": True}

    def rebuild(self, *, purge_legacy: bool = False) -> dict:
        cleanup = self.purge_legacy() if purge_legacy else {"removed": 0, "paths": [], "backup": None, "recoverable": True}
        documents = self.canonical_documents()
        projection = self.build_projection(documents)
        self.storage.ensure_state()
        atomic_write_json(self.projection_path, projection)
        catalog_text = self._catalog_document(projection, documents)
        catalog_hash = self.storage.content_hash(ONTOLOGY_CATALOG_PATH)
        catalog_write = self.storage.write(
            ONTOLOGY_CATALOG_PATH,
            catalog_text,
            expected_hash=catalog_hash,
            operation="ontology_catalog_rebuild",
            metadata={"canonical_fingerprint": projection["canonical_fingerprint"]},
        )
        return {
            "status": "rebuilt",
            "catalog": catalog_write.as_dict(),
            "projection_path": str(self.projection_path),
            "projection": {key: projection[key] for key in ("schema_version", "generated_at", "canonical_fingerprint", "counts")},
            "cleanup": cleanup,
        }

    def read(self) -> dict:
        value = read_json(self.projection_path, {})
        if not isinstance(value, dict) or value.get("schema_version") != ONTOLOGY_PROJECTION_SCHEMA_VERSION:
            return {"status": "missing", "counts": {"documents": 0, "nodes": 0, "edges": 0, "by_kind": {}}}
        return {"status": "ready", **value}
