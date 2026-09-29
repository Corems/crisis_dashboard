import asyncio
import csv
import io
import os
import zipfile
from datetime import date, datetime
from pathlib import Path

import httpx

CFTC_FIN_URL = "https://www.cftc.gov/files/dea/history/fut_fin_txt_{year}.zip"
CFTC_DISAGG_URL = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"

CACHE_DIR = Path(os.getenv("COT_CACHE_DIR", "/tmp/cot_cache"))
CACHE_TTL_DAYS = 7

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MacroDashboard/1.0)"}

# key: (exact_market_name, file_type, long_col, short_col)
INSTRUMENTS: dict[str, tuple[str, str, str, str]] = {
    "crude_oil": (
        "CRUDE OIL, LIGHT SWEET-WTI - ICE FUTURES EUROPE",
        "disagg",
        "M_Money_Positions_Long_All",
        "M_Money_Positions_Short_All",
    ),
    "gold": (
        "GOLD - COMMODITY EXCHANGE INC.",
        "disagg",
        "M_Money_Positions_Long_All",
        "M_Money_Positions_Short_All",
    ),
    "sp500": (
        "E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE",
        "fin",
        "Lev_Money_Positions_Long_All",  # ← was NonComm
        "Lev_Money_Positions_Short_All",  # ← was NonComm
    ),
    "euro": (
        "EURO FX - CHICAGO MERCANTILE EXCHANGE",
        "fin",
        "Lev_Money_Positions_Long_All",  # ← was NonComm
        "Lev_Money_Positions_Short_All",  # ← was NonComm
    ),
}

_NAME_TO_KEY: dict[str, str] = {v[0]: k for k, v in INSTRUMENTS.items()}

# Each entry: (report_date, nc_long, nc_short, c_long, c_short, oi)
_Entry = tuple[date, int, int, int, int, int]

DATE_COL = "As_of_Date_In_Form_YYMMDD"  # capital I — exactly as it appears in the CSV


def _cache_path(file_key: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{file_key}.zip"


def _is_cache_fresh(path: Path) -> bool:
    if not path.exists():
        return False
    age = datetime.utcnow() - datetime.utcfromtimestamp(path.stat().st_mtime)
    return age.days < CACHE_TTL_DAYS


async def _fetch_zip(url_template: str, file_key: str) -> bytes:
    path = _cache_path(file_key)
    if _is_cache_fresh(path):
        print(f"COT: using cached ZIP for {file_key}")
        return path.read_bytes()

    year = int(file_key.split("_")[-1])
    url = url_template.format(year=year)

    try:
        async with httpx.AsyncClient(headers=HEADERS) as client:
            resp = await client.get(url, timeout=60, follow_redirects=True)
            resp.raise_for_status()
            data = resp.content
            path.write_bytes(data)
            print(f"COT: downloaded {url} ({len(data) // 1024} KB)")
            return data
    except Exception as e:
        print(f"COT fetch error [{file_key}]: {e}")
        if path.exists():
            print(f"COT: falling back to stale cache for {file_key}")
            return path.read_bytes()
        return b""


def _parse_zip_sync(zip_bytes: bytes, file_type: str) -> dict[str, list[_Entry]]:
    if not zip_bytes:
        return {}

    # instruments for this file type
    relevant = {name: key for key, (name, ftype, _, _) in INSTRUMENTS.items() if ftype == file_type}
    long_col_map = {name: INSTRUMENTS[key][2] for name, key in relevant.items()}
    short_col_map = {name: INSTRUMENTS[key][3] for name, key in relevant.items()}

    result: dict[str, list[_Entry]] = {k: [] for k in relevant.values()}

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            csv_name = next(
                (
                    n
                    for n in zf.namelist()
                    if n.lower().endswith(".txt") or n.lower().endswith(".csv")
                ),
                None,
            )
            if not csv_name:
                print(f"COT [{file_type}]: no CSV/TXT in ZIP")
                return {}

            with zf.open(csv_name) as raw:
                reader = csv.DictReader(io.TextIOWrapper(raw, encoding="latin-1"))
                for row in reader:
                    name = row.get("Market_and_Exchange_Names", "").strip()
                    if name not in relevant:
                        continue
                    key = relevant[name]
                    try:
                        raw_date = row[DATE_COL].strip()
                        report_date = datetime.strptime(raw_date, "%y%m%d").date()
                        nc_long = int(row[long_col_map[name]].replace(",", ""))
                        nc_short = int(row[short_col_map[name]].replace(",", ""))
                        # comm positions — only in the fin file
                        c_long = int(row.get("Comm_Positions_Long_All", "0").replace(",", "") or 0)
                        c_short = int(
                            row.get("Comm_Positions_Short_All", "0").replace(",", "") or 0
                        )
                        oi = int(row.get("Open_Interest_All", "0").replace(",", "") or 0)
                        result[key].append((report_date, nc_long, nc_short, c_long, c_short, oi))
                    except (ValueError, KeyError):
                        continue
    except Exception as e:
        print(f"COT parse error [{file_type}]: {e}")

    for key in result:
        result[key].sort(key=lambda x: x[0], reverse=True)

    return result


def _compute_rows(instrument_key: str, entries: list[_Entry], now: datetime) -> list[dict]:
    rows = []
    for i, (report_date, nc_long, nc_short, c_long, c_short, oi) in enumerate(entries[:52]):
        nc_net = nc_long - nc_short
        nc_net_pct_oi = round(nc_net / oi * 100, 2) if oi else None

        if i + 1 < len(entries):
            prev_nc_net = entries[i + 1][1] - entries[i + 1][2]
            net_change_wow = nc_net - prev_nc_net
        else:
            net_change_wow = None

        rows.append(
            {
                "report_date": report_date,
                "instrument": instrument_key,
                "noncomm_long": nc_long,
                "noncomm_short": nc_short,
                "noncomm_net": nc_net,
                "noncomm_net_pct_oi": nc_net_pct_oi,
                "comm_long": c_long,
                "comm_short": c_short,
                "open_interest": oi,
                "net_change_wow": net_change_wow,
                "created_at": now,
            }
        )

    return rows


async def collect_all() -> list[dict]:
    year = datetime.utcnow().year

    fin_cur, fin_prev, disagg_cur, disagg_prev = await asyncio.gather(
        _fetch_zip(CFTC_FIN_URL, f"fin_{year}"),
        _fetch_zip(CFTC_FIN_URL, f"fin_{year - 1}"),
        _fetch_zip(CFTC_DISAGG_URL, f"disagg_{year}"),
        _fetch_zip(CFTC_DISAGG_URL, f"disagg_{year - 1}"),
    )

    loop = asyncio.get_event_loop()

    fin_cur_p, fin_prev_p, disagg_cur_p, disagg_prev_p = await asyncio.gather(
        loop.run_in_executor(None, _parse_zip_sync, fin_cur, "fin"),
        loop.run_in_executor(None, _parse_zip_sync, fin_prev, "fin"),
        loop.run_in_executor(None, _parse_zip_sync, disagg_cur, "disagg"),
        loop.run_in_executor(None, _parse_zip_sync, disagg_prev, "disagg"),
    )

    merged: dict[str, list[_Entry]] = {k: [] for k in INSTRUMENTS}
    for parsed in [fin_cur_p, fin_prev_p, disagg_cur_p, disagg_prev_p]:
        for key, entries in parsed.items():
            merged[key].extend(entries)
    for key in merged:
        merged[key].sort(key=lambda x: x[0], reverse=True)

    now = datetime.utcnow()
    collected = []
    for instrument_key, entries in merged.items():
        if not entries:
            print(f"COT: no data for {instrument_key}, skipping")
            continue
        rows = _compute_rows(instrument_key, entries, now)
        collected.extend(rows)
        print(f"COT: computed {len(rows)} rows for {instrument_key}")

    return collected
