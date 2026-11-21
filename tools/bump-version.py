#!/usr/bin/env python3
"""Auto-increment patch version across all version files."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

VERSION_FILES = [
    (ROOT / "version.py", r'APP_VERSION = "(\d+)\.(\d+)\.(\d+)"', 'APP_VERSION = "{major}.{minor}.{patch}"'),
    (ROOT / "version.iss", r'#define MyAppVersion "(\d+)\.(\d+)\.(\d+)"', '#define MyAppVersion "{major}.{minor}.{patch}"'),
    (ROOT / "src-tauri" / "Cargo.toml", r'version = "(\d+)\.(\d+)\.(\d+)"', 'version = "{major}.{minor}.{patch}"'),
    (ROOT / "src-tauri" / "tauri.conf.json", r'"version": "(\d+)\.(\d+)\.(\d+)"', '"version": "{major}.{minor}.{patch}"'),
    (ROOT / "src-tauri" / "src" / "main.rs", r'app_version: "(\d+)\.(\d+)\.(\d+)"', 'app_version: "{major}.{minor}.{patch}"'),
]


def read_version(file_path, pattern):
    content = file_path.read_text(encoding="utf-8")
    match = re.search(pattern, content)
    if not match:
        raise ValueError(f"Version not found in {file_path}")
    return tuple(map(int, match.groups()))


def write_version(file_path, pattern, template, major, minor, patch):
    content = file_path.read_text(encoding="utf-8")
    new_content = re.sub(pattern, template.format(major=major, minor=minor, patch=patch), content)
    file_path.write_text(new_content, encoding="utf-8")


def bump_patch():
    # Read current version from version.py (source of truth)
    major, minor, patch = read_version(VERSION_FILES[0][0], VERSION_FILES[0][1])
    patch += 1
    new_version = f"{major}.{minor}.{patch}"

    print(f"Bumping version to {new_version}")

    for file_path, pattern, template in VERSION_FILES:
        write_version(file_path, pattern, template, major, minor, patch)
        print(f"  Updated {file_path.relative_to(ROOT)}")

    print(f"\nDone! New version: {new_version}")
    return new_version


if __name__ == "__main__":
    bump_patch()