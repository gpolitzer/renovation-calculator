#!/usr/bin/env python3
"""
JAX EPICS Permit Search
Searches Jacksonville's permit database by address using the real API.

REQUIREMENTS:
    pip install playwright
    playwright install chromium

HOW TO USE:
    Step 1: Close all Opera windows
    Step 2: Double-click  launch_opera_debug.bat
    Step 3: Make sure VPN is ON in Opera
    Step 4: Run this script:
            python search_permits.py "8319 SPRINGTREE RD"
            python search_permits.py "123 MAIN ST" --output results.csv
"""

import argparse
import csv
import json
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: Run:  pip install playwright && playwright install chromium")
    sys.exit(1)

SITE_URL = "https://jaxepics.coj.net"
API_URL  = "https://jaxepicsapi.coj.net/api/AdvancedSearches/Advanced"
CDP_URL  = "http://localhost:9222"

import re as _re
_ABBREV = {
    r'\bROAD\b':      'RD',    r'\bSTREET\b':   'ST',
    r'\bAVENUE\b':    'AVE',   r'\bDRIVE\b':    'DR',
    r'\bLANE\b':      'LN',    r'\bCOURT\b':    'CT',
    r'\bCIRCLE\b':    'CIR',   r'\bBOULEVARD\b':'BLVD',
    r'\bPLACE\b':     'PL',    r'\bTERRACE\b':  'TER',
    r'\bTRAIL\b':     'TRL',   r'\bPARKWAY\b':  'PKWY',
    r'\bHIGHWAY\b':   'HWY',   r'\bNORTH\b':    'N',
    r'\bSOUTH\b':     'S',     r'\bEAST\b':     'E',
    r'\bWEST\b':      'W',
}

def normalize_address(raw: str) -> str:
    """Upper-case and convert long-form street words to USPS abbreviations."""
    text = raw.strip().upper()
    for pattern, abbrev in _ABBREV.items():
        text = _re.sub(pattern, abbrev, text)
    return _re.sub(r'\s+', ' ', text)


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", file=sys.stderr)


def search_permits_via_api(page, address, page_size=200):
    """
    Call the JAX EPICS API directly from inside the browser using fetch().
    This automatically uses Opera's VPN and session cookies.
    Returns the raw JSON response from the API.
    """
    address = normalize_address(address)   # "8319 Springtree Road" → "8319 SPRINGTREE RD"
    log(f"Normalized address: {address}")

    url = (
        f"{API_URL}"
        f"?page=1&pageSize={page_size}"
        f"&filter=&sortActive=FullPermitNumber&sortDirection=asc&forSpreadSheet=false"
    )

    body = {
        "SavedSearchColumns": [
            {"ColumnId": 1}, {"ColumnId": 2}, {"ColumnId": 3}, {"ColumnId": 4},
            {"ColumnId": 5}, {"ColumnId": 6}, {"ColumnId": 7}, {"ColumnId": 8}
        ],
        "SavedSearchFilters": [
            {
                "SavedSearchFilterId": 0,
                "SavedSearchId": 0,
                "ColumnId": 8,
                "OperatorId": 2,   # 2 = Contains (more forgiving than 1 = Equals)
                "Order": -1,
                "Obj": {"SearchString": address},
                "groupedSectionControls": {},
                "Completed": True,
                "DateEntered": datetime.now().strftime("%a %b %d %Y"),
                "DateUpdated": datetime.now().strftime("%a %b %d %Y"),
                "EvalValueString": json.dumps({"SearchString": address}),
                "IsActive": True,
                "SavedSearch": None,
                "DisplayInWidget": True,
                "PinnedInWidget": False,
                "Sort": 0
            }
        ],
        "UserSavedSearches": [],
        "UserSavedSearchWidgets": [],
        "TableId": 82
    }

    log(f"Calling JAX EPICS API for: {address}")

    # Run the fetch() call inside Opera so it uses the browser's VPN + session
    result = page.evaluate(
        """async ([url, body]) => {
            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'content-type': 'application/json',
                        'accept': 'application/json, text/plain, */*',
                        'referer': 'https://jaxepics.coj.net/',
                        'ignoreloading': ''
                    },
                    body: JSON.stringify(body)
                });

                if (!response.ok) {
                    return { error: `HTTP ${response.status}: ${response.statusText}` };
                }

                const data = await response.json();
                return { success: true, data: data };
            } catch (e) {
                return { error: e.toString() };
            }
        }""",
        [url, body]
    )

    return result


def parse_results(api_response, address):
    """
    Parse the API response and extract permit number + year.
    Returns a list of dicts: [{'permit_number': ..., 'year': ...}, ...]
    """
    if not api_response:
        log("ERROR: No response from API")
        return []

    if "error" in api_response:
        log(f"ERROR from API: {api_response['error']}")
        return []

    data = api_response.get("data", {})

    # The response is paginated: { values: [...], count: N, page: 1, pageSize: 200 }
    values = data.get("values", []) if isinstance(data, dict) else []

    if not values:
        # Try if data itself is a list
        if isinstance(data, list):
            values = data
        else:
            log(f"No results found for: {address}")
            log(f"API returned: {str(data)[:200]}")
            return []

    import re

    permits = []
    for item in values:
        # Permit number
        permit_num = (
            item.get("FullPermitNumber") or
            item.get("fullPermitNumber") or
            item.get("PermitNumber") or
            item.get("permitNumber") or
            item.get("key") or
            item.get("title") or
            ""
        )

        # Permit type — returned directly by the API
        permit_type = (
            item.get("PermitTypeDescription") or
            item.get("permitTypeDescription") or
            item.get("PermitType") or
            item.get("permitType") or
            ""
        )

        # Year — prefer DateIssued field, fall back to parsing permit number
        year = ""
        date_issued = item.get("DateIssued") or item.get("dateIssued") or ""
        if date_issued:
            # Format: "6/28/2002 12:00:00 AM"  →  "2002"
            m = re.search(r'(\d{4})', str(date_issued))
            if m:
                year = m.group(1)

        if not year and permit_num:
            # 4-digit year in permit number: B-2024-001234
            m4 = re.search(r'-(\d{4})-', str(permit_num))
            if m4:
                year = m4.group(1)
            else:
                # 2-digit year: B-02-32207  →  2002
                m2 = re.search(r'-(\d{2})-', str(permit_num))
                if m2:
                    year = str(2000 + int(m2.group(1)))

        if not year:
            raw_year = item.get("issuedYear") or item.get("IssuedYear") or item.get("Year") or ""
            year = str(raw_year) if raw_year and str(raw_year) != "None" else ""

        if permit_num:
            permits.append({
                "permit_number": permit_num,
                "permit_type":   permit_type,
                "year":          year,
                "raw":           item
            })

    return permits


def display_results(permits, address):
    """Print results to the terminal in a clean table."""
    print()
    print("=" * 55)
    print(f"  PERMITS FOR: {address}")
    print("=" * 55)

    if not permits:
        print("  No permits found.")
        print("=" * 55)
        return

    print(f"  {'Permit Number':<25} {'Permit Type':<30} {'Year'}")
    print(f"  {'-'*25} {'-'*30} {'-'*6}")
    for p in permits:
        print(f"  {p['permit_number']:<25} {p['permit_type']:<30} {p['year']}")

    print()
    print(f"  Total: {len(permits)} permit(s) found")
    print("=" * 55)


def save_to_csv(permits, output_path, address):
    """Save permit list to a CSV file."""
    path = Path(output_path)
    if not path.suffix:
        path = path.with_suffix(".csv")

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["permit_number", "permit_type", "year"])
        writer.writeheader()
        for p in permits:
            writer.writerow({
                "permit_number": p["permit_number"],
                "permit_type":   p["permit_type"],
                "year":          p["year"],
            })

    log(f"Results saved to: {path}")


def save_debug(api_response, address):
    """Save raw API response for debugging."""
    debug_path = Path("site_discovery") / "last_search_response.json"
    Path("site_discovery").mkdir(exist_ok=True)
    debug_path.write_text(
        json.dumps({"address": address, "response": api_response}, indent=2, default=str),
        encoding="utf-8"
    )
    log(f"Raw API response saved to: {debug_path}")


def run_search(address, cdp_url=CDP_URL):
    """
    Core search logic — connects to Opera, calls the API, returns list of permit dicts.
    Raises RuntimeError if Opera is not reachable.
    Each permit dict has keys: permit_number, permit_type, year.
    """
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(cdp_url)
        except Exception as e:
            raise RuntimeError(f"Cannot connect to Opera at {cdp_url}: {e}") from e

        contexts = browser.contexts
        context  = contexts[0] if contexts else browser.new_context()

        page = context.new_page()
        log("Opening JAX EPICS site to establish session...")
        page.goto(SITE_URL, wait_until="networkidle", timeout=60_000)
        time.sleep(2)

        api_response = search_permits_via_api(page, address)
        page.close()
        browser.close()

    return parse_results(api_response, address)


def main():
    parser = argparse.ArgumentParser(
        description="Search Jacksonville EPICS for permits by address",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python search_permits.py "8319 SPRINGTREE RD"
    python search_permits.py "123 MAIN ST" --output permits.csv
    python search_permits.py "123 MAIN ST" --json
    python search_permits.py "123 MAIN ST" --debug
        """
    )
    parser.add_argument("address", help="Street address, e.g. '8319 SPRINGTREE RD'")
    parser.add_argument("--output", "-o", help="Save results to this CSV file")
    parser.add_argument("--json",   action="store_true", help="Print results as JSON array to stdout (for bridge server)")
    parser.add_argument("--debug",  action="store_true", help="Save raw API response for troubleshooting")
    parser.add_argument("--connect", default=CDP_URL,
                        help=f"Opera CDP URL (default: {CDP_URL})")
    args = parser.parse_args()

    if not args.json:
        print()
        print("=" * 55)
        print("  JAX EPICS Permit Search")
        print("=" * 55)
        log(f"Address: {args.address}")
        log("Connecting to Opera (make sure launch_opera_debug.bat is running)...")

    try:
        permits = run_search(args.address, cdp_url=args.connect)
    except RuntimeError as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print()
            print("ERROR: Cannot connect to Opera.")
            print()
            print("Please do this first:")
            print("  1. Close ALL Opera windows")
            print("  2. Double-click  launch_opera_debug.bat")
            print("  3. Wait for Opera to open")
            print("  4. Make sure VPN is ON in Opera")
            print("  5. Run this script again")
        sys.exit(1)

    # ── JSON mode (used by local_server.py) ──────────────────────────────────
    if args.json:
        output = [
            {"permit_number": p["permit_number"],
             "permit_type":   p["permit_type"],
             "year":          p["year"]}
            for p in permits
        ]
        print(json.dumps(output))
        return 0

    # ── Human-readable mode ──────────────────────────────────────────────────
    display_results(permits, args.address)

    if args.output and permits:
        save_to_csv(permits, args.output, args.address)

    if not permits and args.debug:
        log("No permits parsed. Run with --debug and check site_discovery/last_search_response.json")

    return 0 if permits else 1


if __name__ == "__main__":
    sys.exit(main())
