import asyncio
import re
from datetime import datetime
from xml.etree import ElementTree as ET

import httpx

CIK = "0001067983"
CIK_NODASH = "1067983"
EDGAR_SUBMISSIONS = "https://data.sec.gov/submissions"
EDGAR_ARCHIVES = f"https://www.sec.gov/Archives/edgar/data/{CIK_NODASH}"
HEADERS = {"User-Agent": "MacroDashboard contact@example.com", "Accept-Encoding": "gzip, deflate"}

# Best-effort company name → ticker mapping for common Berkshire holdings
COMPANY_TO_TICKER: dict[str, str] = {
    "APPLE INC": "AAPL",
    "BANK OF AMERICA": "BAC",
    "AMERICAN EXPRESS": "AXP",
    "COCA COLA": "KO",
    "COCA-COLA": "KO",
    "CHEVRON CORP": "CVX",
    "OCCIDENTAL PETROLEUM": "OXY",
    "KRAFT HEINZ": "KHC",
    "MOODYS CORP": "MCO",
    "MOODY'S CORP": "MCO",
    "DAVITA INC": "DVA",
    "CITIGROUP INC": "C",
    "HP INC": "HPQ",
    "CHARTER COMMUNICATIONS": "CHTR",
    "VERISIGN INC": "VRSN",
    "VISA INC": "V",
    "AMAZON COM INC": "AMZN",
    "AMAZON.COM INC": "AMZN",
    "CAPITAL ONE FINANCIAL": "COF",
    "NU HOLDINGS": "NU",
    "LIBERTY MEDIA": "LSXMA",
    "SIRIUS XM": "SIRI",
    "T-MOBILE US INC": "TMUS",
    "KROGER CO": "KR",
    "MARSH MCLENNAN": "MMC",
    "ALLY FINANCIAL": "ALLY",
    "SNOWFLAKE INC": "SNOW",
    "BYD CO": "BYDDY",
    "PILOT CORP": "FLY",
}


def _resolve_ticker(name: str) -> str:
    name_upper = name.upper()
    for key, ticker in COMPANY_TO_TICKER.items():
        if key in name_upper:
            return ticker
    words = name_upper.split()
    return words[0][:6] if words else "???"


async def _get_latest_13f_filings(client: httpx.AsyncClient, count: int = 2) -> list[dict]:

    resp = await client.get(f"{EDGAR_SUBMISSIONS}/CIK{CIK}.json", headers=HEADERS, timeout=20)
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


async def _find_infotable_xml(client: httpx.AsyncClient, accession: str) -> str | None:

    accession_dir = accession.replace("-", "")
    dir_url = f"{EDGAR_ARCHIVES}/{accession_dir}/"

    await asyncio.sleep(0.15)
    resp = await client.get(dir_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    # find all XML files in the directory
    xml_files = re.findall(r'href="([^"]+\.xml)"', resp.text, re.IGNORECASE)

    if not xml_files:
        return None

    # strip absolute URLs down to relative filenames
    filenames = []
    for f in xml_files:
        filename = f.split("/")[-1]
        filenames.append(filename)

    # look for the infotable file (usually numeric or contains 'infotable')
    # primary_doc.xml — this is the cover page, skip it
    for filename in filenames:
        if filename.lower() == "primary_doc.xml":
            continue
        if re.match(r"^\d+\.xml$", filename):
            # numeric filename — this is the infotable (e.g. 50240.xml)
            return filename
        if "infotable" in filename.lower() or "13f" in filename.lower():
            return filename

    # nothing matched — fall back to the first non-primary XML
    for filename in filenames:
        if filename.lower() != "primary_doc.xml":
            return filename

    return None


async def _fetch_holdings(client: httpx.AsyncClient, accession: str) -> tuple[list[dict], float]:

    xml_filename = await _find_infotable_xml(client, accession)
    if not xml_filename:
        print(f"Buffett: no infotable XML found for {accession}")
        return [], 0.0

    accession_dir = accession.replace("-", "")
    xml_url = f"{EDGAR_ARCHIVES}/{accession_dir}/{xml_filename}"

    await asyncio.sleep(0.15)
    resp = await client.get(xml_url, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    return _parse_infotable_xml(resp.text)


def _parse_infotable_xml(xml_text: str) -> tuple[list[dict], float]:

    # remove all namespace declarations
    xml_text = re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', "", xml_text)
    # remove xsi:schemaLocation which breaks the parser
    xml_text = re.sub(r'\s+xsi:schemaLocation="[^"]*"', "", xml_text)
    # remove namespace prefixes from tags (<ns:tag> → <tag>)
    xml_text = re.sub(r"<(/?)[\w]+:", r"<\1", xml_text)

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"Buffett XML parse error: {e}")
        return [], 0.0

    # aggregate by company name (one issuer may have multiple rows)
    aggregated: dict[str, dict] = {}

    for info in root.findall(".//infoTable"):
        name = (info.findtext("nameOfIssuer") or "").strip().upper()
        value_text = info.findtext("value")
        shr_elem = info.find(".//sshPrnamt")

        if not name or not value_text:
            continue

        try:
            value_usd = float(value_text)
            shares = int(shr_elem.text) if shr_elem is not None and shr_elem.text else 0
        except (ValueError, TypeError):
            continue

        if name in aggregated:
            aggregated[name]["value_usd"] += value_usd
            aggregated[name]["shares"] += shares
        else:
            aggregated[name] = {
                "company_name": name,
                "ticker": _resolve_ticker(name),
                "value_usd": value_usd,
                "shares": shares,
            }

    holdings = sorted(aggregated.values(), key=lambda x: x["value_usd"], reverse=True)
    total_value = sum(h["value_usd"] for h in holdings)

    for h in holdings:
        h["portfolio_pct"] = (
            round(h["value_usd"] / total_value * 100, 2) if total_value > 0 else 0.0
        )

    return holdings[:15], total_value


def _compare_with_previous(current: list[dict], previous: list[dict]) -> list[dict]:

    prev_map = {h["company_name"]: h for h in previous}

    result = []
    for h in current:
        name = h["company_name"]
        prev = prev_map.get(name)

        if prev is None:
            change_type = "new"
            change_pct = None
        else:
            prev_val = prev["value_usd"]
            curr_val = h["value_usd"]
            change_pct = round((curr_val - prev_val) / prev_val * 100, 1) if prev_val > 0 else None

            if change_pct is None:
                change_type = "unchanged"
            elif change_pct > 1.0:
                change_type = "increased"
            elif change_pct < -1.0:
                change_type = "decreased"
            else:
                change_type = "unchanged"

        result.append({**h, "change_type": change_type, "change_pct": change_pct})

    return result


async def collect_buffett() -> dict:

    async with httpx.AsyncClient() as client:
        filings = await _get_latest_13f_filings(client, count=2)
        if not filings:
            raise ValueError("No 13F-HR filings found for Berkshire Hathaway on EDGAR")

        latest = filings[0]
        current_holdings, total_value = await _fetch_holdings(client, latest["accession"])

        previous_holdings: list[dict] = []
        if len(filings) > 1:
            await asyncio.sleep(0.2)
            previous_holdings, _ = await _fetch_holdings(client, filings[1]["accession"])

        annotated = _compare_with_previous(current_holdings, previous_holdings)
        now = datetime.utcnow()

        return {
            "filing": {
                "accession_number": latest["accession"],
                "filing_date": latest["filing_date"],
                "period_of_report": latest["period_of_report"],
                "total_value_usd": total_value,
                "fetched_at": now,
            },
            "holdings": [
                {
                    **h,
                    "filing_date": latest["filing_date"],
                    "created_at": now,
                }
                for h in annotated
            ],
        }
