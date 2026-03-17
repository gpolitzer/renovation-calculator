# JAX EPICS Permit Search Tool

Search Jacksonville's EPICS permit system for building permits by address.

## Prerequisites

- **Python 3.8+**
- **US VPN** (the site may block non-US IPs)
- **A Chromium-based browser** (Chrome, Edge, or Opera)

## Quick Setup

```bash
# 1. Install dependencies
pip install playwright

# 2. Install browser (uses Playwright's bundled Chromium)
playwright install chromium

# 3. Connect your VPN (must be US-based)
```

## Usage

### Step 1: Discover the Site Structure (run once)

Since the site is an Angular SPA that may change, run the discovery tool first:

```bash
# Run in headed mode so you can see what's happening
python discover_site.py --headed

# Or use your Opera browser
python discover_site.py --headed --browser "C:\Users\YOU\AppData\Local\Programs\Opera\opera.exe"
```

This will save screenshots and element data to `site_discovery/` so we can fine-tune the search selectors.

### Step 2: Search for Permits

```bash
# Basic search
python search_permits.py "8319 SPRINGTREE RD"

# Save results to CSV
python search_permits.py "8319 SPRINGTREE RD" --output permits.csv

# Save results to JSON
python search_permits.py "8319 SPRINGTREE RD" --output permits.json

# Watch the browser (headed mode) with debug screenshots
python search_permits.py "8319 SPRINGTREE RD" --headed --debug

# Use Opera browser
python search_permits.py "8319 SPRINGTREE RD" --browser "C:\path\to\opera.exe"
```

## Using with Opera Browser

Opera is Chromium-based, so Playwright can use it directly:

```bash
# Windows - typical Opera path
python search_permits.py "123 MAIN ST" --browser "C:\Users\YOU\AppData\Local\Programs\Opera\opera.exe"

# macOS
python search_permits.py "123 MAIN ST" --browser "/Applications/Opera.app/Contents/MacOS/Opera"
```

## Troubleshooting

1. **Site not loading**: Make sure your US VPN is connected
2. **No results found**: Try `--headed --debug` mode to see what's happening
3. **Wrong elements clicked**: Run `discover_site.py` and share the JSON files so we can update selectors
4. **Playwright can't install**: Try `playwright install --with-deps chromium`

## Output Format

### CSV
```
permit_number,year,link,raw_text
B-2024-001234,2024,https://jaxepics.coj.net/Permit/View/abc123,...
```

### JSON
```json
{
  "address": "8319 SPRINGTREE RD",
  "search_date": "2026-02-27T10:30:00",
  "permit_count": 3,
  "permits": [
    {"permit_number": "B-2024-001234", "year": "2024", "link": "..."}
  ]
}
```
