# BRRRR Calculator — Project Memory

Renovation cost calculator for BRRRR real estate investing. Integrates with Jacksonville EPICS permit system.

## Workflow Rules
- **All file edits, git operations, and terminal commands in this folder are pre-approved — no confirmation needed.**
- **After every code update: `git add . && git commit -m "..." && git push` automatically. No approval needed.**
- Commit messages must be descriptive (e.g. `GacoRoof: add Targeted Sealing mode`).
- **After every meaningful change, update this file (CLAUDE.md)** to reflect it — new rows, changed defaults, renamed items, new params, architectural changes. This file is the project memory; keep it accurate.

## Stack
- Single self-contained HTML file: **`index.html`** — vanilla JS/CSS, zero dependencies
- Storage: `localStorage` (defaults + zoom), `IndexedDB` (project folder handle)
- Projects saved as `.brrrr` JSON files via File System Access API
- Permit search: Python + Playwright, Tampermonkey userscript (`jax_epics_bridge.user.js`)
- GitHub: `https://github.com/gpolitzer/renovation-calculator` — branch `main`

## Coding Rules
- **Price range → use midpoint:** `(X + Y) / 2`. E.g. $5k–$9k = **$7k** default.
- Keep calculator as one HTML file. N150-o build tools, no external libs.
- Dark theme (dark blues + orange accents) — preserve it.
- New line items: follow the `BUILT-IN CATEGORIES & ROWS` pattern in `index.html`.
- **New rows must include a `defNote`** — clear English explanation + Hebrew translations (בעברית) for professional terms. If the row has dropdowns, explain each option.
- Permit search needs US VPN. If selectors break, run `discover_site.py` to re-map.

## Mobile-First Global Rules
Applied globally across the app:
- **Base font:** `html { font-size: 16px }` — prevents iOS auto-zoom on input focus
- **Body:** `line-height: 1.5` — readability on small screens
- **All inputs/selects/textareas:** `font-size: 16px` — critical iOS auto-zoom prevention
- **Body:** `max-width:100vw; overflow-x:hidden; padding-bottom:120px`
- **Container:** `display:flex; flex-direction:column; gap:16px` — single-column mobile layout
- **Nord color theme** applied to `:root` vars:
  - `--bg: #2e3440`, `--card: #3b4252`, `--card2: #434c5e`
  - `--text: #d8dee9`, `--border: #4c566a`, `--input-bg: #2e3440`
  - Orange accents (`--orange`, `--orange2`) preserved for emphasis
- **Touch targets:** standalone buttons (`add-cat-btn`, `fetch-btn`, `ebtn`, `about-close`) have `min-height:48px`

## Renovation Row Standards (Mobile-First)
All table rows and toggle buttons must follow these standards:

### Toggle Button (Yes/No)
- `min-height: 48px`, `min-width: 90px` — tap-safe for iPhone
- **Yes (active):** `background: #88c0d0` (Frost Blue), `color: #2e3440` (bold/800)
- **No (inactive):** `background: #4c566a` (Muted Grey), `color: #d8dee9`
- **Active press:** `transform: scale(0.95)` on `:active` — tactile feedback
- CSS classes: `.toggle-btn.yes` / `.toggle-btn.no`

### Row Columns
| Column | Rule |
|---|---|
| Col 1 — Description | `flex:1`, `overflow-wrap:break-word`, `padding-right:16px` gap before toggle |
| Col 2 — Toggle | Fixed `width:95px`, centered vertically |
| Col 3 — Cost/Total | Fixed `width:85px`, `text-align:right`, `font-family:'JetBrains Mono','Consolas',monospace` |

### Inactive State
- Off rows get CSS classes: `disabled row-muted`
- `tr.row-muted { opacity: 0.5 }` — entire row dims to 50%
- `tr.disabled td { color: #616e88 }` — text color before opacity

### Layout
- Min row height: `height: 60px` on `tbody tr` (excluding formula/cat-header/add rows)
- Body: `padding-bottom: 120px` — clears iOS home indicator + browser bars

## Architecture

### Core State
- `st[]` — array of row state objects: `{on, oM, oL, oT, k, notes, exp}`
- `customCats[]` — user-added categories
- `customByBuiltin{}` — custom rows added to built-in categories
- `permitsState[]` — 5 permit tracking entries (Roof, HVAC, Water Heater, Plumbing, Electrical)
- `miscOn` / `miscMin` / `miscMax` / `miscManual` / `miscManualRate` / `miscRate` — Miscellaneous toggle + mode: **Range** (min/max → midpoint, default 5–10%) or **Manual** (user types exact %, default 7.5%); `miscRate` is always derived by `syncMisc()` which must be called after changing any misc param
- `editDefaultsMode` — when true, param changes are saved to localStorage

### Key Functions
| Function | Purpose |
|---|---|
| `getP()` | Returns `{sqft, bed, bath}` from inputs |
| `fmt(v)` | Format number as `$1,234` |
| `pIn(i, name, val, w)` | Inline editable param input |
| `eP(i, name, v)` | Update param, re-render row formula panel only |
| `ePSel(i, name, v)` | Update param from dropdown, calls `build()` |
| `eF(i, f, v)` | User override for oM/oL/oT |
| `togOn(i)` | Toggle row on/off |
| `calc()` | Recalculate totals + `_gcBase` |
| `build()` | Full re-render of table |
| `loadState()` / `saveState()` | localStorage persistence |

### Row Object Shape
```js
{
  cat: 'CATEGORY',   // must match one of CATS
  item: 'Name',
  split: 0|1,        // 0=single total cT, 1=separate cM+cL
  on: true|false,    // default on/off (omit = true)
  gcExcl: true,      // excluded from GC markup (optional)
  dp: { ... },       // default params → becomes st[i].k
  cM/cL/cT: (p,k)=>Number,
  fM/fL/fT: (p,k,i)=>HTMLString,
  h: (p,k)=>String,  // hint shown under item name
  d: 'short desc',
  defNote: 'long help text with Hebrew'
}
```

### GC Markup Logic
- `_gcBase` = sum of all active rows where `gcExcl !== true`
- **Excluded from GC:** Appliances, Survey+Inspection, Insurance, Boots on the Ground
- GC Fee row = `_gcBase × rate` (default 15%)

## Categories (render order)
`EXTERIOR · TERMITE · PLUMBING · ELECTRICAL · HVAC · KITCHEN · BATHROOMS · PAINT · GARAGE · FENCE · WINDOWS · DEMOLITION · CONTINGENCY · GARDENING · INSURANCE · FLOORING · DOORS · APPLIANCES · GENERAL`

## Row Catalog

⚠️ **Current State (2026-03-30):** Most rows are OFF. Only enabled:
- **Survey + Inspection** (GENERAL)
- **Insurance** (GENERAL)
- **Boots on the Ground** (GENERAL — already OFF by design)
- **Miscellaneous** (via `miscOn=true`)
- **GC Fee** (OFF for now — add back if needed)

### DEMOLITION
| Item | split | Default | Key params |
|---|---|---|---|
| Dumpster / Waste Disposal | 0 | **OFF** | `tier` (0=light/1=standard/2=heavy), `dumpCost`=475, `dumpQty` (1–2), `freeTons`=2/dumpster, `totalTons` (3/7/10 by tier), `overRate`=63/ton |
| Demo Labor | 0 | **OFF** | `tier` (0=light/1=standard/2=heavy), `rate`=325/person/day, `crew` (2–4), `days` (1–3) |

### CONTINGENCY
| Item | split | Default | Key params |
|---|---|---|---|
| General Labor Allowance | 0 | **OFF** | `val` (-1=auto by sqft: <1k→$2,500 / 1k-1.5k→$4,500 / 1.5k+→$5,250 — 60% of budget) |
| Home Depot Materials Buffer | 0 | **OFF** | `val` (-1=auto by sqft: <1k→$1,500 / 1k-1.5k→$3,000 / 1.5k+→$3,500 — 40% of budget) |
| **Combined target** | — | — | <1k→$4,000 · 1k-1.5k→$7,500 · 1.5k+→$8,750 |

### GARDENING
| Item | split | Default | Key params |
|---|---|---|---|
| Initial Cleanup | 0 | **OFF** | `t`=750 (flat fee $500–$1,000) · includes mow/edge, trim, weed, mulch |

### INSURANCE (gcExcl)
| Item | split | Default | Key params |
|---|---|---|---|
| Vacant Property Insurance | 0 | **OFF** | `monthly`=475 ($450–$500 range midpoint), `setup`=250, `months`=1 (adjustable) |

### EXTERIOR
| Item | split | Default | Key params |
|---|---|---|---|
| Replacing a Tiled Roof | 1 | **OFF** | `r` ($/sqft=7), `lab` (fixed=2000) |
| Sealing a Metal Roof (GacoRoof) | 0 | **OFF** | `mode` (0=Full Restoration / 1=Targeted Sealing), `rfac`=1.15, `pailCost`=320, `cov`=250, `anc`=0.175, `labType` (0=per sqft / 1=hourly), `labRate`=2, `labHrRate`=65, `labHrs`=10, `subMode` (0=standalone / 1=part of project), `standalone`=400, `partOf`=200 |
| Gutter Installation | 0 | **OFF** | `stories` (1/2), `wastePct`=0.10, `contPct`=0.05, `miters`=4, `gutRate`=6.25/LF, `mitRate`=15, `dsRate1`=74 (1-story), `dsRate2`=125 (2-story), `splRate`=5 · baseLF=√sqft×2.6, downspouts=⌈baseLF/40⌉, elbows=3/downspout |
| Tree Removal | 0 | **OFF** | `trees`, `size` (0=small/1=med/2=large) |
| Driveway | 1 | **OFF** | `tier` (0=Patch & Seal / 1=Resurfacing / 2=Full Replace), `totalSqft`=500, `repairSqft`=45, `labRate`=12.50, `matFlat`=150 (T1 fixed), `resLabRate`=6.50 `resMatRate`=1.50 (T2), `repLabRate`=15 `repMatRate`=5.50 (T3), `wastePct`=0.10, `contPct`=0.05 · hint shows $/sqft + ARV impact (1.5×) |

### TERMITE
| Item | split | Default | Key params |
|---|---|---|---|
| Termite Treatment | 0 | **OFF** | `method` (0=Sentricon/1=Termidor), `tent` (bool — active infestation), `annual`=425 |

### PLUMBING
| Item | split | Default | Key params |
|---|---|---|---|
| Water Heater | 1 | **OFF** | `mat`, `lab` (fixed) |
| Plumbing Repipe | 0 | **OFF** | `fc` ($/point), `lc` ($/faucet), `df` (drywall factor), `dc` |
| Drain Line | 0 | **OFF** | `t` (flat fee) |

### ELECTRICAL
| Item | split | Default | Key params |
|---|---|---|---|
| Panel Upgrade | 0 | **OFF** | `t` (flat fee) |
| Panel Swap | 0 | **OFF** | `t` (flat fee) |
| AlumiConn | 0 | **OFF** | `t` (flat fee) |
| Outlets & Switches | 1 | **OFF** | `mat`, `lab` (fixed) |
| GFCI Breakers | 1 | **OFF** | `mat`, `lab` per breaker; count = f(bed+bath) |
| Light Fixtures | 1 | **OFF** | `mat`, `lab` per fixture; count = bed+bath+6 |
| Fans | 1 | **OFF** | `mat`, `lab` per fan; count = bed+1 |

### HVAC
| Item | split | Default | Key params |
|---|---|---|---|
| Central AC | 0 | **OFF** | `t1–t5` (size tiers by sqft) |
| Ductwork | 0 | **OFF** | `t` (flat fee) |

### KITCHEN / BATHROOMS
| Item | split | Default | Notes |
|---|---|---|---|
| Standard Kitchen | 0 | **OFF** | lump sum |
| Bath Fixtures | 1 | **OFF** | multiplied by `bath` count |
| Shower Stall (Stand-Up) | 1 | **OFF** | units, tile sqft, dark matter, glass, Delta valve |
| Bathtub | 1 | **OFF** | units, tile sqft, dark matter, curtain, Delta valve |

### PAINT
| Item | split | Default | Notes |
|---|---|---|---|
| Exterior Painting | 1 | **OFF** | includes pressure wash |
| Exterior Wash Only | 0 | **OFF** | ⚠️ disable if Exterior Painting is ON |
| Interior Painting | 1 | **OFF** | walls only (not ceiling/trim/doors) |
| Door Painting | 1 | **OFF** | per door |
| Baseboard Painting | 0 | **OFF** | flat fee |

### GARAGE / FENCE
| Item | split | Default | Key params |
|---|---|---|---|
| Garage Door | 0 | **OFF** | `type` (single/double) |
| Garage Door Opener | 1 | **OFF** | `mat`, `lab` |
| Dog-Ear Wood Fence | 0 | **OFF** | `lf` (linear feet), per-panel pricing |

### WINDOWS
| Item | split | Default | Key params |
|---|---|---|---|
| Window Replacement | 0 | **OFF** | `qtySingle` (-1=auto: bath, 0=none, N=manual), `qtyDouble` (-1=auto: bed+4, 0=none, N=manual), `frameType` (0=Block/1=Wood +$20/unit), `repairAmt`=100/unit · labor $150/opening |
| Mini Blinds | 0 | **OFF** | `qty` (0=none, independent), `mat`=40 (range $20–$59) · labor $10/unit hardcoded |
| Spring/Balance Replacement | 0 | **OFF** | `qty`=1 · $125/window flat (labor + parts — broken lift mechanism repair) |

### FLOORING / DOORS
| Item | split | Default | Key params |
|---|---|---|---|
| Flooring | 0 | **OFF** | `type` (0=carpet/1=LVP/2=tile — default tile) |
| Baseboard | 1 | **OFF** | `lfFac` × sqft |
| Interior Doors | 0 | **OFF** | `type` (prehung/slab), count = bed+bath |
| Exterior Doors | 0 | **OFF** | `type` (slab/prehung) |
| Bi-Fold Closet Doors | 0 | **OFF** | panel count |

### APPLIANCES (all gcExcl — owner-supplied)
| Item | split | Default | Notes |
|---|---|---|---|
| Appliance Set | 0 | **OFF** | flat $2,750 bundle |
| Refrigerator | 0 | **OFF** | $1,350 — use instead of Set |
| Stove / Range | 0 | **OFF** | $650 |
| Microwave | 0 | **OFF** | $700 |
| Dishwasher | 0 | **OFF** | $700 |

### GENERAL (all gcExcl)
| Item | split | Default | Notes |
|---|---|---|---|
| Survey + Inspection | 0 | ON | flat fee |
| Insurance | 0 | ON | default $0 — enter actual quote |
| Boots on the Ground | 0 | **OFF** | `mode` (per-visit/weekly/monthly) — NOT subject to GC markup |
| GC Fee | 0 | **OFF** | `rate`=15% applied to `_gcBase` |

## Permit Tracking (5 built-in)
`Roof` (15yr) · `HVAC` (12yr) · `Water Heater` (12yr) · `Plumbing` · `Electrical`
Manual date entry → auto status badge. City permits pulled live from Jacksonville EPICS API.

## localStorage Keys
| Key | Contents |
|---|---|
| `'brrrr-calc-defaults'` | Full state snapshot (st, customCats, permitsState) |
| `'brrrr-zoom'` | Zoom level index 0–8 (80%–120%) |
