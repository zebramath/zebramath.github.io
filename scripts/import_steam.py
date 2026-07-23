#!/usr/bin/env python3
"""Import a public Steam library into Hugo data without exposing API credentials."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path


API_URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"


def configured_appids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    source = path.read_text(encoding="utf-8")
    appids = {int(value) for value in re.findall(r"^\s*steam_appid:\s*(\d+)\s*$", source, re.MULTILINE)}
    excluded = re.search(r"^\s*excluded_steam_appids:\s*\[([^]]*)\]", source, re.MULTILINE)
    if excluded:
        appids.update(int(value) for value in re.findall(r"\d+", excluded.group(1)))
    return appids


def fetch_library(api_key: str, steam_id: str) -> list[dict]:
    query = urllib.parse.urlencode(
        {
            "key": api_key,
            "steamid": steam_id,
            "include_appinfo": "true",
            "include_played_free_games": "true",
            "format": "json",
        }
    )
    request = urllib.request.Request(f"{API_URL}?{query}", headers={"User-Agent": "zebramath.github.io/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return payload.get("response", {}).get("games", [])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="data/steam.json")
    parser.add_argument("--curated", default="data/hobbies.yaml")
    args = parser.parse_args()

    api_key = os.environ.get("STEAM_API_KEY", "").strip()
    steam_id = os.environ.get("STEAM_ID", "").strip()
    if not api_key or not steam_id:
        print("STEAM_API_KEY and STEAM_ID are required.", file=sys.stderr)
        return 2

    existing = configured_appids(Path(args.curated))
    imported = []
    for game in fetch_library(api_key, steam_id):
        appid = int(game["appid"])
        if appid in existing or int(game.get("playtime_forever", 0)) <= 0:
            continue
        imported.append(
            {
                "title": {"zh": game["name"], "en": game["name"]},
                "steam_appid": appid,
                "playtime_hours": round(int(game.get("playtime_forever", 0)) / 60, 1),
            }
        )

    imported.sort(key=lambda item: item["playtime_hours"], reverse=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"games": imported}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(imported)} played games into {output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
