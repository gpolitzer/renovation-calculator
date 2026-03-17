# BRRRR Calculator

Renovation cost calculator for BRRRR real estate investing. Integrates with Jacksonville EPICS permit system.

## Stack
- Single self-contained HTML file (`brrrr-calculator.html`) — vanilla JS/CSS, zero dependencies
- Storage: `localStorage` (defaults), `IndexedDB` (projects)
- Permit search: Python + Playwright, Tampermonkey userscript (`jax_epics_bridge.user.js`)

## Rules
- **Price range → use midpoint:** `(X + Y) / 2`. E.g. $5k–$9k = **$7k** default.
- Keep calculator as one HTML file. No build tools, no external libs.
- Dark theme (dark blues + orange accents) — preserve it.
- New line items: follow the `BUILT-IN CATEGORIES & ROWS` pattern in the main file.
- **New rows must include a `defNote`** — a clear English explanation of what the item is and how it's calculated. Use simple language. Add Hebrew translations (בעברית) in parentheses for professional construction terms. If the row has dropdown menus, explain each option and what changes when you select it.
- Permit search needs US VPN. If selectors break, run `discover_site.py` to re-map.
