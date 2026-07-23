#!/usr/bin/env python3
"""Import a public Douban watched list into data/media_import.json."""

from __future__ import annotations

import argparse
import html
import http.cookiejar
import json
import math
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


ITEM_SPLIT = re.compile(r'<div class="item comment-item"[^>]*>', re.I)
TAG = re.compile(r"<[^>]+>")


def clean(value: str) -> str:
    return " ".join(html.unescape(TAG.sub("", value)).split())


def first(pattern: str, source: str) -> str:
    match = re.search(pattern, source, re.I | re.S)
    return html.unescape(match.group(1)).strip() if match else ""


def titles(em_title: str, image_title: str) -> tuple[str, str]:
    parts = [part.strip() for part in re.split(r"\s+/\s+", clean(em_title)) if part.strip()]
    zh = parts[0] if parts else clean(image_title)
    en = next((part for part in parts[1:] if re.search(r"[A-Za-z]", part)), "")
    if not en and re.search(r"[A-Za-z]", image_title):
        en = clean(image_title)
    return zh, en or zh


def parse_page(source: str, media_type: str) -> list[dict]:
    chunks = ITEM_SPLIT.split(source)[1:]
    items: list[dict] = []
    for chunk in chunks:
        url = first(r'<a[^>]+href="([^"]+/subject/\d+/)"[^>]+class="nbg"', chunk)
        if not url:
            url = first(r'<a[^>]+href="([^"]+/subject/\d+/)"', chunk)
        if not url:
            continue
        image_title = first(r'<a[^>]+title="([^"]*)"[^>]+class="nbg"', chunk)
        em_title = first(r"<em>(.*?)</em>", chunk)
        zh, en = titles(em_title, image_title)
        intro = clean(first(r'<li class="intro">(.*?)</li>', chunk))
        year_match = re.search(r"(?:18|19|20)\d{2}", intro)
        cover = first(r'<img[^>]+src="([^"]+)"', chunk)
        watched_date = clean(first(r'<span class="date">(.*?)</span>', chunk))
        item = {
            "title": {"zh": zh, "en": en},
            "type": media_type,
            "douban_url": url,
        }
        if year_match:
            item["year"] = int(year_match.group(0))
        if cover:
            item["cover"] = cover
        if watched_date:
            item["watched_date"] = watched_date
        items.append(item)
    return items


def fetch(opener: urllib.request.OpenerDirector, url: str, retries: int = 3) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; zebramath-site importer/1.0)",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
        },
    )
    for attempt in range(retries):
        try:
            with opener.open(request, timeout=25) as response:
                text = response.read().decode("utf-8", errors="replace")
            if "subject-num" not in text or "异常请求" in text:
                raise RuntimeError("Douban returned a verification page")
            return text
        except Exception:
            if attempt + 1 == retries:
                raise
            time.sleep(2.0 * (attempt + 1))
    raise RuntimeError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("user_id", help="Numeric Douban user ID")
    parser.add_argument("--output", default="data/media_import.json")
    parser.add_argument("--delay", type=float, default=0.7, help="Delay between page requests")
    args = parser.parse_args()

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    collected: list[dict] = []
    expected_total = 0

    for douban_type, media_type in (("movie", "movie"), ("tv", "series")):
        query = {
            "start": 0,
            "sort": "time",
            "type": douban_type,
            "filter": "all",
            "mode": "grid",
        }
        base = f"https://movie.douban.com/people/{args.user_id}/collect"
        first_page = fetch(opener, f"{base}?{urllib.parse.urlencode(query)}")
        total_match = re.search(r"\d+-\d+&nbsp;/&nbsp;(\d+)", first_page)
        if not total_match:
            raise RuntimeError(f"Could not determine {douban_type} count")
        total = int(total_match.group(1))
        expected_total += total
        pages = math.ceil(total / 15)
        page_items = parse_page(first_page, media_type)
        collected.extend(page_items)
        print(f"{douban_type}: page 1/{pages}, {len(page_items)} items")

        for page in range(1, pages):
            time.sleep(max(args.delay, 0))
            query["start"] = page * 15
            source = fetch(opener, f"{base}?{urllib.parse.urlencode(query)}")
            page_items = parse_page(source, media_type)
            if not page_items:
                raise RuntimeError(f"No items parsed on {douban_type} page {page + 1}")
            collected.extend(page_items)
            print(f"{douban_type}: page {page + 1}/{pages}, {len(page_items)} items")

    unique = {item["douban_url"]: item for item in collected}
    media = sorted(unique.values(), key=lambda item: item.get("watched_date", ""), reverse=True)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"media": media}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {len(media)} unique titles into {output}.")
    if len(media) != expected_total:
        print(
            f"Note: Douban reports {expected_total} titles, but its public pages exposed "
            f"{len(media)} item cards. Missing or private cards were not fabricated."
        )


if __name__ == "__main__":
    main()
