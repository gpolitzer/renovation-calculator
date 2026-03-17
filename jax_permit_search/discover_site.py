#!/usr/bin/env python3
"""
JAX EPICS Site Discovery Tool
Connects to your already-running Opera browser (with VPN active)
and maps out the search page structure.

USAGE:
    Step 1: Double-click launch_opera_debug.bat
    Step 2: In Opera, make sure VPN is ON
    Step 3: Run this script:
            python discover_site.py
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: Playwright not installed.")
    print("Run:  pip install playwright")
    print("Then: playwright install chromium")
    sys.exit(1)

BASE_URL    = "https://jaxepics.coj.net"
SEARCH_URL  = f"{BASE_URL}/Search/AdvancedSearch"
RESULTS_URL = f"{BASE_URL}/Search/SearchResults"
OUTPUT_DIR  = Path("site_discovery")
CDP_URL     = "http://localhost:9222"   # Opera remote debugging port


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# ── helpers ──────────────────────────────────────────────────────────────────

def safe_attr(el, attr):
    try:
        return el.get_attribute(attr) or ""
    except Exception:
        return ""

def safe_text(el, limit=120):
    try:
        return (el.inner_text() or "").strip()[:limit]
    except Exception:
        return ""

def safe_visible(el):
    try:
        return el.is_visible()
    except Exception:
        return False


# ── discovery ────────────────────────────────────────────────────────────────

def discover_page(page, url, name):
    log(f"Navigating to {url} ...")
    page.goto(url, wait_until="networkidle", timeout=60_000)
    time.sleep(3)

    OUTPUT_DIR.mkdir(exist_ok=True)
    page.screenshot(path=str(OUTPUT_DIR / f"{name}.png"), full_page=True)
    (OUTPUT_DIR / f"{name}.html").write_text(page.content(), encoding="utf-8")
    log(f"Saved screenshot and HTML for: {name}")

    elements = {
        "inputs":        [],
        "buttons":       [],
        "selects":       [],
        "radio_buttons": [],
        "tabs":          [],
        "labels":        [],
        "permit_links":  [],
    }

    # inputs
    for el in page.locator("input").all():
        elements["inputs"].append({
            "type":            safe_attr(el, "type"),
            "name":            safe_attr(el, "name"),
            "id":              safe_attr(el, "id"),
            "placeholder":     safe_attr(el, "placeholder"),
            "formcontrolname": safe_attr(el, "formcontrolname"),
            "aria_label":      safe_attr(el, "aria-label"),
            "class":           safe_attr(el, "class"),
            "visible":         safe_visible(el),
        })

    # buttons
    for el in page.locator("button, [role='button'], input[type='submit']").all():
        elements["buttons"].append({
            "text":    safe_text(el),
            "type":    safe_attr(el, "type"),
            "id":      safe_attr(el, "id"),
            "class":   safe_attr(el, "class"),
            "visible": safe_visible(el),
        })

    # selects
    for el in page.locator("select, mat-select, [role='listbox']").all():
        elements["selects"].append({
            "name":    safe_attr(el, "name"),
            "id":      safe_attr(el, "id"),
            "text":    safe_text(el, 300),
            "visible": safe_visible(el),
        })

    # radio buttons
    for el in page.locator("input[type='radio'], mat-radio-button").all():
        elements["radio_buttons"].append({
            "name":    safe_attr(el, "name"),
            "value":   safe_attr(el, "value"),
            "id":      safe_attr(el, "id"),
            "text":    safe_text(el),
            "visible": safe_visible(el),
        })

    # tabs
    for el in page.locator("[role='tab'], mat-tab-header .mat-tab-label, .nav-link").all():
        elements["tabs"].append({
            "text":    safe_text(el),
            "class":   safe_attr(el, "class"),
            "visible": safe_visible(el),
        })

    # labels
    for el in page.locator("label").all():
        elements["labels"].append({
            "text":    safe_text(el),
            "for":     safe_attr(el, "for"),
            "visible": safe_visible(el),
        })

    # permit links
    for el in page.locator("a").all():
        href = safe_attr(el, "href")
        text = safe_text(el)
        if any(k in (href + text).lower() for k in ["permit", "search", "address", "property"]):
            elements["permit_links"].append({
                "text":    text,
                "href":    href,
                "visible": safe_visible(el),
            })

    (OUTPUT_DIR / f"{name}_elements.json").write_text(
        json.dumps(elements, indent=2), encoding="utf-8"
    )
    log(f"Saved elements to: {name}_elements.json")

    # print summary
    print(f"\n{'='*55}")
    print(f"  PAGE: {name}")
    print(f"{'='*55}")
    for key, items in elements.items():
        visible = [e for e in items if e.get("visible")]
        if visible:
            print(f"\n  {key.upper()} ({len(visible)} visible):")
            for item in visible:
                label = (item.get("text") or item.get("placeholder") or
                         item.get("name") or item.get("id") or "")
                if label:
                    print(f"    · {label[:80]}")

    return elements


def capture_api_calls(context):
    """Open a new page and capture network calls made by the Angular app."""
    api_calls = []

    page = context.new_page()

    def on_response(response):
        url = response.url
        ct  = response.headers.get("content-type", "")
        if "application/json" in ct and any(
            k in url.lower() for k in ["api", "search", "permit", "address"]
        ):
            try:
                data = response.json()
                api_calls.append({"url": url, "status": response.status, "data": data})
            except Exception:
                api_calls.append({"url": url, "status": response.status, "data": None})

    page.on("response", on_response)
    page.goto(SEARCH_URL, wait_until="networkidle", timeout=60_000)
    time.sleep(4)

    if api_calls:
        out = OUTPUT_DIR / "api_calls.json"
        out.write_text(json.dumps(api_calls, indent=2), encoding="utf-8")
        log(f"Captured {len(api_calls)} API calls → {out}")
        for c in api_calls:
            log(f"  {c['status']}  {c['url']}")
    else:
        log("No JSON API calls detected on load.")

    page.close()
    return api_calls


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print()
    print("=" * 55)
    print("  JAX EPICS — Site Discovery")
    print("=" * 55)
    print()
    print("Connecting to Opera browser on localhost:9222 ...")
    print("(Make sure you ran launch_opera_debug.bat first!)")
    print()

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print()
            print("ERROR: Could not connect to Opera.")
            print()
            print("Make sure you:")
            print("  1. Closed all Opera windows")
            print("  2. Double-clicked launch_opera_debug.bat")
            print("  3. Waited for Opera to fully open")
            print()
            print(f"Technical detail: {e}")
            sys.exit(1)

        log("Connected to Opera successfully!")

        # When connecting via CDP, use the existing browser context
        # (creating a new_context() doesn't work with connect_over_cdp)
        contexts = browser.contexts
        if contexts:
            context = contexts[0]
            log(f"Using existing Opera context (has {len(context.pages)} tab(s))")
        else:
            context = browser.new_context()
            log("Created fresh context")

        # Discover the advanced-search page
        page = context.new_page()
        discover_page(page, SEARCH_URL, "advanced_search")
        page.close()

        # Capture background API calls
        capture_api_calls(context)

        browser.close()

    print()
    print("=" * 55)
    print("  DISCOVERY COMPLETE")
    print("=" * 55)
    print(f"\nFiles saved to:  site_discovery\\")
    print()
    print("Next step:")
    print("  Share the site_discovery folder (or paste the")
    print("  advanced_search_elements.json here) so I can")
    print("  fine-tune the search script for exact selectors.")
    print()


if __name__ == "__main__":
    main()
