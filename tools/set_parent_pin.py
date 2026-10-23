#!/usr/bin/env python3
"""Set or reset the parent PIN without placing it in command arguments or files."""
from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.auth.security import hash_pin, valid_pin
from app.database import Database


def main() -> int:
    os.umask(0o077)
    data_dir = Path(os.environ.get("KLT_DATA_DIR", ROOT / "var")).expanduser().resolve()
    data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        data_dir.chmod(0o700)
    except OSError:
        pass
    first = getpass.getpass("New parent PIN (6-12 digits): ")
    second = getpass.getpass("Repeat parent PIN: ")
    if not valid_pin(first):
        print("PIN must contain 6 to 12 digits.", file=sys.stderr)
        return 2
    if first != second:
        print("PIN entries did not match.", file=sys.stderr)
        return 2
    database = Database(data_dir / "kid-learning-tv.sqlite3")
    database.set_pin_hash(hash_pin(first))
    try:
        database.path.chmod(0o600)
    except OSError:
        pass
    print("Parent PIN updated. The PIN is stored as a salted hash.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
