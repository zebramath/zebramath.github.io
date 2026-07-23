#!/usr/bin/env python3
"""Download Douban poster thumbnails locally and rewrite their data paths."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def subject_id(item: dict) -> str:
    match = re.search(r"/subject/(\d+)/", item.get("douban_url", ""))
    if not match:
        raise ValueError(f"Missing Douban subject ID: {item.get('douban_url')}")
    return match.group(1)


def download(item: dict, cover_dir: Path, retries: int) -> tuple[str, str]:
    sid = subject_id(item)
    source = item.get("cover", "")
    if source.startswith("/"):
        existing = Path("static") / source.lstrip("/")
        if existing.exists() and existing.stat().st_size > 512:
            return sid, source
        raise FileNotFoundError(existing)

    suffix = Path(source.split("?", 1)[0]).suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        suffix = ".jpg"
    destination = cover_dir / f"{sid}{suffix}"
    public_path = f"/images/douban/{destination.name}"
    if destination.exists() and destination.stat().st_size > 512:
        return sid, public_path

    request = urllib.request.Request(
        source,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; zebramath-site cover cache/1.0)",
            "Referer": "https://movie.douban.com/",
        },
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                content_type = response.headers.get("Content-Type", "")
                content = response.read()
            if not content_type.startswith("image/") or len(content) <= 512:
                raise RuntimeError(f"Invalid image response for {source}")
            temporary = destination.with_suffix(destination.suffix + ".part")
            temporary.write_bytes(content)
            temporary.replace(destination)
            return sid, public_path
        except Exception:
            if attempt + 1 == retries:
                raise
            time.sleep(attempt + 1)
    raise RuntimeError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="data/media_import.json")
    parser.add_argument("--cover-dir", default="static/images/douban")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    data_path = Path(args.data)
    payload = json.loads(data_path.read_text(encoding="utf-8"))
    media = payload.get("media", [])
    cover_dir = Path(args.cover_dir)
    cover_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    failures: list[str] = []

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(download, item, cover_dir, args.retries): item for item in media}
        for index, future in enumerate(as_completed(futures), 1):
            item = futures[future]
            try:
                sid, local_path = future.result()
                paths[sid] = local_path
            except Exception as exc:
                failures.append(f"{item.get('douban_url')}: {exc}")
            if index % 50 == 0 or index == len(futures):
                print(f"Processed {index}/{len(futures)} covers")

    if failures:
        raise RuntimeError("Cover download failures:\n" + "\n".join(failures))
    for item in media:
        item["cover"] = paths[subject_id(item)]
    data_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Cached {len(paths)} posters in {cover_dir}.")


if __name__ == "__main__":
    main()
