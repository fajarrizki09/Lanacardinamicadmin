from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_PY = ROOT / "version.py"
VERSION_ISS = ROOT / "version.iss"
ISS_FILE = ROOT / "RumahSehatInstaller.iss"


VERSION_RE = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


def read_version() -> str:
    if VERSION_PY.exists():
        match = re.search(r'APP_VERSION\s*=\s*"([^"]+)"', VERSION_PY.read_text(encoding="utf-8"))
        if match:
            return match.group(1)

    if VERSION_ISS.exists():
        match = re.search(r'MyAppVersion\s+"([^"]+)"', VERSION_ISS.read_text(encoding="utf-8"))
        if match:
            return match.group(1)

    text = ISS_FILE.read_text(encoding="utf-8")
    match = re.search(r"^AppVersion=(.+)$", text, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()

    return "1.0.0"


def bump_patch(version: str) -> str:
    match = VERSION_RE.fullmatch(version.strip())
    if not match:
        raise ValueError(f"Versi tidak valid: {version!r}")

    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3) or 0) + 1
    return f"{major}.{minor}.{patch}"


def write_version(version: str) -> None:
    VERSION_PY.write_text(f'APP_VERSION = "{version}"\n', encoding="utf-8")
    VERSION_ISS.write_text(f'#define MyAppVersion "{version}"\n', encoding="utf-8")


def main() -> None:
    current = read_version()
    updated = bump_patch(current)
    write_version(updated)
    print(updated)


if __name__ == "__main__":
    main()
