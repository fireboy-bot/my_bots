#!/usr/bin/env python3
"""
Экспорт/импорт одного пользователя между SQLite-базами (bot local <-> VPS).

Примеры:
  python scripts/sync_user_db.py export 331113480 --db data/progress.db -o data/user_331113480.json
  python scripts/sync_user_db.py import 331113480 --db data/progress.db -i data/user_331113480.json
"""
import argparse
import json
import os
import sys
from typing import Any, Dict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from database.schema import init_database
from database.storage import PlayerStorage


def export_user(db_path: str, user_id: str, out_path: str) -> None:
    init_database(db_path)
    storage = PlayerStorage()
    user = storage.get_user(user_id)
    if not user:
        raise SystemExit(f"User {user_id} not found in {db_path}")

    payload: Dict[str, Any] = {
        "user_id": str(user_id),
        "source_db": os.path.abspath(db_path),
        "user": user,
    }
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"exported {user_id} -> {out_path}")


def import_user(db_path: str, user_id: str, in_path: str) -> None:
    with open(in_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    user = payload.get("user")
    if not user:
        raise SystemExit("Invalid export file: missing 'user'")

    init_database(db_path)
    storage = PlayerStorage()
    user["user_id"] = int(user_id)
    storage.save_user(str(user_id), user)
    print(f"imported {user_id} into {db_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync single user between progress.db files")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_exp = sub.add_parser("export")
    p_exp.add_argument("user_id")
    p_exp.add_argument("--db", default="data/progress.db")
    p_exp.add_argument("-o", "--out", required=True)

    p_imp = sub.add_parser("import")
    p_imp.add_argument("user_id")
    p_imp.add_argument("--db", default="data/progress.db")
    p_imp.add_argument("-i", "--in", dest="in_path", required=True)

    args = parser.parse_args()
    if args.cmd == "export":
        export_user(args.db, args.user_id, args.out)
    else:
        import_user(args.db, args.user_id, args.in_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
