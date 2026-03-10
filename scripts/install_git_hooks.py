#!/usr/bin/env python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    hooks_path = root / ".githooks"
    if not hooks_path.exists():
        print(f"hooks path not found: {hooks_path}")
        return 1

    try:
        subprocess.run(
            ["git", "config", "core.hooksPath", str(hooks_path)],
            cwd=root,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(f"failed to configure git hooks: {exc}")
        return 1

    print(f"configured git hooks path: {hooks_path}")
    print("pre-commit will now run: python scripts/i18n_check.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
