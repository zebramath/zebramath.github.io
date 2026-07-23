#!/usr/bin/env python3
"""Convert a simple CSV watchlist into data/media_import.json."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file")
    parser.add_argument("--output", default="data/media_import.json")
    args = parser.parse_args()

    items = []
    with Path(args.csv_file).open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            title_zh = row.get("title_zh", "").strip()
            title_en = row.get("title_en", "").strip() or title_zh
            if not title_zh:
                continue
            item = {
                "title": {"zh": title_zh, "en": title_en},
                "type": row.get("type", "movie").strip() or "movie",
            }
            for key in ("year", "douban_url", "cover"):
                value = row.get(key, "").strip()
                if value:
                    item[key] = int(value) if key == "year" else value
            note_zh = row.get("note_zh", "").strip()
            note_en = row.get("note_en", "").strip()
            if note_zh or note_en:
                item["note"] = {"zh": note_zh or note_en, "en": note_en or note_zh}
            items.append(item)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"media": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(items)} titles into {output}.")


if __name__ == "__main__":
    main()
