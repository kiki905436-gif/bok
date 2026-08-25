from __future__ import annotations

import ctypes
import os
import queue
import re
import shutil
import subprocess
import threading
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, ttk


APP_DIR = Path(__file__).resolve().parent
VAULT_ROOT = APP_DIR.parent
POLL_MS = 2500

IGNORED_DIRS = {
    ".bok",
    ".cache",
    ".codebuddy",
    ".codex",
    ".git",
    ".agents",
    ".mypy_cache",
    ".nox",
    ".openai",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    ".workbuddy",
    "__pypackages__",
    "node_modules",
    "site-packages",
    "venv",
    "__pycache__",
    "99-Logs",
    "_dist",
}

COLORS = {
    "canvas": "#F4EFE5",
    "paper": "#FFFDF8",
    "white": "#FFFFFF",
    "ink": "#152526",
    "muted": "#687473",
    "line": "#DEDCD5",
    "navy": "#102237",
    "navy_2": "#172D45",
    "teal": "#159A8C",
    "teal_dark": "#08786F",
    "teal_soft": "#E1F3EE",
    "blue": "#2864D7",
    "blue_soft": "#E5EFFF",
    "amber": "#C98714",
    "amber_soft": "#FFF2CE",
    "violet": "#7453C7",
    "violet_soft": "#EEE8FF",
    "coral": "#D66758",
}

FONT_UI = "Microsoft YaHei UI"
FONT_MONO = "Consolas"


@dataclass
class Category:
    key: str
    label: str
    symbol: str
    accent: str
    soft: str


CATEGORIES = [
    (
        "AI-Second-Brain-UI/",
        Category("projects", "项目", "UI", COLORS["teal"], COLORS["teal_soft"]),
    ),
    ("02-Projects/", Category("projects", "项目", "P", COLORS["blue"], COLORS["blue_soft"])),
    ("03-Knowledge/", Category("knowledge", "知识", "K", COLORS["teal"], COLORS["teal_soft"])),
    ("04-Content/", Category("content", "内容", "C", COLORS["amber"], COLORS["amber_soft"])),
    ("05-Prompts/", Category("prompts", "提示词", ">_", COLORS["violet"], COLORS["violet_soft"])),
    ("06-Business/", Category("business", "商业", "B", COLORS["amber"], COLORS["amber_soft"])),
    ("90-Archive/", Category("archive", "归档", "A", COLORS["coral"], "#FBEAE6")),
    (
        "98-Skills/Codex-Skills/",
        Category("skills", "Skill", "S", COLORS["violet"], COLORS["violet_soft"]),
    ),
]

SYSTEM_CATEGORY = Category("system", "系统", "M", COLORS["teal"], COLORS["teal_soft"])


@dataclass
class MarkdownRecord:
    path: str
    title: str
    excerpt: str
    text: str
    updated: str
    tags: list[str]
    aliases: list[str]
    category: Category
    mtime_ns: int
    size: int
    next_actions: str = ""


@dataclass
class VaultFile:
    path: Path
    relative: str
    stat: os.stat_result


def category_for(path: str) -> Category:
    normalized = path.replace("\\", "/")
    for prefix, category in CATEGORIES:
        if normalized.startswith(prefix):
            return category
    return SYSTEM_CATEGORY


def strip_markdown(text: str) -> str:
    text = re.sub(r"^---[\s\S]*?---\s*", "", text)
    text = re.sub(r"```[\s\S]*?```", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[#>*_`~|]", " ", text)
    text = re.sub(r"^\s*[-+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+[.)、]\s+", "", text, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", text).strip()


def parse_frontmatter(text: str) -> dict[str, str | list[str]]:
    match = re.match(r"^---\s*\n([\s\S]*?)\n---", text)
    if not match:
        return {}
    result: dict[str, str | list[str]] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip().strip("'\"")
        if value.startswith("[") and value.endswith("]"):
            result[key] = [
                item.strip().strip("'\"")
                for item in value[1:-1].split(",")
                if item.strip()
            ]
        else:
            result[key] = value
    return result


def section_text(text: str, titles: list[str]) -> str:
    lines = text.splitlines()
    for title in titles:
        heading = re.compile(rf"^#{{1,3}}\s*{re.escape(title)}\s*$", re.IGNORECASE)
        start = next((i for i, line in enumerate(lines) if heading.match(line.strip())), -1)
        if start < 0:
            continue
        collected: list[str] = []
        for line in lines[start + 1 :]:
            if re.match(r"^#{1,3}\s+", line):
                break
            collected.append(line)
        result = strip_markdown("\n".join(collected))
        if result:
            return result
    return ""


def term_list(raw: object) -> list[str]:
    if isinstance(raw, list):
        output: list[str] = []
        for item in raw:
            output.extend(term_list(str(item)))
        return output
    if not isinstance(raw, str):
        return []
    return [
        re.sub(r"^\s*[-*+]\s*", "", item).lstrip("#").strip()
        for item in re.split(r"[,，、;；\n]+", raw)
        if re.sub(r"^\s*[-*+]\s*", "", item).lstrip("#").strip()
    ]


def section_list(text: str, titles: list[str]) -> list[str]:
    wanted = {title.casefold() for title in titles}
    lines = text.splitlines()
    for index, line in enumerate(lines):
        heading = re.match(r"^#{1,3}\s*(.+?)\s*$", line)
        if not heading or heading.group(1).casefold() not in wanted:
            continue
        items: list[str] = []
        for candidate in lines[index + 1 :]:
            if re.match(r"^#{1,3}\s+", candidate):
                break
            item = re.match(r"^\s*[-*+]\s+(.+?)\s*$", candidate)
            if item:
                items.extend(term_list(item.group(1)))
        return items
    return []


def extract_tags(text: str, frontmatter: dict, category: Category) -> list[str]:
    tags: list[str] = []
    tags.extend(term_list(frontmatter.get("tags", [])))
    tags.extend(section_list(text, ["相关标签", "标签", "Tags"]))
    tags.extend(re.findall(r"(?:^|\s)#([\w\u4e00-\u9fff-]{2,24})", text))
    tags.append(category.label)
    output: list[str] = []
    for tag in tags:
        normalized = tag.lstrip("#").strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output[:8]


def extract_aliases(text: str, frontmatter: dict) -> list[str]:
    aliases: list[str] = []
    for key in ("aliases", "alias", "keywords"):
        aliases.extend(term_list(frontmatter.get(key, [])))
    aliases.extend(section_list(text, ["别名", "关键词", "触发词", "相关词", "Aliases"]))
    return list(dict.fromkeys(aliases))[:24]


def parse_record(path: Path, relative: str, stat: os.stat_result) -> MarkdownRecord:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    frontmatter = parse_frontmatter(text)
    category = category_for(relative)
    heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = str(frontmatter.get("title") or (heading.group(1) if heading else path.stem))
    title = strip_markdown(title)
    conclusion = section_text(text, ["一句话结论", "结论", "摘要"])
    body = strip_markdown(text)
    excerpt = conclusion or body.replace(title, "", 1).strip()[:170] or "Markdown 知识卡"
    inline_date = re.search(r"更新时间[：:]\s*(\d{4}-\d{2}-\d{2})", text)
    fm_date = frontmatter.get("updated") or frontmatter.get("date") or frontmatter.get("modified")
    updated = (
        str(fm_date)[:10]
        if fm_date
        else inline_date.group(1)
        if inline_date
        else datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
    )
    return MarkdownRecord(
        path=relative.replace("\\", "/"),
        title=title,
        excerpt=excerpt,
        text=text,
        updated=updated,
        tags=extract_tags(text, frontmatter, category),
        aliases=extract_aliases(text, frontmatter),
        category=category,
        mtime_ns=stat.st_mtime_ns,
        size=stat.st_size,
        next_actions=section_text(text, ["下一步行动", "下一步", "后续行动", "Next"]),
    )


def find_ripgrep() -> str | None:
    executable = shutil.which("rg")
    if executable:
        return executable
    codex_bin = (
        Path.home()
        / "AppData"
        / "Local"
        / "OpenAI"
        / "Codex"
        / "bin"
    )
    candidates = sorted(codex_bin.glob("*/rg.exe"), reverse=True)
    return str(candidates[0]) if candidates else None


def markdown_paths() -> list[Path]:
    ripgrep = find_ripgrep()
    if ripgrep:
        creation_flags = 0x08000000 if os.name == "nt" else 0
        command = [
            ripgrep,
            "--files",
            "--hidden",
            "--no-ignore",
            "-g",
            "*.md",
        ]
        for ignored in sorted(IGNORED_DIRS):
            command.extend(["-g", f"!**/{ignored}/**"])
        result = subprocess.run(
            command,
            cwd=VAULT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=creation_flags,
            check=False,
        )
        if result.returncode in (0, 1):
            return [
                VAULT_ROOT / line.strip()
                for line in result.stdout.splitlines()
                if line.strip()
            ]

    paths: list[Path] = []
    for current, dirs, filenames in os.walk(VAULT_ROOT):
        dirs[:] = sorted(name for name in dirs if name not in IGNORED_DIRS)
        current_path = Path(current)
        paths.extend(
            current_path / filename
            for filename in sorted(filenames)
            if filename.lower().endswith(".md")
        )
    return paths


def snapshot_vault() -> tuple[list[VaultFile], str]:
    files: list[VaultFile] = []
    for path in markdown_paths():
        try:
            stat = path.stat()
            relative = path.relative_to(VAULT_ROOT).as_posix()
            files.append(VaultFile(path=path, relative=relative, stat=stat))
        except (OSError, ValueError):
            continue
    fingerprint = "|".join(
        f"{item.relative}:{item.stat.st_mtime_ns}:{item.stat.st_size}"
        for item in sorted(files, key=lambda entry: entry.relative)
    )
    return files, fingerprint


def load_records(files: list[VaultFile]) -> list[MarkdownRecord]:
    records: list[MarkdownRecord] = []
    for item in files:
        try:
            records.append(parse_record(item.path, item.relative, item.stat))
        except (OSError, UnicodeError):
            continue
    records.sort(key=lambda item: (item.mtime_ns, -len(item.path)), reverse=True)

    index_records = [
        record
        for record in records
        if record.path in ("00-System/Memory-Index.md", "00-System/Hot-Index.md")
    ]
    alias_rules: list[tuple[str, list[str]]] = []
    for index_record in index_records:
        heading = ""
        targets: list[str] = []
        aliases: list[str] = []

        def flush_rule() -> None:
            if targets and aliases:
                terms = list(dict.fromkeys([heading, *aliases]))
                alias_rules.extend(
                    (target.replace("\\", "/"), terms)
                    for target in targets
                )
            targets.clear()
            aliases.clear()

        for line in index_record.text.splitlines():
            heading_match = re.match(r"^#{2,3}\s+(.+?)\s*$", line)
            if heading_match:
                flush_rule()
                heading = strip_markdown(heading_match.group(1))
                continue
            if not heading:
                continue
            if re.match(r"^-\s*(?:位置|入口|工程|小白手册)[：:]", line):
                targets.extend(
                    value.strip()
                    for value in re.findall(r"`([^`\r\n]+)`", line)
                    if value.strip() and not re.search(r"[*?]", value)
                )
            trigger_match = re.match(r"^-\s*触发[：:]\s*(.+?)\s*$", line)
            if trigger_match:
                aliases.extend(term_list(trigger_match.group(1)))
        flush_rule()

    for record in records:
        aliases = list(record.aliases)
        for target, terms in alias_rules:
            if record.path == target or record.path.startswith(f"{target}/"):
                aliases.extend(terms)
        record.aliases = list(dict.fromkeys(aliases))[:40]

    # 多个项目会保留同一份输入模板。文件仍然存在于 Vault 中，
    # 这里只在只读预览层折叠“标题与正文完全相同”的副本。
    unique: dict[str, MarkdownRecord] = {}
    for record in records:
        body = re.sub(r"^---[\s\S]*?---\s*", "", record.text)
        body = re.sub(r"\s+", " ", body).strip().casefold()
        key = f"{record.title.strip().casefold()}\u241f{body}"
        unique.setdefault(key, record)
    return list(unique.values())


def scan_vault() -> tuple[list[MarkdownRecord], str]:
    files, fingerprint = snapshot_vault()
    records = load_records(files)
    return records, fingerprint


class ScrollFrame(tk.Frame):
    def __init__(self, parent: tk.Misc, background: str):
        super().__init__(parent, bg=background)
        self.canvas = tk.Canvas(
            self,
            bg=background,
            highlightthickness=0,
            bd=0,
        )
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.body = tk.Frame(self.canvas, bg=background)
        self.window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.body.bind("<Configure>", self._on_body)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind_all("<MouseWheel>", self._on_wheel, add="+")

    def _on_body(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)

    def _on_wheel(self, event):
        if not self.winfo_exists():
            return
        widget = self.winfo_containing(self.winfo_pointerx(), self.winfo_pointery())
        while widget is not None:
            if widget == self:
                self.canvas.yview_scroll(int(-event.delta / 120), "units")
                return
            widget = widget.master


class KnowledgePreviewApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.records: list[MarkdownRecord] = []
        self.fingerprint = ""
        self.nav_filter = "all"
        self.type_filter = "all"
        self.search_text = ""
        self.selected: MarkdownRecord | None = None
        self.scan_queue: queue.Queue = queue.Queue()
        self.scan_running = False
        self.next_scan_job: str | None = None
        self.closed = False
        self.search_after: str | None = None
        self.nav_buttons: dict[str, tk.Button] = {}
        self.type_buttons: dict[str, tk.Button] = {}

        self._configure_root()
        self._build_layout()
        self._request_scan(initial=True)
        self.root.after(100, self._consume_scan_result)
        self.root.protocol("WM_DELETE_WINDOW", self._close)

    def _configure_root(self):
        self.root.title("Boujoy知识库")
        self.root.configure(bg=COLORS["canvas"])
        self.root.minsize(1180, 720)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        width = min(1680, max(1200, screen_w - 90))
        height = min(980, max(740, screen_h - 110))
        x = max(20, (screen_w - width) // 2)
        y = max(20, (screen_h - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Vertical.TScrollbar",
            background="#D9D6CE",
            troughcolor=COLORS["canvas"],
            bordercolor=COLORS["canvas"],
            arrowcolor=COLORS["muted"],
        )

    def _build_layout(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=0, minsize=260)
        self.root.grid_columnconfigure(1, weight=1, minsize=620)
        self.root.grid_columnconfigure(2, weight=0, minsize=355)

        self.sidebar = tk.Frame(self.root, bg=COLORS["navy"], width=260)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.center = tk.Frame(self.root, bg=COLORS["canvas"])
        self.center.grid(row=0, column=1, sticky="nsew")

        self.context = tk.Frame(
            self.root,
            bg=COLORS["paper"],
            width=355,
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        )
        self.context.grid(row=0, column=2, sticky="nsew")
        self.context.grid_propagate(False)

        self._build_sidebar()
        self._build_center()
        self._build_context()

    def _build_sidebar(self):
        brand = tk.Frame(self.sidebar, bg=COLORS["navy"])
        brand.pack(fill="x", padx=24, pady=(28, 22))
        mark = tk.Label(
            brand,
            text="|||",
            width=3,
            height=1,
            bg=COLORS["teal_dark"],
            fg="#53E1CC",
            font=(FONT_MONO, 18, "bold"),
        )
        mark.pack(side="left", padx=(0, 12))
        brand_text = tk.Frame(brand, bg=COLORS["navy"])
        brand_text.pack(side="left")
        tk.Label(
            brand_text,
            text="Boujoy知识库",
            bg=COLORS["navy"],
            fg="#F5FBFA",
            font=(FONT_UI, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand_text,
            text="LOCAL MARKDOWN VAULT",
            bg=COLORS["navy"],
            fg="#7E9AAF",
            font=(FONT_UI, 8),
        ).pack(anchor="w", pady=(3, 0))

        nav_frame = tk.Frame(self.sidebar, bg=COLORS["navy"])
        nav_frame.pack(fill="x", padx=18)
        nav_items = [
            ("all", "▦", "总览"),
            ("projects", "□", "项目"),
            ("knowledge", "◇", "知识库"),
            ("content", "≡", "内容"),
            ("prompts", ">_", "提示词"),
            ("business", "B", "商业"),
            ("skills", "✦", "Skills"),
            ("archive", "▱", "归档"),
        ]
        for key, symbol, label in nav_items:
            button = tk.Button(
                nav_frame,
                text=f"  {symbol}    {label}",
                anchor="w",
                relief="flat",
                bd=0,
                padx=12,
                pady=12,
                bg=COLORS["teal_dark"] if key == "all" else COLORS["navy"],
                activebackground=COLORS["teal_dark"],
                fg="#FFFFFF" if key == "all" else "#B7C8D5",
                activeforeground="#FFFFFF",
                cursor="hand2",
                font=(FONT_UI, 12),
                command=lambda value=key: self._set_nav_filter(value),
            )
            button.pack(fill="x", pady=3)
            self.nav_buttons[key] = button

        status = tk.Frame(
            self.sidebar,
            bg=COLORS["navy_2"],
            highlightbackground="#274058",
            highlightthickness=1,
        )
        status.pack(side="bottom", fill="x", padx=18, pady=20)
        top = tk.Frame(status, bg=COLORS["navy_2"])
        top.pack(fill="x", padx=15, pady=(15, 7))
        tk.Label(
            top,
            text="本地知识库",
            bg=COLORS["navy_2"],
            fg="#BFD1DC",
            font=(FONT_UI, 10),
        ).pack(side="left")
        self.status_dot = tk.Label(
            top,
            text="●",
            bg=COLORS["navy_2"],
            fg="#60778A",
            font=(FONT_UI, 10),
        )
        self.status_dot.pack(side="right")
        self.file_count_label = tk.Label(
            status,
            text="正在读取…",
            bg=COLORS["navy_2"],
            fg="#FFFFFF",
            font=(FONT_UI, 12, "bold"),
        )
        self.file_count_label.pack(anchor="w", padx=15, pady=(5, 2))
        self.vault_label = tk.Label(
            status,
            text=str(VAULT_ROOT),
            bg=COLORS["navy_2"],
            fg="#7F9AAE",
            font=(FONT_UI, 8),
            wraplength=210,
            justify="left",
        )
        self.vault_label.pack(anchor="w", padx=15, pady=(4, 12))
        self.sync_status_label = tk.Label(
            status,
            text="等待首次同步",
            bg=COLORS["navy_2"],
            fg="#5BDBCA",
            font=(FONT_UI, 9),
        )
        self.sync_status_label.pack(anchor="w", padx=15, pady=(0, 15))

    def _build_center(self):
        self.center.grid_rowconfigure(0, weight=1)
        self.center.grid_columnconfigure(0, weight=1)
        self.scroll = ScrollFrame(self.center, COLORS["canvas"])
        self.scroll.grid(row=0, column=0, sticky="nsew")
        body = self.scroll.body

        header = tk.Frame(body, bg=COLORS["canvas"])
        header.pack(fill="x", padx=34, pady=(30, 0))
        title_box = tk.Frame(header, bg=COLORS["canvas"])
        title_box.pack(side="left")
        tk.Label(
            title_box,
            text="LOCAL KNOWLEDGE VIEWER",
            bg=COLORS["canvas"],
            fg=COLORS["teal_dark"],
            font=(FONT_UI, 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="知识库总览",
            bg=COLORS["canvas"],
            fg=COLORS["ink"],
            font=(FONT_UI, 25, "bold"),
        ).pack(anchor="w", pady=(4, 0))
        self.top_sync_label = tk.Label(
            header,
            text="● 正在读取",
            bg=COLORS["paper"],
            fg=COLORS["muted"],
            padx=13,
            pady=7,
            font=(FONT_UI, 9),
        )
        self.top_sync_label.pack(side="right", anchor="n")

        search_wrap = tk.Frame(
            body,
            bg=COLORS["white"],
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        )
        search_wrap.pack(fill="x", padx=34, pady=(24, 0))
        tk.Label(
            search_wrap,
            text="⌕",
            bg=COLORS["white"],
            fg=COLORS["muted"],
            font=(FONT_UI, 20),
        ).pack(side="left", padx=(14, 6))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_wrap,
            textvariable=self.search_var,
            relief="flat",
            bd=0,
            bg=COLORS["white"],
            fg=COLORS["ink"],
            insertbackground=COLORS["teal"],
            font=(FONT_UI, 12),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12), pady=14)
        self.search_var.trace_add("write", self._on_search_change)

        chips = tk.Frame(body, bg=COLORS["canvas"])
        chips.pack(fill="x", padx=34, pady=(12, 0))
        for key, label in [
            ("all", "全部"),
            ("项目", "项目"),
            ("知识", "知识卡"),
            ("内容", "内容"),
            ("提示词", "提示词"),
            ("Skill", "Skill"),
        ]:
            button = tk.Button(
                chips,
                text=label,
                relief="flat",
                bd=0,
                padx=13,
                pady=6,
                cursor="hand2",
                bg=COLORS["teal"] if key == "all" else COLORS["paper"],
                fg="#FFFFFF" if key == "all" else COLORS["muted"],
                activebackground=COLORS["teal"],
                activeforeground="#FFFFFF",
                font=(FONT_UI, 9),
                command=lambda value=key: self._set_type_filter(value),
            )
            button.pack(side="left", padx=(0, 7))
            self.type_buttons[key] = button

        focus_head = tk.Frame(body, bg=COLORS["canvas"])
        focus_head.pack(fill="x", padx=34, pady=(26, 10))
        focus_titles = tk.Frame(focus_head, bg=COLORS["canvas"])
        focus_titles.pack(side="left")
        tk.Label(
            focus_titles,
            text="CURRENT FOCUS",
            bg=COLORS["canvas"],
            fg=COLORS["teal_dark"],
            font=(FONT_UI, 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            focus_titles,
            text="当前进行中",
            bg=COLORS["canvas"],
            fg=COLORS["ink"],
            font=(FONT_UI, 16, "bold"),
        ).pack(anchor="w", pady=(3, 0))
        tk.Button(
            focus_head,
            text="立即同步 ↻",
            relief="flat",
            bd=0,
            bg=COLORS["canvas"],
            fg=COLORS["teal_dark"],
            activebackground=COLORS["canvas"],
            cursor="hand2",
            font=(FONT_UI, 9),
            command=lambda: self._request_scan(force=True),
        ).pack(side="right", anchor="s")

        self.focus_card = tk.Frame(
            body,
            bg=COLORS["paper"],
            height=148,
            highlightbackground=COLORS["line"],
            highlightthickness=1,
        )
        self.focus_card.pack(fill="x", padx=34)
        self.focus_card.pack_propagate(False)
        self._render_focus_placeholder()

        cards_head = tk.Frame(body, bg=COLORS["canvas"])
        cards_head.pack(fill="x", padx=34, pady=(27, 10))
        card_titles = tk.Frame(cards_head, bg=COLORS["canvas"])
        card_titles.pack(side="left")
        tk.Label(
            card_titles,
            text="KNOWLEDGE CARDS",
            bg=COLORS["canvas"],
            fg=COLORS["teal_dark"],
            font=(FONT_UI, 8, "bold"),
        ).pack(anchor="w")
        self.cards_title_label = tk.Label(
            card_titles,
            text="最近更新",
            bg=COLORS["canvas"],
            fg=COLORS["ink"],
            font=(FONT_UI, 16, "bold"),
        )
        self.cards_title_label.pack(anchor="w", pady=(3, 0))
        self.result_count_label = tk.Label(
            cards_head,
            text="读取中",
            bg=COLORS["canvas"],
            fg=COLORS["muted"],
            font=(FONT_UI, 9),
        )
        self.result_count_label.pack(side="right", anchor="s")

        self.card_grid = tk.Frame(body, bg=COLORS["canvas"])
        self.card_grid.pack(fill="both", expand=True, padx=34, pady=(0, 36))
        self.card_grid.grid_columnconfigure(0, weight=1, uniform="cards")
        self.card_grid.grid_columnconfigure(1, weight=1, uniform="cards")

    def _build_context(self):
        header = tk.Frame(self.context, bg=COLORS["paper"])
        header.pack(fill="x", padx=25, pady=(30, 18))
        title_wrap = tk.Frame(header, bg=COLORS["paper"])
        title_wrap.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_wrap,
            text="LIVE CONTEXT",
            bg=COLORS["paper"],
            fg=COLORS["teal_dark"],
            font=(FONT_UI, 8, "bold"),
        ).pack(anchor="w")
        self.context_title = tk.Label(
            title_wrap,
            text="当前上下文",
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            font=(FONT_UI, 17, "bold"),
            wraplength=270,
            justify="left",
        )
        self.context_title.pack(anchor="w", pady=(4, 0))
        self.close_context_button = tk.Button(
            header,
            text="×",
            relief="flat",
            bd=0,
            padx=9,
            pady=4,
            bg=COLORS["white"],
            fg=COLORS["muted"],
            activebackground=COLORS["teal_soft"],
            cursor="hand2",
            font=(FONT_UI, 15),
            command=self._clear_selection,
        )

        separator = tk.Frame(self.context, bg=COLORS["line"], height=1)
        separator.pack(fill="x", padx=25)

        self.context_scroll = ScrollFrame(self.context, COLORS["paper"])
        self.context_scroll.pack(fill="both", expand=True, padx=(25, 16), pady=(17, 20))
        body = self.context_scroll.body

        tk.Label(
            body,
            text="下一步行动",
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            font=(FONT_UI, 12, "bold"),
        ).pack(anchor="w", pady=(0, 10))
        self.actions_frame = tk.Frame(body, bg=COLORS["paper"])
        self.actions_frame.pack(fill="x")

        line1 = tk.Frame(body, bg=COLORS["line"], height=1)
        line1.pack(fill="x", pady=20)
        recent_head = tk.Frame(body, bg=COLORS["paper"])
        recent_head.pack(fill="x")
        tk.Label(
            recent_head,
            text="最近更新",
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            font=(FONT_UI, 12, "bold"),
        ).pack(side="left")
        self.context_sync_label = tk.Label(
            recent_head,
            text="正在读取",
            bg=COLORS["paper"],
            fg="#9AA3A1",
            font=(FONT_UI, 8),
        )
        self.context_sync_label.pack(side="right")
        self.timeline_frame = tk.Frame(body, bg=COLORS["paper"])
        self.timeline_frame.pack(fill="x", pady=(13, 0))

        line2 = tk.Frame(body, bg=COLORS["line"], height=1)
        line2.pack(fill="x", pady=20)
        tk.Label(
            body,
            text="关联标签",
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            font=(FONT_UI, 12, "bold"),
        ).pack(anchor="w")
        self.tags_frame = tk.Frame(body, bg=COLORS["paper"])
        self.tags_frame.pack(fill="x", pady=(12, 0))

        source = tk.Frame(body, bg=COLORS["navy"])
        source.pack(fill="x", pady=(22, 0))
        tk.Label(
            source,
            text="唯一数据源",
            bg=COLORS["navy"],
            fg="#61D9C8",
            font=(FONT_UI, 8, "bold"),
        ).pack(anchor="w", padx=16, pady=(15, 4))
        tk.Label(
            source,
            text="本地 Markdown 文件",
            bg=COLORS["navy"],
            fg="#FFFFFF",
            font=(FONT_UI, 12, "bold"),
        ).pack(anchor="w", padx=16)
        tk.Label(
            source,
            text="WorkBuddy 或 Codex 保存后，界面自动检测并更新。",
            bg=COLORS["navy"],
            fg="#91A7B7",
            wraplength=275,
            justify="left",
            font=(FONT_UI, 8),
        ).pack(anchor="w", padx=16, pady=(7, 15))

        self._render_context_placeholder()

    def _render_focus_placeholder(self):
        for child in self.focus_card.winfo_children():
            child.destroy()
        tk.Label(
            self.focus_card,
            text="M↓",
            bg=COLORS["navy_2"],
            fg="#FFFFFF",
            width=4,
            height=2,
            font=(FONT_MONO, 17, "bold"),
        ).pack(side="left", padx=(24, 18))
        text = tk.Frame(self.focus_card, bg=COLORS["paper"])
        text.pack(side="left", fill="x", expand=True)
        tk.Label(
            text,
            text="正在同步本地知识库",
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            font=(FONT_UI, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            text,
            text="无需选择文件夹，桌面版会直接读取当前 Vault。",
            bg=COLORS["paper"],
            fg=COLORS["muted"],
            font=(FONT_UI, 10),
        ).pack(anchor="w", pady=(6, 0))

    def _render_context_placeholder(self):
        self._clear_frame(self.actions_frame)
        self._make_action("正在读取知识库", "首次同步完成后显示真实行动项")
        self._clear_frame(self.timeline_frame)
        self._make_timeline("等待同步", "读取本地 Markdown")
        self._clear_frame(self.tags_frame)

    def _request_scan(self, initial: bool = False, force: bool = False):
        if self.scan_running or self.closed:
            return
        self.next_scan_job = None
        self.scan_running = True
        self.top_sync_label.configure(text="● 正在同步", fg=COLORS["blue"])
        self.sync_status_label.configure(text="正在检查文件变化")

        def worker():
            try:
                files, fingerprint = snapshot_vault()
                changed = initial or force or fingerprint != self.fingerprint
                records = load_records(files) if changed else None
                self.scan_queue.put(("success", records, fingerprint, initial, force))
            except Exception as exc:  # pragma: no cover - visible app fallback
                self.scan_queue.put(("error", exc, initial))

        threading.Thread(target=worker, daemon=True).start()

    def _consume_scan_result(self):
        if self.closed:
            return
        try:
            while True:
                payload = self.scan_queue.get_nowait()
                self.scan_running = False
                if payload[0] == "success":
                    _, records, fingerprint, initial, force = payload
                    changed = initial or force or fingerprint != self.fingerprint
                    if changed and records is not None:
                        self.records = records
                        self.fingerprint = fingerprint
                        self._render_all()
                    now = datetime.now().strftime("%H:%M:%S")
                    self.top_sync_label.configure(text="● 自动同步中", fg=COLORS["teal_dark"])
                    self.sync_status_label.configure(text=f"已同步 · {now}")
                    self.context_sync_label.configure(text=f"已同步 {now}")
                    self.status_dot.configure(fg="#31D4B8")
                else:
                    self.top_sync_label.configure(text="● 同步失败", fg=COLORS["coral"])
                    self.sync_status_label.configure(text="读取失败，请检查目录权限")
                self._schedule_next_scan()
        except queue.Empty:
            pass
        self.root.after(100, self._consume_scan_result)

    def _schedule_next_scan(self):
        if self.closed or self.next_scan_job is not None:
            return
        self.next_scan_job = self.root.after(POLL_MS, self._request_scan)

    def _render_all(self):
        self.file_count_label.configure(text=f"{len(self.records)} 张独立知识卡")
        self._render_focus()
        self._render_cards()
        self._render_global_context()

    def _display_records(self) -> list[MarkdownRecord]:
        query = self.search_text.strip().casefold()
        query_tokens = [
            token
            for token in re.sub(r"[^\w\u4e00-\u9fff+.#-]+", " ", query).split()
            if token
        ]
        output: list[tuple[MarkdownRecord, int]] = []
        for record in self.records:
            if record.category.key == "system":
                continue
            if self.nav_filter != "all" and record.category.key != self.nav_filter:
                continue
            if self.type_filter != "all" and record.category.label != self.type_filter:
                continue
            score = 0
            if query_tokens:
                title = record.title.casefold()
                aliases = " ".join(record.aliases).casefold()
                tags = " ".join(record.tags).casefold()
                path = record.path.casefold()
                excerpt = record.excerpt.casefold()
                body = record.text.casefold()
                haystack = " ".join([title, aliases, tags, path, excerpt, body])
                if not all(token in haystack for token in query_tokens):
                    continue
                for token in query_tokens:
                    score += 100 if token in title else 0
                    score += 70 if token in aliases else 0
                    score += 45 if token in tags else 0
                    score += 25 if token in path else 0
                    score += 15 if token in excerpt else 0
                    score += 5 if token in body else 0
                score += 80 if query in title else 0
                score += 50 if query in aliases else 0
            output.append((record, score))
        if query_tokens:
            output.sort(key=lambda item: (item[1], item[0].mtime_ns), reverse=True)
        return [record for record, _score in output]

    def _render_focus(self):
        projects = [item for item in self.records if item.category.key == "projects"]
        active = next(
            (item for item in self.records if item.path == "00-System/Active-Context.md"),
            None,
        )
        focus_path = ""
        if active:
            match = re.search(r"^focus_path:\s*(.+)$", active.text, re.MULTILINE)
            focus_path = match.group(1).strip() if match else ""
        record = next((item for item in self.records if item.path == focus_path), None)
        record = record or (projects[0] if projects else active or (self.records[0] if self.records else None))
        if not record:
            self._render_focus_placeholder()
            return
        self._clear_frame(self.focus_card)
        symbol = tk.Label(
            self.focus_card,
            text=record.category.symbol,
            bg=COLORS["navy_2"],
            fg="#FFFFFF",
            width=4,
            height=2,
            font=(FONT_MONO, 18, "bold"),
        )
        symbol.pack(side="left", padx=(24, 18))
        text = tk.Frame(self.focus_card, bg=COLORS["paper"])
        text.pack(side="left", fill="both", expand=True, pady=22)
        tk.Label(
            text,
            text=record.title,
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            font=(FONT_UI, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            text,
            text=record.excerpt[:145],
            bg=COLORS["paper"],
            fg=COLORS["muted"],
            wraplength=560,
            justify="left",
            font=(FONT_UI, 9),
        ).pack(anchor="w", pady=(6, 8))
        meta = tk.Frame(text, bg=COLORS["paper"])
        meta.pack(anchor="w")
        for tag in record.tags[:3]:
            tk.Label(
                meta,
                text=f"#{tag}",
                bg=COLORS["teal_soft"],
                fg=COLORS["teal_dark"],
                padx=7,
                pady=3,
                font=(FONT_UI, 8),
            ).pack(side="left", padx=(0, 5))
        tk.Button(
            self.focus_card,
            text="查看内容 →",
            relief="flat",
            bd=0,
            bg=COLORS["teal"],
            fg="#FFFFFF",
            activebackground=COLORS["teal_dark"],
            activeforeground="#FFFFFF",
            cursor="hand2",
            padx=15,
            pady=9,
            font=(FONT_UI, 9),
            command=lambda: self._open_record(record),
        ).pack(side="right", padx=24)

    def _render_cards(self):
        records = self._display_records()
        self.cards_title_label.configure(
            text="最近更新"
            if self.nav_filter == self.type_filter == "all" and not self.search_text
            else "筛选结果"
        )
        self.result_count_label.configure(text=f"{len(records)} 条内容")
        self._clear_frame(self.card_grid)
        self.card_grid.grid_columnconfigure(0, weight=1, uniform="cards")
        self.card_grid.grid_columnconfigure(1, weight=1, uniform="cards")

        if not records:
            empty = tk.Frame(
                self.card_grid,
                bg=COLORS["paper"],
                highlightbackground=COLORS["line"],
                highlightthickness=1,
            )
            empty.grid(row=0, column=0, columnspan=2, sticky="ew", pady=2)
            tk.Label(
                empty,
                text="没有找到匹配内容",
                bg=COLORS["paper"],
                fg=COLORS["ink"],
                font=(FONT_UI, 13, "bold"),
            ).pack(pady=(38, 5))
            tk.Label(
                empty,
                text="换一个关键词或清除筛选条件。",
                bg=COLORS["paper"],
                fg=COLORS["muted"],
                font=(FONT_UI, 9),
            ).pack(pady=(0, 38))
            return

        for index, record in enumerate(records[:30]):
            row, column = divmod(index, 2)
            card = tk.Frame(
                self.card_grid,
                bg=COLORS["paper"],
                height=178,
                highlightbackground=(
                    COLORS["teal"] if self.selected and self.selected.path == record.path else COLORS["line"]
                ),
                highlightthickness=1,
                cursor="hand2",
            )
            card.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0, 7) if column == 0 else (7, 0),
                pady=7,
            )
            card.grid_propagate(False)
            top = tk.Frame(card, bg=COLORS["paper"])
            top.pack(fill="x", padx=17, pady=(16, 8))
            icon = tk.Label(
                top,
                text=record.category.symbol,
                bg=record.category.soft,
                fg=record.category.accent,
                width=4,
                height=2,
                font=(FONT_MONO, 12, "bold"),
            )
            icon.pack(side="left")
            tk.Label(
                top,
                text=record.category.label,
                bg=COLORS["paper"],
                fg=COLORS["muted"],
                font=(FONT_UI, 8),
            ).pack(side="right", anchor="n")
            title = tk.Label(
                card,
                text=record.title,
                bg=COLORS["paper"],
                fg=COLORS["ink"],
                anchor="w",
                font=(FONT_UI, 12, "bold"),
            )
            title.pack(fill="x", padx=17)
            excerpt = tk.Label(
                card,
                text=record.excerpt[:105],
                bg=COLORS["paper"],
                fg=COLORS["muted"],
                wraplength=350,
                justify="left",
                anchor="nw",
                font=(FONT_UI, 8),
            )
            excerpt.pack(fill="x", padx=17, pady=(6, 8))
            footer = tk.Frame(card, bg=COLORS["paper"])
            footer.pack(side="bottom", fill="x", padx=17, pady=(0, 13))
            tag_text = "  ".join(f"#{tag}" for tag in record.tags[:2])
            tk.Label(
                footer,
                text=tag_text,
                bg=COLORS["paper"],
                fg="#3C6F88",
                font=(FONT_UI, 7),
            ).pack(side="left")
            tk.Label(
                footer,
                text=record.updated,
                bg=COLORS["paper"],
                fg="#98A19F",
                font=(FONT_UI, 7),
            ).pack(side="right")
            self._bind_tree(card, lambda _event, item=record: self._select_record(item))

    def _render_global_context(self):
        if self.selected:
            self._render_selected_context(self.selected)
            return
        self.context_title.configure(text="当前上下文")
        self.close_context_button.pack_forget()
        active = next(
            (item for item in self.records if item.path == "00-System/Active-Context.md"),
            None,
        )
        focus_path = ""
        if active:
            match = re.search(r"^focus_path:\s*(.+)$", active.text, re.MULTILINE)
            focus_path = match.group(1).strip() if match else ""
        focus = next((item for item in self.records if item.path == focus_path), None)
        action_text = section_text(focus.text, ["下一步行动", "下一步"]) if focus else (section_text(active.text, ["下一步"]) if active else "保持知识库持续更新")
        actions = self._action_lines(action_text)[:4] or ["保持知识库持续更新"]
        self._clear_frame(self.actions_frame)
        for action in actions:
            self._make_action(action, "来自当前上下文")

        recent = [item for item in self.records if item.category.key != "system"][:5]
        self._clear_frame(self.timeline_frame)
        for record in recent:
            self._make_timeline(record.title, f"{record.updated} · {record.category.label}", record)

        counts = Counter(tag for record in self.records for tag in record.tags)
        tags = [tag for tag, _count in counts.most_common(12)]
        self._render_tags(tags)

    def _render_selected_context(self, record: MarkdownRecord):
        self.context_title.configure(text=record.title)
        self.close_context_button.pack(side="right", anchor="n")
        actions = self._action_lines(record.next_actions or record.excerpt)[:3]
        self._clear_frame(self.actions_frame)
        for action in actions or [record.excerpt[:70]]:
            self._make_action(action, "点击卡片可阅读全文")
        self._clear_frame(self.timeline_frame)
        self._make_timeline("最后更新", record.updated)
        self._make_timeline(record.category.label, record.path)
        self._render_tags(record.tags)

    def _render_tags(self, tags: list[str]):
        self._clear_frame(self.tags_frame)
        for index, tag in enumerate(tags):
            button = tk.Button(
                self.tags_frame,
                text=f"#{tag}",
                relief="flat",
                bd=0,
                padx=8,
                pady=4,
                bg="#EFF7FB",
                fg="#2F6F9A",
                activebackground=COLORS["blue_soft"],
                cursor="hand2",
                font=(FONT_UI, 8),
                command=lambda value=tag: self._search_tag(value),
            )
            button.grid(row=index // 3, column=index % 3, sticky="w", padx=(0, 5), pady=4)

    def _make_action(self, title: str, subtitle: str):
        item = tk.Frame(
            self.actions_frame,
            bg=COLORS["white"],
            highlightbackground="#E6E4DE",
            highlightthickness=1,
        )
        item.pack(fill="x", pady=4)
        tk.Label(
            item,
            text="✓",
            bg=COLORS["teal"],
            fg="#FFFFFF",
            width=2,
            height=1,
            font=(FONT_UI, 9, "bold"),
        ).pack(side="left", padx=11, pady=12)
        text = tk.Frame(item, bg=COLORS["white"])
        text.pack(side="left", fill="x", expand=True, pady=9)
        tk.Label(
            text,
            text=title[:70],
            bg=COLORS["white"],
            fg=COLORS["ink"],
            wraplength=240,
            justify="left",
            font=(FONT_UI, 9, "bold"),
        ).pack(anchor="w")
        tk.Label(
            text,
            text=subtitle,
            bg=COLORS["white"],
            fg=COLORS["muted"],
            font=(FONT_UI, 7),
        ).pack(anchor="w", pady=(3, 0))

    def _make_timeline(
        self, title: str, subtitle: str, record: MarkdownRecord | None = None
    ):
        item = tk.Frame(self.timeline_frame, bg=COLORS["paper"], cursor="hand2" if record else "")
        item.pack(fill="x", pady=6)
        tk.Label(
            item,
            text="●",
            bg=COLORS["paper"],
            fg=record.category.accent if record else COLORS["teal"],
            font=(FONT_UI, 9),
        ).pack(side="left", anchor="n", padx=(0, 8))
        text = tk.Frame(item, bg=COLORS["paper"])
        text.pack(side="left", fill="x", expand=True)
        tk.Label(
            text,
            text=title[:42],
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            wraplength=255,
            justify="left",
            font=(FONT_UI, 9, "bold"),
        ).pack(anchor="w")
        tk.Label(
            text,
            text=subtitle[:70],
            bg=COLORS["paper"],
            fg=COLORS["muted"],
            wraplength=255,
            justify="left",
            font=(FONT_UI, 7),
        ).pack(anchor="w", pady=(2, 0))
        if record:
            self._bind_tree(item, lambda _event, value=record: self._select_record(value))

    def _set_nav_filter(self, value: str):
        self.nav_filter = value
        self.selected = None
        for key, button in self.nav_buttons.items():
            active = key == value
            button.configure(
                bg=COLORS["teal_dark"] if active else COLORS["navy"],
                fg="#FFFFFF" if active else "#B7C8D5",
            )
        self._render_cards()
        self._render_global_context()

    def _set_type_filter(self, value: str):
        self.type_filter = value
        for key, button in self.type_buttons.items():
            active = key == value
            button.configure(
                bg=COLORS["teal"] if active else COLORS["paper"],
                fg="#FFFFFF" if active else COLORS["muted"],
            )
        self._render_cards()

    def _on_search_change(self, *_args):
        if self.search_after:
            self.root.after_cancel(self.search_after)
        self.search_after = self.root.after(180, self._apply_search)

    def _apply_search(self):
        self.search_text = self.search_var.get()
        self._render_cards()

    def _search_tag(self, tag: str):
        self.search_var.set(tag)
        self.search_entry.focus_set()

    def _select_record(self, record: MarkdownRecord):
        self.selected = record
        self._render_cards()
        self._render_selected_context(record)

    def _clear_selection(self):
        self.selected = None
        self._render_cards()
        self._render_global_context()

    def _open_record(self, record: MarkdownRecord):
        self._select_record(record)
        reader = tk.Toplevel(self.root)
        reader.title(record.title)
        reader.configure(bg=COLORS["paper"])
        reader.geometry("900x720")
        reader.minsize(720, 520)
        header = tk.Frame(reader, bg=COLORS["paper"])
        header.pack(fill="x", padx=28, pady=(24, 15))
        tk.Label(
            header,
            text=record.category.label.upper(),
            bg=COLORS["paper"],
            fg=COLORS["teal_dark"],
            font=(FONT_UI, 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text=record.title,
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            font=(FONT_UI, 19, "bold"),
        ).pack(anchor="w", pady=(4, 3))
        tk.Label(
            header,
            text=record.path,
            bg=COLORS["paper"],
            fg=COLORS["muted"],
            font=(FONT_MONO, 8),
        ).pack(anchor="w")
        text_wrap = tk.Frame(reader, bg=COLORS["paper"])
        text_wrap.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        scrollbar = ttk.Scrollbar(text_wrap)
        scrollbar.pack(side="right", fill="y")
        text = tk.Text(
            text_wrap,
            wrap="word",
            relief="flat",
            bd=0,
            bg=COLORS["paper"],
            fg=COLORS["ink"],
            insertbackground=COLORS["teal"],
            padx=4,
            pady=4,
            font=(FONT_UI, 11),
            spacing1=4,
            spacing3=6,
            yscrollcommand=scrollbar.set,
        )
        text.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=text.yview)
        text.insert("1.0", record.text)
        text.configure(state="disabled")

    @staticmethod
    def _action_lines(text: str) -> list[str]:
        lines = re.split(r"[。\n；;]+", text)
        output = []
        for line in lines:
            cleaned = re.sub(r"^\s*(?:[-*+]|\d+[.)、])\s*", "", line).strip()
            if len(cleaned) >= 3:
                output.append(cleaned)
        return output[:8]

    @staticmethod
    def _clear_frame(frame: tk.Misc):
        for child in frame.winfo_children():
            child.destroy()

    @staticmethod
    def _bind_tree(widget: tk.Misc, callback):
        widget.bind("<Button-1>", callback)
        for child in widget.winfo_children():
            KnowledgePreviewApp._bind_tree(child, callback)

    def _close(self):
        self.closed = True
        if self.next_scan_job is not None:
            self.root.after_cancel(self.next_scan_job)
        self.root.destroy()


def main():
    global VAULT_ROOT
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    if not (VAULT_ROOT / "AGENTS.md").exists() or not (VAULT_ROOT / "00-System").is_dir():
        root.withdraw()
        selected = filedialog.askdirectory(
            parent=root,
            title="选择 Boujoy 知识库文件夹",
            mustexist=True,
        )
        if not selected:
            root.destroy()
            return
        VAULT_ROOT = Path(selected).resolve()
        if not (VAULT_ROOT / "AGENTS.md").exists() or not (VAULT_ROOT / "00-System").is_dir():
            root.destroy()
            return
        root.deiconify()
    KnowledgePreviewApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
