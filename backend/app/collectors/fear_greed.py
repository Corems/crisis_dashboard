from datetime import datetime

import httpx

URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MacroDashboard/1.0)"}


async def collect_fear_greed() -> dict:

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(URL, headers=HEADERS, timeout=10, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"Fear & Greed fetch error: {e}")
            raise

    fg = data.get("fear_and_greed", {})
    fg_hist = data.get("fear_and_greed_historical", {})
    hist_data = fg_hist.get("data", [])

    def _score_at(index: int) -> float | None:
        if index < len(hist_data):
            return float(hist_data[index].get("y", 0))
        return None

    return {
        "score": float(fg.get("score", 0)),
        "rating": fg.get("rating", ""),
        "previous_close": _score_at(1),
        "one_week_ago": _score_at(7),
        "one_month_ago": _score_at(30),
        "fetched_at": datetime.utcnow(),
    }
