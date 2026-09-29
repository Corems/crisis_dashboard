import json
import re
from datetime import date, datetime
from pathlib import Path

import httpx

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

CONFIG_PATH = Path(__file__).parent.parent / "config" / "indicators.json"

PATTERN = re.compile(
    r"(?:increased|decreased|rose|fell|climbed|dropped|unchanged)?\s*to\s+([\d.]+)\s+points.*?from\s+([\d.]+)\s+points",
    re.IGNORECASE,
)


def load_scraper_config() -> list[dict]:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    return [item for item in raw if item.get("source") == "scraper"]


async def scrape_single(client: httpx.AsyncClient, item: dict) -> dict | None:
    fred_id = item["fred_id"]
    url = item["scrape_url"]

    try:
        resp = await client.get(url, timeout=15)
        resp.raise_for_status()

        match_meta = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', resp.text)
        if not match_meta:
            print(f"PMI [{fred_id}]: meta description not found")
            return None

        description = match_meta.group(1)
        match_values = PATTERN.search(description)

        if not match_values:
            print(f"PMI [{fred_id}]: values not parsed from: {description[:100]}")
            return None

        return {
            "fred_id": fred_id,
            "name": item["name"],
            "value": float(match_values.group(1)),
            "previous_value": float(match_values.group(2)),
            "fetched_at": datetime.utcnow(),
            "date": date.today(),
        }

    except Exception as e:
        print(f"PMI scrape error [{fred_id}]: {e}")
        return None


async def collect_pmi() -> list[dict]:
    configs = load_scraper_config()
    results = []

    async with httpx.AsyncClient(headers=HEADERS) as client:
        for item in configs:
            result = await scrape_single(client, item)
            if result:
                results.append(result)
            else:
                print(f"Skipping {item['fred_id']} — scrape failed")

    return results
