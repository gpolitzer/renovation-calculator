---
name: jax-permit-search
description: "Search Jacksonville's EPICS permit system (jaxepics.coj.net) for building permits by address. Use this skill whenever the user mentions Jacksonville permits, COJ permits, EPICS permits, JaxEPICS, building permits for a Jacksonville address, or wants to look up permit history for a property in Jacksonville/Duval County FL. Also trigger when the user mentions jaxepics.coj.net or asks about permit records for any Jacksonville FL address."
---

# JAX EPICS Permit Search

This skill searches Jacksonville's EPICS permit database at jaxepics.coj.net for permits associated with a given address. It returns a list of permits with their permit numbers and years.

## Important Context

- The site is an **Angular SPA** that requires JavaScript rendering (traditional HTTP requests won't work)
- A **US VPN** is required to access the site
- The user may need to use **Opera browser** specifically
- The **Claude browser extension does not work** on this site

## How to Use This Skill

### Option 1: Run the Python Script (Recommended)

The script is located at `jax_permit_search/search_permits.py` in the user's workspace folder.

Tell the user to run:

```bash
# Make sure VPN is connected first!

# Basic usage
python search_permits.py "YOUR ADDRESS HERE"

# With Opera browser
python search_permits.py "YOUR ADDRESS HERE" --browser "C:\Users\...\Opera\opera.exe" --headed

# Save to CSV
python search_permits.py "YOUR ADDRESS HERE" --output permits.csv --headed --debug
```

### Option 2: First-Time Setup Discovery

If the script isn't finding the right elements, have the user run the discovery tool first:

```bash
python discover_site.py --headed --browser "C:\path\to\opera.exe"
```

This saves screenshots and DOM element maps to `site_discovery/`. The user can share these files back so the selectors in `search_permits.py` can be refined.

### Option 3: Manual Guidance

If the scripts can't be run, guide the user through manual steps:
1. Open Opera browser with US VPN connected
2. Go to https://jaxepics.coj.net/Search/AdvancedSearch
3. Select "Search by Address"
4. Enter the street address
5. Click Search
6. Review the permit list showing permit numbers and years

## Workflow When User Asks for Permits

1. Ask the user for the **street address** (just the street, no city/state needed since it's Jacksonville-specific)
2. Confirm their VPN is connected and they have the script installed
3. Help them run the script with the right arguments
4. If they share results or discovery data, help interpret or refine the search

## Troubleshooting

- **Timeout errors**: The site may be slow; increase timeout or use `--headed` to watch
- **No results**: Try different address formats (e.g., "SPRINGTREE RD" vs "SPRINGTREE ROAD")
- **Element not found**: Run `discover_site.py` to get updated selectors
- **VPN issues**: Must be a US-based VPN; some free VPNs may be blocked
