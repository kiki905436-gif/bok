from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import re
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import ProxyHandler, Request, build_opener


UI_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = UI_ROOT.parent
VAULT_ROOT = PACKAGE_ROOT / "Bok-Desktop" / "starter-vault"
os.environ["BOK_VAULT_ROOT"] = str(VAULT_ROOT)


def load_preview_module():
    path = UI_ROOT / "web_preview.pyw"
    loader = importlib.machinery.SourceFileLoader("boujoy_web_preview_test", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise RuntimeError("Cannot load web_preview.pyw")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class ProductContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.preview = load_preview_module()
        cls.preview.CACHE.read()
        cls.server = cls.preview.PreviewServer(("127.0.0.1", 0))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}"
        cls.opener = build_opener(ProxyHandler({}))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def request(self, path: str, **kwargs):
        request = Request(f"{self.base_url}{path}", **kwargs)
        return self.opener.open(request, timeout=10)

    def test_focus_project_and_actions_exist(self) -> None:
        active = (VAULT_ROOT / "00-System/Active-Context.md").read_text(encoding="utf-8-sig")
        match = re.search(r"^focus_path:\s*([^\r\n]+)$", active, re.MULTILINE)
        self.assertIsNotNone(match)
        focus_path = match.group(1).strip()
        focus = VAULT_ROOT / focus_path
        self.assertTrue(focus.is_file(), focus_path)
        text = focus.read_text(encoding="utf-8-sig")
        self.assertRegex(text, r"(?m)^#{1,3}\s*(?:后续行动|下一步行动|下一步|Next)\s*$")

    def test_both_frontends_recognize_next_action_heading(self) -> None:
        browser_source = (UI_ROOT / "app.js").read_text(encoding="utf-8-sig")
        desktop_source = (UI_ROOT / "desktop_app.pyw").read_text(encoding="utf-8-sig")
        self.assertIn('"下一步行动"', browser_source)
        self.assertIn('"下一步行动"', desktop_source)

    def test_information_architecture_keeps_capabilities_but_prioritizes_real_work(self) -> None:
        html = (UI_ROOT / "index.html").read_text(encoding="utf-8-sig")
        source = (UI_ROOT / "app.js").read_text(encoding="utf-8-sig")
        polish = (UI_ROOT / "polish.css").read_text(encoding="utf-8-sig")
        quick_note_styles = (UI_ROOT / "quick-note-window.css").read_text(encoding="utf-8-sig")
        expected_entries = (
            ('data-view="overview"', 'aria-label="今天"'),
            ('data-scope="projects"', 'aria-label="项目"'),
            ('data-scope="knowledge"', 'aria-label="知识"'),
            ('data-view="person"', 'aria-label="我的记忆"'),
            ('id="libraryNavGroup"', 'aria-label="展开系统功能"'),
        )
        positions = []
        for marker, label in expected_entries:
            self.assertIn(marker, html)
            self.assertIn(label, html)
            positions.append(html.index(marker))
        self.assertEqual(positions, sorted(positions))
        for scope in ("projects", "knowledge", "content", "prompts", "business", "skills", "all"):
            self.assertIn(f'data-scope="{scope}"', html)
        for route in (
            'data-memory-tab-target="search"',
            'data-memory-tab-target="inbox"',
            'data-memory-tab-target="notes"',
            'data-view="pipeline"',
            'data-view="atlas"',
            'data-view="health"',
            'data-memory-tab-target="settings"',
        ):
            self.assertIn(route, html)
        self.assertIn('view: "overview"', source)
        self.assertNotIn("legacy-nav-routes", html)
        self.assertIn('href="./polish.css?v=20260830-3"', html)
        self.assertIn("UI-only visual layer", polish)
        self.assertIn('--desk-font-display: "Songti SC"', polish)
        self.assertIn("Information architecture v2", polish)
        self.assertIn("KNOWLEDGE_COLLECTIONS", source)
        self.assertIn("STARTER_PLACEHOLDER_PATHS", source)
        self.assertNotIn('"Fusion Pixel"', source)
        self.assertNotIn('"Fusion Pixel"', quick_note_styles)

    def test_cross_platform_launchers_have_safe_dependency_paths(self) -> None:
        macos_source = (UI_ROOT / "open-preview.command").read_text(encoding="utf-8-sig")
        windows_source = (UI_ROOT / "open-preview.cmd").read_text(encoding="utf-8-sig")
        preview_source = (UI_ROOT / "web_preview.pyw").read_text(encoding="utf-8-sig")
        bok_windows_source = (PACKAGE_ROOT / "Bok" / "start-bok.cmd").read_text(encoding="utf-8-sig")
        self.assertIn("codex-primary-runtime/dependencies/python", macos_source)
        self.assertIn('"/opt/homebrew/bin/python3"', macos_source)
        self.assertIn("--ready-file", macos_source)
        self.assertIn("choice /C YN", windows_source)
        self.assertIn("Python.Python.3.12", windows_source)
        self.assertLess(windows_source.index("choice /C YN"), windows_source.index("winget install"))
        self.assertIn(":compatibility", windows_source)
        self.assertIn("仅浏览兼容模式", windows_source)
        self.assertIn('APP_DIR.parent / "Bok"', preview_source)
        self.assertIn("where python", bok_windows_source)
        self.assertIn("exit /b 1", bok_windows_source)

    def test_personal_ui_exposes_review_evidence_permissions_and_cleanup(self) -> None:
        html = (UI_ROOT / "index.html").read_text(encoding="utf-8-sig")
        source = (UI_ROOT / "app.js").read_text(encoding="utf-8-sig")
        for identifier in (
            'id="personView"',
            'id="personGraphPanel"',
            'id="personGraph"',
            'id="personGraphList"',
            'id="personReviewPanel"',
            'id="personEvidencePanel"',
            'id="personTimelineList"',
            'id="personProfileSummary"',
            'id="personPermissionSummary"',
            'id="personCleanupPanel"',
            'id="personConfirmDialog"',
        ):
            self.assertIn(identifier, html)
        self.assertNotIn("window.confirm", source)
        self.assertIn('data-person-action="confirm"', source)
        self.assertIn('data-person-action="forget"', source)
        self.assertIn('bokRequest("person/claims/forget"', source)
        self.assertIn('data-person-action="outcome-negative"', source)
        self.assertIn("ArrowRight", source)
        self.assertIn("state.personData?.claims?.understanding", source)
        self.assertIn("data.claims?.profile", source)
        self.assertIn('learned: "长期观察后形成"', source)
        self.assertNotIn("state.personData?.claims?.pending || []).filter", source)
        self.assertIn("stepAtlasPhysics", source)
        self.assertIn("atlasCamera", source)
        self.assertIn('addEventListener("wheel"', source)
        self.assertIn("atlasNodeAt", source)

    def test_bok_workspace_exposes_complete_safe_write_flow(self) -> None:
        html = (UI_ROOT / "index.html").read_text(encoding="utf-8-sig")
        source = (UI_ROOT / "app.js").read_text(encoding="utf-8-sig")
        for identifier in (
            'id="memoryView"',
            'id="memoryTodayPanel"',
            'id="memorySearchPanel"',
            'id="memoryInboxPanel"',
            'id="memoryNotesPanel"',
            'id="memoryActivityPanel"',
            'id="memorySettingsPanel"',
            'id="quickNoteDialog"',
            'id="documentEditDialog"',
            'id="backupRestoreDialog"',
            'id="memoryPersonalBackupSection"',
        ):
            self.assertIn(identifier, html)
        for route in (
            'bokRequest("today")',
            'bokRequest("search"',
            'bokRequest("quick-notes"',
            'bokRequest("memory/commit"',
            'bokRequest("documents/write"',
            'bokRequest("backups/create"',
            '"backups/restore"',
            'bokRequest("person/backups/create"',
        ):
            self.assertIn(route, source)
        self.assertIn("expected_hash", source)
        self.assertIn("confirm_important", source)
        self.assertIn("bok.quick-note-draft.v2", source)
        self.assertIn("24 * 60 * 60 * 1000", source)

    def test_floating_quick_note_reuses_bok_without_a_second_store(self) -> None:
        html = (UI_ROOT / "quick-note.html").read_text(encoding="utf-8-sig")
        source = (UI_ROOT / "quick-note-window.js").read_text(encoding="utf-8-sig")
        app = (UI_ROOT / "app.js").read_text(encoding="utf-8-sig")
        self.assertIn('id="noteValue"', html)
        self.assertIn('/api/bok/v1/quick-notes', source)
        self.assertIn('/api/heartbeat', source)
        self.assertIn('source: "boujoy-ui-floating"', source)
        self.assertNotIn("indexedDB", source)
        self.assertIn("window.open(url.href, windowName", app)
        self.assertIn('fetch("/api/native/quick-note"', app)
        self.assertIn('fetch("/api/native/select-vault"', app)
        self.assertIn('fetch("/api/native/connect-codex"', app)
        self.assertIn("state.nativeShell", app)
        self.assertIn("state.nativeFolderPicker", app)
        self.assertIn("window.location.assign(result.url)", app)
        self.assertIn("await readNativeShellStatus()", app)
        self.assertIn('button.addEventListener("click", openQuickNoteWindow)', app)
        self.assertIn('window.location.port || "local"', app)
        self.assertNotIn('button.addEventListener("click", openQuickNote)', app)
        self.assertIn("草稿已保留", source)

        with self.request("/quick-note.html") as response:
            self.assertEqual(response.status, 200)
            self.assertIn("text/html", response.headers["Content-Type"])

    def test_server_refresh_closes_a_reader_for_a_removed_file(self) -> None:
        browser_source = (UI_ROOT / "app.js").read_text(encoding="utf-8-sig")
        self.assertRegex(
            browser_source,
            r"state\.currentReaderPath\s*&&\s*!state\.files\.some[\s\S]*?elements\.readerDialog\.close\(\)",
        )

    def test_ui_avoids_redundant_background_work(self) -> None:
        source = (UI_ROOT / "app.js").read_text(encoding="utf-8-sig")
        self.assertIn("if (state.serverSyncing) return;", source)
        self.assertIn('document.visibilityState === "visible"', source)
        self.assertIn("if (state.searchFrame) cancelAnimationFrame(state.searchFrame);", source)
        self.assertIn('view === "memory" && (viewChanged || !state.memoryData)', source)
        self.assertIn('view === "person" && (viewChanged || !state.personData)', source)

    def test_heartbeat_and_vault_etag(self) -> None:
        with self.request("/api/heartbeat") as response:
            heartbeat = json.load(response)
        self.assertTrue(heartbeat["ready"])
        self.assertEqual(heartbeat["service"], "boujoy-knowledge-preview")
        self.assertEqual(heartbeat["version"], 6)
        self.assertFalse(heartbeat["nativeShell"])
        self.assertEqual(
            heartbeat["nativeFolderPicker"],
            self.preview.native_folder_picker_available(),
        )

        with self.request("/api/vault") as response:
            etag = response.headers["ETag"]
            self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])
            payload = json.load(response)
        paths = {item["path"] for item in payload["files"]}
        self.assertIn("00-System/Active-Context.md", paths)
        self.assertIn("03-Knowledge/knowledge-card-example.md", paths)
        self.assertFalse(payload["unreadable"])

        request = Request(f"{self.base_url}/api/vault", headers={"If-None-Match": etag})
        with self.assertRaises(HTTPError) as caught:
            self.opener.open(request, timeout=10)
        self.assertEqual(caught.exception.code, 304)

    def test_operational_ontology_projection_replaces_tag_patched_graph(self) -> None:
        source = (UI_ROOT / "app.js").read_text(encoding="utf-8-sig")
        self.assertIn("buildOntologyAtlas", source)
        self.assertIn('"verification-gate": "验证门"', source)
        self.assertIn("payload.ontologyGraph", source)
        self.assertNotIn("标签补边", source)
        with tempfile.TemporaryDirectory() as vault_directory:
            vault = Path(vault_directory).resolve()
            (vault / "06-Business").mkdir(parents=True)
            (vault / "06-Business/Operational-Ontology.md").write_text("# FDE 业务本体\n", encoding="utf-8")
            projection_path = vault / ".bok/state/operational-ontology/projection.json"
            projection_path.parent.mkdir(parents=True)
            projection_path.write_text(json.dumps({
                "schema_version": 1,
                "canonical_fingerprint": "abc",
                "canonical_documents": ["06-Business/Operational-Ontology.md"],
                "nodes": [{"id": "ontology:operational", "kind": "ontology", "label": "FDE 业务本体", "path": "06-Business/Operational-Ontology.md"}],
                "edges": [],
            }), encoding="utf-8")
            with patch.object(self.preview, "VAULT_ROOT", vault):
                _, raw_payload = self.preview.VaultCache().read()
        payload = json.loads(raw_payload)
        self.assertEqual(payload["ontologyGraph"]["canonical_fingerprint"], "abc")
        self.assertEqual(payload["ontologyGraph"]["nodes"][0]["kind"], "ontology")

    def test_vault_selection_is_persisted_and_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            vault = root / "vault"
            vault.mkdir()
            selection_file = root / "state" / "vault.json"
            self.preview.save_vault_root(vault, selection_file=selection_file)
            loaded = self.preview.saved_vault_root(
                root / "fallback",
                selection_file=selection_file,
            )
        self.assertEqual(loaded, vault.resolve())

    def test_preview_folder_picker_switches_to_the_selected_local_server(self) -> None:
        headers = {
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "Sec-Fetch-Site": "same-origin",
        }
        with tempfile.TemporaryDirectory() as directory:
            selected = Path(directory).resolve()
            with (
                patch.object(self.preview, "native_folder_picker_available", return_value=True),
                patch.object(self.preview, "choose_native_vault", return_value=selected),
                patch.object(self.preview, "save_vault_root") as save_vault,
                patch.object(
                    self.preview,
                    "launch_selected_vault",
                    return_value="http://127.0.0.1:54321/",
                ) as launch_selected,
            ):
                with self.request(
                    "/api/native/select-vault",
                    data=b"",
                    headers=headers,
                    method="POST",
                ) as response:
                    payload = json.load(response)
        self.assertTrue(payload["native"])
        self.assertEqual(payload["url"], "http://127.0.0.1:54321/")
        save_vault.assert_called_once_with(selected)
        launch_selected.assert_called_once_with(selected)

    def test_vault_path_escape_is_rejected(self) -> None:
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/file?path=../../../../../../../../../../etc/hosts")
        self.assertEqual(caught.exception.code, 403)

    def test_local_asset_response_is_browser_sandboxed(self) -> None:
        path = "03-Knowledge/knowledge-card-example.md"
        with self.request(f"/api/file?path={path}") as response:
            self.assertIn("sandbox", response.headers["Content-Security-Policy"])
            self.assertEqual(response.headers["X-Frame-Options"], "DENY")
            self.assertEqual(
                response.headers["Cross-Origin-Resource-Policy"], "same-origin"
            )

    def test_local_asset_head_and_range_remain_available(self) -> None:
        path = "03-Knowledge/knowledge-card-example.md"
        with self.request(f"/api/file?path={path}", method="HEAD") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers["Accept-Ranges"], "bytes")
            self.assertFalse(response.read())
        with self.request(
            f"/api/file?path={path}", headers={"Range": "bytes=0-9"}
        ) as response:
            self.assertEqual(response.status, 206)
            self.assertTrue(response.headers["Content-Range"].startswith("bytes 0-9/"))
            self.assertEqual(len(response.read()), 10)

    def test_cache_etag_changes_when_a_markdown_file_changes(self) -> None:
        with tempfile.TemporaryDirectory() as vault_directory:
            vault = Path(vault_directory).resolve()
            card = vault / "card.md"
            card.write_text("# Before", encoding="utf-8")
            with patch.object(self.preview, "VAULT_ROOT", vault):
                cache = self.preview.VaultCache()
                first_etag, first_payload = cache.read()
                card.write_text("# After with a different size", encoding="utf-8")
                second_etag, second_payload = cache.read()
        self.assertNotEqual(first_etag, second_etag)
        self.assertNotEqual(first_payload, second_payload)
        self.assertIn("After with a different size", second_payload.decode("utf-8"))

    def test_large_markdown_is_truncated_in_initial_payload_and_keeps_full_hash(self) -> None:
        with tempfile.TemporaryDirectory() as vault_directory:
            vault = Path(vault_directory).resolve()
            content = "# Large\n\n" + ("段落内容。" * 30000) + "END-OF-LARGE-FILE"
            card = vault / "large.md"
            card.write_text(content, encoding="utf-8")
            with patch.object(self.preview, "VAULT_ROOT", vault):
                _, raw_payload = self.preview.VaultCache().read()
            payload = json.loads(raw_payload)
        record = payload["files"][0]
        self.assertTrue(record["truncated"])
        self.assertLessEqual(len(record["text"].encode("utf-8")), self.preview.INITIAL_MARKDOWN_TEXT_BYTES + 3)
        self.assertNotIn("END-OF-LARGE-FILE", record["text"])
        self.assertRegex(record["contentHash"], r"^[0-9a-f]{64}$")

    def test_system_markdown_cannot_be_deleted(self) -> None:
        body = json.dumps({"path": "00-System/Active-Context.md"}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "Sec-Fetch-Site": "same-origin",
        }
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/delete-card", data=body, headers=headers, method="POST")
        self.assertEqual(caught.exception.code, 403)
        self.assertTrue((VAULT_ROOT / "00-System/Active-Context.md").is_file())

    def test_delete_cannot_bypass_protection_with_parent_segments(self) -> None:
        body = json.dumps(
            {"path": "03-Knowledge/../00-System/Active-Context.md"}
        ).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "Sec-Fetch-Site": "same-origin",
        }
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/delete-card", data=body, headers=headers, method="POST")
        self.assertEqual(caught.exception.code, 403)
        self.assertTrue((VAULT_ROOT / "00-System/Active-Context.md").is_file())

    def test_content_markdown_delete_route_remains_available(self) -> None:
        relative = "03-Knowledge/knowledge-card-example.md"
        body = json.dumps({"path": relative}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "Sec-Fetch-Site": "same-origin",
        }
        with patch.object(self.preview.PreviewHandler, "move_to_trash") as move_to_trash:
            with self.request(
                "/api/delete-card", data=body, headers=headers, method="POST"
            ) as response:
                payload = json.load(response)
        self.assertEqual(payload["deleted"], relative)
        move_to_trash.assert_called_once()
        self.assertTrue((VAULT_ROOT / relative).is_file())

    def test_mutating_api_requires_same_origin_browser_proof(self) -> None:
        body = json.dumps({"paths": []}).encode("utf-8")
        with self.assertRaises(HTTPError) as caught:
            self.request(
                "/api/cleanup",
                data=body,
                headers={"Content-Type": "application/json", "Sec-Fetch-Site": "cross-site"},
                method="POST",
            )
        self.assertEqual(caught.exception.code, 403)

    def test_cleanup_status_and_absent_candidates_are_verified_without_failure(self) -> None:
        with self.request("/api/cleanup") as response:
            status = json.load(response)
        self.assertEqual(status["count"], len(status["items"]))
        self.assertEqual(status["already_absent_count"], len(status["already_absent"]))
        self.assertEqual(status["blocked_count"], len(status["blocked"]))
        self.assertTrue(status["verified"])

        headers = {
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "Sec-Fetch-Site": "same-origin",
        }
        body = json.dumps({"paths": status["already_absent"]}).encode("utf-8")
        with self.request("/api/cleanup", data=body, headers=headers, method="POST") as response:
            result = json.load(response)
        self.assertTrue(result["verified"])
        self.assertFalse(result["failed"])
        self.assertFalse(result["remaining"])
        self.assertEqual(result["already_absent"], len(status["already_absent"]))

    def test_bok_bridge_keeps_api_credentials_server_side(self) -> None:
        bridged = SimpleNamespace(
            status=200,
            body=b'{"ready":true,"service":"bok-memory"}',
            content_type="application/json; charset=utf-8",
        )
        with patch.object(self.server.bok_bridge, "forward", return_value=bridged) as forward:
            with self.request("/api/bok/v1/health") as response:
                payload = json.load(response)
        self.assertTrue(payload["ready"])
        args, kwargs = forward.call_args
        self.assertEqual(args, ("GET", "/api/bok/v1/health"))
        self.assertNotIn("Authorization", kwargs["headers"])

    def test_bok_bridge_post_requires_same_origin_browser_proof(self) -> None:
        body = json.dumps({"text": "note"}).encode("utf-8")
        with patch.object(self.server.bok_bridge, "forward") as forward:
            with self.assertRaises(HTTPError) as caught:
                self.request(
                    "/api/bok/v1/quick-notes",
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
        self.assertEqual(caught.exception.code, 403)
        forward.assert_not_called()

    def test_bok_bridge_forwards_same_origin_post_and_idempotency(self) -> None:
        body = json.dumps({"text": "note"}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Idempotency-Key": "preview-note-once",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "Sec-Fetch-Site": "same-origin",
        }
        bridged = SimpleNamespace(
            status=200,
            body=b'{"path":"07-Quick-Notes/note.md"}',
            content_type="application/json; charset=utf-8",
        )
        with patch.object(self.server.bok_bridge, "forward", return_value=bridged) as forward:
            with self.request(
                "/api/bok/v1/quick-notes",
                data=body,
                headers=headers,
                method="POST",
            ) as response:
                payload = json.load(response)
        self.assertEqual(payload["path"], "07-Quick-Notes/note.md")
        _, kwargs = forward.call_args
        self.assertEqual(kwargs["body"], body)
        self.assertEqual(kwargs["headers"]["Idempotency-Key"], "preview-note-once")

    def test_bok_bridge_keeps_agent_credentials_out_of_browser_context(self) -> None:
        for method, route in (
            ("GET", "/api/bok/v1/agents"),
            ("POST", "/api/bok/v1/agents/issue"),
            ("POST", "/api/bok/v1/agents/revoke"),
        ):
            body = b"" if method == "GET" else b"{}"
            response = self.server.bok_bridge.forward(method, route, body=body)
            payload = json.loads(response.body)
            self.assertEqual(response.status, 403)
            self.assertEqual(payload["error"]["code"], "browser_route_forbidden")

    def test_mutating_api_rejects_a_different_local_origin(self) -> None:
        body = json.dumps({"paths": []}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Origin": "http://127.0.0.1:1",
            "Referer": "http://127.0.0.1:1/",
            "Sec-Fetch-Site": "same-origin",
        }
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/cleanup", data=body, headers=headers, method="POST")
        self.assertEqual(caught.exception.code, 403)

    def test_cleanup_cannot_bypass_protection_with_parent_segments(self) -> None:
        relative = "03-Knowledge/../00-System/Active-Context.md"
        body = json.dumps({"paths": [relative]}).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "Sec-Fetch-Site": "same-origin",
        }
        with patch.object(
            self.preview.PreviewHandler,
            "cleanup_candidates",
            return_value={relative},
        ):
            with self.assertRaises(HTTPError) as caught:
                self.request("/api/cleanup", data=body, headers=headers, method="POST")
        self.assertEqual(caught.exception.code, 403)
        self.assertTrue((VAULT_ROOT / "00-System/Active-Context.md").is_file())

    def test_external_markdown_symlink_is_not_indexed(self) -> None:
        with tempfile.TemporaryDirectory() as vault_directory, tempfile.TemporaryDirectory() as outside_directory:
            vault = Path(vault_directory).resolve()
            content = vault / "03-Knowledge"
            content.mkdir()
            external = Path(outside_directory) / "private.md"
            external.write_text("outside-vault-marker", encoding="utf-8")
            link = content / "linked.md"
            try:
                link.symlink_to(external)
            except OSError as error:
                self.skipTest(f"Symlinks are unavailable: {error}")
            with patch.object(self.preview, "VAULT_ROOT", vault):
                _, raw_payload = self.preview.VaultCache().read()
            payload = json.loads(raw_payload)
        self.assertFalse(payload["files"])
        self.assertNotIn("outside-vault-marker", raw_payload.decode("utf-8"))
        self.assertTrue(payload["skipped"])

    def test_bok_runtime_versions_are_not_exposed_as_knowledge(self) -> None:
        with tempfile.TemporaryDirectory() as vault_directory:
            vault = Path(vault_directory).resolve()
            (vault / "03-Knowledge").mkdir()
            (vault / "03-Knowledge/visible.md").write_text("visible-card", encoding="utf-8")
            version = vault / ".bok/versions/v1"
            version.mkdir(parents=True)
            (version / "before.md").write_text("private-old-version", encoding="utf-8")
            with patch.object(self.preview, "VAULT_ROOT", vault):
                _, raw_payload = self.preview.VaultCache().read()
            payload = json.loads(raw_payload)
        paths = {item["path"] for item in payload["files"]}
        self.assertIn("03-Knowledge/visible.md", paths)
        self.assertNotIn(".bok/versions/v1/before.md", paths)
        self.assertNotIn("private-old-version", raw_payload.decode("utf-8"))

    def test_native_backup_reader_also_ignores_bok_runtime(self) -> None:
        source = (UI_ROOT / "desktop_app.pyw").read_text(encoding="utf-8-sig")
        self.assertRegex(source, r"IGNORED_DIRS\s*=\s*\{[\s\S]*?[\"']\.bok[\"']")

    def test_delete_does_not_follow_an_internal_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as vault_directory:
            vault = Path(vault_directory).resolve()
            (vault / "02-Projects").mkdir()
            knowledge = vault / "03-Knowledge"
            knowledge.mkdir()
            target = vault / "02-Projects/real.md"
            target.write_text("keep-me", encoding="utf-8")
            link = knowledge / "linked.md"
            try:
                link.symlink_to(target)
            except OSError as error:
                self.skipTest(f"Symlinks are unavailable: {error}")
            body = json.dumps({"path": "03-Knowledge/linked.md"}).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/",
                "Sec-Fetch-Site": "same-origin",
            }
            with patch.object(self.preview, "VAULT_ROOT", vault):
                with self.assertRaises(HTTPError) as caught:
                    self.request(
                        "/api/delete-card", data=body, headers=headers, method="POST"
                    )
            self.assertEqual(caught.exception.code, 403)
            self.assertEqual(target.read_text(encoding="utf-8"), "keep-me")
            self.assertTrue(link.is_symlink())


if __name__ == "__main__":
    unittest.main(verbosity=2)
