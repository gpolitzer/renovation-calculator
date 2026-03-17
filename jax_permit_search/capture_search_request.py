#!/usr/bin/env python3
"""
JAX EPICS — Search Request Capture Tool

This script connects to your Opera browser, opens the JAX EPICS search page,
and waits for YOU to manually do one search by address. It then captures
the exact API request the site sends, so we can replicate it automatically.

USAGE:
    Step 1: Run launch_opera_debug.bat (close Opera first)
    Step 2: Run this script:  python capture_search_request.py
    Step 3: In the Opera window that opens, do ONE address search manually
    Step 4: This script captures the API call and saves it
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: Run:  pip install playwright")
    sys.exit(1)

BASE_URL   = "https://jaxepics.coj.net"
API_BASE   = "https://jaxepicsapi.coj.net"
SEARCH_URL = f"{BASE_URL}/Search/AdvancedSearch"
OUTPUT     = Path("site_discovery") / "captured_search.json"
CDP_URL    = "http://localhost:9222"


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def main():
    Path("site_discovery").mkdir(exist_ok=True)

    print()
    print("=" * 60)
    print("  JAX EPICS — Search Request Capture")
    print("=" * 60)
    print()

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print("ERROR: Could not connect to Opera.")
            print("  1. Close all Opera windows")
            print("  2. Double-click launch_opera_debug.bat")
            print("  3. Run this script again")
            sys.exit(1)

        contexts = browser.contexts
        context  = contexts[0] if contexts else browser.new_context()
        page     = context.new_page()

        captured = []

        def on_request(request):
            url = request.url
            if API_BASE in url and request.method in ("POST", "GET"):
                entry = {
                    "method":  request.method,
                    "url":     url,
                    "headers": dict(request.headers),
                    "body":    request.post_data,
                }
                captured.append(entry)
                log(f"→ {request.method} {url}")
                if request.post_data:
                    log(f"  BODY: {request.post_data[:300]}")

        def on_response(response):
            url = response.url
            if API_BASE in url and any(
                k in url.lower() for k in ["search", "permit", "result", "get"]
            ):
                try:
                    data = response.json()
                    for entry in captured:
                        if entry["url"] == url:
                            entry["response_status"] = response.status
                            entry["response_data"]   = data
                except Exception:
                    pass

        page.on("request",  on_request)
        page.on("response", on_response)

        log(f"Navigating to search page ...")
        page.goto(SEARCH_URL, wait_until="networkidle", timeout=60_000)

        print()
        print("=" * 60)
        print("  The search page is now open in Opera.")
        print()
        print("  PLEASE DO THIS NOW in the Opera window:")
        print("  1. Choose 'Search by Address' (or look for address field)")
        print("  2. Type a test address, e.g.:  8319 SPRINGTREE RD")
        print("  3. Click the Search button")
        print("  4. Wait for results to appear")
        print()
        print("  This script is watching all network calls...")
        print("  Press Ctrl+C here when you have seen results in Opera.")
        print("=" * 60)
        print()

        # Wait and keep monitoring until user presses Ctrl+C
        try:
            while True:
                time.sleep(1)
                if len(captured) > 0:
                    # Show count of captured calls
                    search_calls = [c for c in captured if "search" in c["url"].lower() or "result" in c["url"].lower()]
                    if search_calls:
                        print(f"\r  Captured {len(captured)} API calls ({len(search_calls)} search-related)...", end="", flush=True)
        except KeyboardInterrupt:
            print()

        page.close()
        browser.close()

    # Save everything
    OUTPUT.write_text(json.dumps(captured, indent=2, default=str), encoding="utf-8")
    log(f"Saved {len(captured)} captured API calls to: {OUTPUT}")

    # Print summary of interesting calls
    print()
    print("=" * 60)
    print("  CAPTURED API CALLS SUMMARY")
    print("=" * 60)
    for entry in captured:
        body = entry.get("body") or ""
        print(f"\n  {entry['method']}  {entry['url']}")
        if body:
            print(f"  Body: {body[:200]}")
        resp = entry.get("response_data")
        if resp:
            resp_str = str(resp)[:150]
            print(f"  Response preview: {resp_str}")

    print()
    print(f"Full details saved to: {OUTPUT}")
    print()
    print("Share the output above (or the captured_search.json file)")
    print("so we can build the final automated search script.")


if __name__ == "__main__":
    main()
