from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path


TEXT_SUFFIXES = {
    ".css", ".html", ".js", ".json", ".md", ".py", ".pyw", ".rs",
    ".toml", ".txt", ".xml", ".yaml", ".yml",
}
MAC_USER_PATH = re.compile(b"/" + b"Users/" + rb"[^/\x00\r\n\t ]+/")
WINDOWS_SEPARATOR = re.escape(bytes([92]))
WINDOWS_USER_PATH = re.compile(
    rb"[A-Za-z]:" + WINDOWS_SEPARATOR + b"Users" + WINDOWS_SEPARATOR
    + rb"[^\\\x00\r\n\t ]+" + WINDOWS_SEPARATOR,
    re.IGNORECASE,
)


GENERIC_PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "openai_style_key": re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"),
    # Build local-path detectors without embedding the exact path signature in
    # this source file; otherwise auditing the audit tool reports itself.
    "mac_user_path": MAC_USER_PATH,
    "windows_user_path": WINDOWS_USER_PATH,
}
SKIPPED_NAMES = {".DS_Store", "Thumbs.db"}
SKIPPED_DIRS = {
    ".bok", ".git", ".mypy_cache", ".pytest_cache", ".venv",
    "__pycache__", "_dist", "build-resources", "node_modules", "target",
}


def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"Symbolic link is forbidden in share output: {path}")
        relative_parts = path.relative_to(root).parts
        if any(part.casefold() in SKIPPED_DIRS for part in relative_parts):
            continue
        if path.is_file() and path.name not in SKIPPED_NAMES:
            yield path


def scan_bytes(path: Path, payload: bytes, deny: list[bytes]) -> list[str]:
    issues = []
    for name, pattern in GENERIC_PATTERNS.items():
        if pattern.search(payload):
            issues.append(f"{path}: {name}")
    lowered = payload.lower()
    for value in deny:
        if value and value.lower() in lowered:
            issues.append(f"{path}: local deny token")
    return issues


def scan_path(path: Path, deny: list[bytes]) -> list[str]:
    issues = []
    for item in iter_files(path):
        try:
            payload = item.read_bytes()
        except OSError as error:
            issues.append(f"{item}: unreadable ({error})")
            continue
        issues.extend(scan_bytes(item, payload, deny))
        if item.suffix.lower() == ".zip" and zipfile.is_zipfile(item):
            try:
                with zipfile.ZipFile(item) as archive:
                    for name in archive.namelist():
                        if name.endswith("/"):
                            continue
                        issues.extend(scan_bytes(Path(f"{item}!{name}"), archive.read(name), deny))
            except (OSError, zipfile.BadZipFile, RuntimeError) as error:
                issues.append(f"{item}: invalid zip ({error})")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed privacy scan for Bok share artifacts.")
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--deny", action="append", default=[])
    args = parser.parse_args()
    deny = [value.encode("utf-8") for value in args.deny if value]
    missing = [str(path) for path in args.paths if not path.exists()]
    if missing:
        print("Missing audit targets:\n" + "\n".join(missing), file=sys.stderr)
        return 2
    issues = []
    for path in args.paths:
        issues.extend(scan_path(path.resolve(), deny))
    if issues:
        print("Bok share privacy audit: FAIL", file=sys.stderr)
        print("\n".join(sorted(set(issues))), file=sys.stderr)
        return 1
    count = sum(1 for path in args.paths for _ in iter_files(path.resolve()))
    print(f"Bok share privacy audit: PASS ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
