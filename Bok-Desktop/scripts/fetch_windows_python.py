from __future__ import annotations

import argparse
import hashlib
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path


PYTHON_VERSION = "3.13.15"
PYTHON_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
PYTHON_SHA256 = "d1f04d990aee1253d8569e8e5104e30fa9f5fa830899f14843448872d936a2cf"


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch the verified official CPython Windows embeddable runtime.")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="bok-python-runtime-") as temporary:
        archive_path = Path(temporary) / "python-embed.zip"
        with urllib.request.urlopen(PYTHON_URL, timeout=120) as response:
            archive_path.write_bytes(response.read())
        digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
        if digest != PYTHON_SHA256:
            raise RuntimeError(f"Python runtime checksum mismatch: {digest}")
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(output)
    pth_files = list(output.glob("python*._pth"))
    if len(pth_files) != 1 or not (output / "pythonw.exe").is_file():
        raise RuntimeError("The Windows embeddable runtime is incomplete")
    lines = [line for line in pth_files[0].read_text(encoding="utf-8").splitlines() if line.strip() != "#import site"]
    pth_files[0].write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Verified CPython {PYTHON_VERSION} Windows runtime: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
