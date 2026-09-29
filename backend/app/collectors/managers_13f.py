import asyncio
import re
from datetime import datetime

import httpx

from app.collectors.buffett import (
    HEADERS,
    _compare_with_previous,
    _parse_infotable_xml,
)

EDGAR_SUBMISSIONS_BASE = "https://data.sec.gov/submissions"
EDGAR_ARCHIVES_BASE = "https://www.sec.gov/Archives/edgar/data"

MANAGERS: dict[str, dict] = {
    "bridgewater": {
        "cik": "0001350694",
        "name": "Bridgewater Associates",
        "manager": "Ray Dalio",
    },
    "scion": {
        "cik": "0001649339",
        "name": "Scion Asset Management",
        "manager": "Michael Burry",
    },
    "pershing": {
        "cik": "0001336528",
        "name": "Pershing Square Capital Management",
        "manager": "Bill Ackman",
    },
}


async def _get_filings_for_cik(client: httpx.AsyncClient, cik: str, count: int = 2) -> list[dict]:

    resp = await client.get(
        f"{EDGAR_SUBMISSIONS_BASE}/CIK{cik}.json",
        headers=HEADERS,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    recent = data["filings"]["recent"]
    forms = recent["form"]
    accessions = recent["accessionNumber"]
    filing_dates = recent["filingDate"]
    report_dates = recent.get("reportDate", [""] * len(forms))

    results = []
    for i, form in enumerate(forms):
        if form == "13F-HR":
            results.append(
                {
                    "accession": accessions[i],
                    "filing_date": filing_dates[i],
                    "period_of_report": report_dates[i],
                }
            )
            if len(results) >= count:
                break

    return results


async def _find_xml_in_filing(
    client: httpx.AsyncClient,
    cik_nodash: str,
    accession: str,
    manager_key: str,
) -> str | None:

    accession_dir = accession.replace("-", "")
    dir_url = f"{EDGAR_ARCHIVES_BASE}/{cik_nodash}/{accession_dir}/"

    await asyncio.sleep(0.15)
    resp = await client.get(dir_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    xml_files = re.findall(r'href="([^"]+\.xml)"', resp.text, re.IGNORECASE)
    if not xml_files:
        return None

    filenames = [f.split("/")[-1] for f in xml_files]

    for filename in filenames:
        if filename.lower() == "primary_doc.xml":
            continue
        if re.match(r"^\d+\.xml$", filename):
            return filename
        if "infotable" in filename.lower() or "13f" in filename.lower():
            return filename

    for filename in filenames:
        if filename.lower() != "primary_doc.xml":
            return filename

    return None


async def _fetch_holdings_for_cik(
    client: httpx.AsyncClient,
    cik_nodash: str,
    accession: str,
    manager_key: str,
) -> tuple[list[dict], float]:

    xml_filename = await _find_xml_in_filing(client, cik_nodash, accession, manager_key)
    if not xml_filename:
        print(f"managers_13f [{manager_key}]: no infotable XML found for {accession}")
        return [], 0.0

    accession_dir = accession.replace("-", "")
    xml_url = f"{EDGAR_ARCHIVES_BASE}/{cik_nodash}/{accession_dir}/{xml_filename}"

    await asyncio.sleep(0.15)
    resp = await client.get(xml_url, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    return _parse_infotable_xml(resp.text)


async def _collect_manager(
    client: httpx.AsyncClient,
    manager_key: str,
    info: dict,
) -> dict | None:

    cik = info["cik"]
    cik_nodash = str(int(cik))  # strip leading zeros: "0001350694" → "1350694"

    try:
        filings = await _get_filings_for_cik(client, cik, count=2)
        if not filings:
            print(f"managers_13f [{manager_key}]: no 13F-HR filings found")
            return None

        latest = filings[0]
        current_holdings, total_value = await _fetch_holdings_for_cik(
            client, cik_nodash, latest["accession"], manager_key
        )

        previous_holdings: list[dict] = []
        if len(filings) > 1:
            await asyncio.sleep(0.2)
            previous_holdings, _ = await _fetch_holdings_for_cik(
                client, cik_nodash, filings[1]["accession"], manager_key
            )

        annotated = _compare_with_previous(current_holdings, previous_holdings)
        now = datetime.utcnow()

        return {
            "filing": {
                "accession_number": latest["accession"],
                "filing_date": latest["filing_date"],
                "period_of_report": latest["period_of_report"],
                "total_value_usd": total_value,
                "manager_key": manager_key,
                "manager_name": info["name"],
                "fetched_at": now,
            },
            "holdings": [
                {
                    **h,
                    "manager_key": manager_key,
                    "filing_date": latest["filing_date"],
                    "created_at": now,
                }
                for h in annotated
            ],
        }

    except Exception as e:
        print(f"managers_13f [{manager_key}]: error — {e}")
        return None


async def collect_all() -> list[dict]:

    results = []
    async with httpx.AsyncClient() as client:
        for i, (manager_key, info) in enumerate(MANAGERS.items()):
            if i > 0:
                await asyncio.sleep(1.0)  # pause between managers
            result = await _collect_manager(client, manager_key, info)
            if result:
                results.append(result)
                print(f"managers_13f [{manager_key}]: {len(result['holdings'])} holdings")

    return results
