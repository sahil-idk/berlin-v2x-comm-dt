# DT-QUEST Project Audit Report

> Audit performed on 2026-02-11 by code review of all 26 project files.

---

## 1. PROJECT STRUCTURE

```
dt-quest/
├── backend/
│   ├── __pycache__/main.cpython-312.pyc
│   ├── main.py              (976 lines — FastAPI backend, NOT actively used)
│   ├── server.js             (1114 lines — Express backend, PRIMARY)
│   ├── package.json
│   ├── package-lock.json
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── package.json
    ├── package-lock.json
    ├── postcss.config.js
    ├── tailwind.config.js
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── main.jsx
        ├── index.css
        ├── utils/
        │   └── api.js
        └── components/
            ├── Sidebar.jsx
            ├── UploadStep.jsx
            ├── RangeCheck.jsx
            ├── ConsistencyCheck.jsx
            ├── ConstantCheck.jsx
            ├── CompletenessCheck.jsx
            ├── UnitCheck.jsx
            ├── CleanExport.jsx
            ├── PathLossPlot.jsx
            └── ReadinessGauge.jsx
```

### Tech Stack

| Layer | Framework | Key Dependencies |
|-------|----------|-----------------|
| **Backend (primary)** | Express 4.18 / Node.js | multer, papaparse, simple-statistics, uuid |
| **Backend (unused)** | FastAPI / Python | pandas, numpy, scipy, pydantic |
| **Frontend** | React 18 + Vite 5 | recharts, axios, react-dropzone, TailwindCSS 3.4 |

### Missing / Empty Files
- No `domains/` directory, no `config.yaml` files, no plugin registry
- No `SummaryCard`, `DataTable`, or `ChartWrapper` shared components
- No `.env` or configuration file for API URL (hardcoded to `localhost:8000`)
- No tests, no CI/CD config

---

## 2. BACKEND STATUS

### a) Server Entry Point — **EXISTS** ✅
[server.js](file:///c:/Users/sahil/Sumo/berlin_v2x/dt-quest/backend/server.js) — Express on port **8000**, CORS enabled (`*`), `express.json()` middleware. Well structured with helper functions.

### b) File Upload Route — **EXISTS** ✅
`POST /upload` via **multer** (memory storage). Parses CSV with **PapaParse** (`dynamicTyping: true`). Returns session ID, row/column counts, NaN counts, and 10-row preview. Parquet returns a 400 error ("convert to CSV").

### c) Domain Plugin System — **MISSING** ❌
No `domains/` directory. No registry, no auto-discovery, no `config.yaml` files. Parameter ranges and presets are hardcoded directly in `server.js` (lines 28-88).

### d) ITS/V2X Domain Plugin — **PARTIAL** ⚠️
The parameter bounds and presets exist but are **hardcoded constants**, not a plugin:
- `PARAMETER_RANGES`: 10 parameters with 3GPP bounds (SNR, RSRP, RSSI, noise, Tx, Rx, PL, distance, lat, lon)
- `PRESETS`: 3 presets — `tihan_v2i`, `berlin_sidelink`, `berlin_cellular` with column mappings

### e) Validation Pipeline Modules — All **EXISTS** ✅ (monolithic in server.js)

| Module | Endpoint | Status | Logic |
|--------|----------|--------|-------|
| **Range check** | `POST /pipeline/step1/:id` | ✅ | Checks each mapped param against 3GPP bounds, calculates compliance %, detects systematic errors (<5%), computes histograms |
| **Consistency check** | `POST /pipeline/step2/:id` | ✅ | Dual-mode (dBm vs linear): derives SNR from Rx-Noise, Pearson correlation, % within ±3dB, verdict scoring |
| **Constant check** | `POST /pipeline/step3/:id` | ✅ | Finds mode value per column, flags ≥95% identical as placeholder |
| **Completeness check** | `POST /pipeline/step4/:id` | ✅ | Per-column NaN rates, per-vehicle completeness, heatmap data (top 20 vehicles), completeness gap |
| **Unit check** | `POST /pipeline/step5/:id` | ✅ | Detects linear vs dBm scale for power params, PL consistency check (Tx-Rx vs measured PL) |
| **Corrections** | `POST /pipeline/step6/:id` | ✅ | 5 corrections: offset subtraction, unit conversion, completeness flags, column filtering, outlier flagging (z>3) |
| **Report generator** | `GET /export/report/:id` | ✅ | Returns JSON with all pipeline results + readiness score + corrections |

> **Note:** All modules live in a single `server.js` file — no separate modules or files per check.

### f) Export Routes — **EXISTS** ✅
- `GET /export/csv/:sessionId` — serves cleaned CSV via PapaParse unparse
- `GET /export/report/:sessionId` — serves JSON quality report

### g) Statistics Utilities — **EXISTS** ✅
- Pearson correlation: custom implementation (lines 133-151)
- Histogram: custom implementation (lines 108-130)
- Mean, std dev, median, quantile: via `simple-statistics` library
- Z-score: computed manually in outlier flagging (line 838)

### h) Session/Data Storage — **EXISTS** ⚠️
In-memory JavaScript object (`const datasets = {}`). Data persists only while the server process is running. No database, no file-based persistence. Session ID format: `session_{timestamp}_{uuid4_prefix}`.

---

## 3. FRONTEND STATUS

### a) App Layout — **EXISTS** ✅
[App.jsx](file:///c:/Users/sahil/Sumo/berlin_v2x/dt-quest/frontend/src/App.jsx) — Fixed header (64px) + left sidebar (256px) + main content area. Dark theme via TailwindCSS custom colors (`dt-dark: #0f0f1a`, `dt-card: #1a1a2e`). Inter font from Google Fonts.

### b) Pipeline Context/State — **PARTIAL** ⚠️
State is managed via `useState` hooks directly in `App.jsx` — **no Context API, no Redux, no Zustand**. State includes: `currentStep`, `sessionId`, `datasetInfo`, `mapping`, `pipelineResults`, `readinessScore`, `completedSteps`, `showPathLoss`. Props are drilled down to each component.

### c) Sidebar — **EXISTS** ✅
[Sidebar.jsx](file:///c:/Users/sahil/Sumo/berlin_v2x/dt-quest/frontend/src/components/Sidebar.jsx) — 7-step stepper with emoji icons, completion indicators (✓), glow animation on current step, step locking via `canAccessStep()`, Path Loss bonus tab, ReadinessGauge at bottom. **No domain selector**.

### d) Step 0 (Upload) — **EXISTS** ✅
[UploadStep.jsx](file:///c:/Users/sahil/Sumo/berlin_v2x/dt-quest/frontend/src/components/UploadStep.jsx) — Drag-drop zone (react-dropzone), file stats (4 summary cards: filename, rows, columns, size), 10-row data preview table, 3 preset buttons (TiHAN V2I, Berlin Sidelink, Berlin Cellular), full column mapping with dropdowns for all 12 parameters, validation requiring SNR/RSRP + Rx Power + Distance + GPS before proceeding.

### e) Step 1 (Range) — **EXISTS** ✅
[RangeCheck.jsx](file:///c:/Users/sahil/Sumo/berlin_v2x/dt-quest/frontend/src/components/RangeCheck.jsx) — 3 summary cards (pass/outliers/systematic), horizontal bar chart (Recharts) with 95% and 5% reference lines, expandable parameter detail panels with actual range/mean/std, systematic offset warnings. **No distribution histograms per parameter** — histogram data exists in the backend response but is not rendered.

### f) Step 2 (Consistency) — **EXISTS** ✅
[ConsistencyCheck.jsx](file:///c:/Users/sahil/Sumo/berlin_v2x/dt-quest/frontend/src/components/ConsistencyCheck.jsx) — Verdict card (color-coded by dBm_confirmed/linear_detected/inconclusive), dual scatter plots (Mode A vs Mode B) with y=x reference line, correlation + ±3dB stats, residual histogram (Mode A only), skipped-state handling.

### g) Step 3 (Constants) — **EXISTS** ✅
[ConstantCheck.jsx](file:///c:/Users/sahil/Sumo/berlin_v2x/dt-quest/frontend/src/components/ConstantCheck.jsx) — 3 summary cards, full results table (column, mode value, mode %, unique count, status badge), mode % progress bars, placeholder detection warning banner. **No flat-line charts** — data is presented in tabular form.

### h) Step 4 (Completeness) — **EXISTS** ✅
[CompletenessCheck.jsx](file:///c:/Users/sahil/Sumo/berlin_v2x/dt-quest/frontend/src/components/CompletenessCheck.jsx) — Insight banner, 4 summary cards (records, avg completeness, gap, >50% missing), per-column bar chart, per-vehicle bar chart (top 20), HTML-based heatmap (Vehicle × Column, colored by NaN %). **No missingness correlation display** — data exists in the backend response (`missingness_correlation` from Python version) but the Node.js backend doesn't compute it and the frontend doesn't render it.

### i) Step 5 (Units) — **EXISTS** ✅
[UnitCheck.jsx](file:///c:/Users/sahil/Sumo/berlin_v2x/dt-quest/frontend/src/components/UnitCheck.jsx) — Scale indicator cards per power param (icon + scale badge + min/max/mean + mini histogram), PL consistency scatter plot (Tx-Rx vs measured PL with correlation), linear scale warning banner.

### j) Step 6 (Clean/Export) — **EXISTS** ✅
[CleanExport.jsx](file:///c:/Users/sahil/Sumo/berlin_v2x/dt-quest/frontend/src/components/CleanExport.jsx) — 5 correction toggle checkboxes (offset subtraction, unit conversion, completeness flags, column filtering, outlier flagging), context-aware disabling (offsets disabled if none detected, unit conversion disabled if no linear), applied corrections result panel (original/cleaned shape, per-correction detail), CSV download button (opens in new tab), JSON report download (Blob URL), DT-Readiness gauge panel with 5-component breakdown bars, Key Findings panel. **No before/after previews**.

### k) Path Loss Tab — **EXISTS** ✅
[PathLossPlot.jsx](file:///c:/Users/sahil/Sumo/berlin_v2x/dt-quest/frontend/src/components/PathLossPlot.jsx) — ComposedChart with measured scatter + binned median line + 3 reference models (FSPL, 3GPP LOS, 3GPP NLOS), 4 MAE summary cards (best fit, FSPL MAE, LOS MAE, NLOS MAE), model equation reference panel. Accessible via sidebar bonus tab.

### l) Shared Components

| Component | Status | Notes |
|-----------|--------|-------|
| **ReadinessGauge** | ✅ EXISTS | SVG circular gauge with animated arc, color-coded (green/yellow/red), shows score/100 + status text |
| **SummaryCard** | ❌ MISSING | Each component builds its own card markup inline |
| **DataTable** | ❌ MISSING | Tables built inline in each component |
| **ChartWrapper** | ❌ MISSING | Recharts used directly in each component |

---

## 4. API INTEGRATION

### Backend Endpoints (Node.js `server.js`)

| Method | Route | Purpose |
|--------|-------|---------|
| GET | `/` | Health check |
| GET | `/presets` | Get column mapping presets |
| GET | `/parameter-ranges` | Get 3GPP parameter bounds |
| POST | `/upload` | Upload CSV file |
| POST | `/mapping/:sessionId` | Set column mapping |
| POST | `/pipeline/step1/:sessionId` | Range validation |
| POST | `/pipeline/step2/:sessionId` | Consistency check |
| POST | `/pipeline/step3/:sessionId` | Constant screening |
| POST | `/pipeline/step4/:sessionId` | Completeness profiling |
| POST | `/pipeline/step5/:sessionId` | Unit verification |
| POST | `/pipeline/step6/:sessionId` | Apply corrections |
| GET | `/export/csv/:sessionId` | Download cleaned CSV |
| GET | `/export/report/:sessionId` | Download quality report |
| GET | `/path-loss-analysis/:sessionId` | Path loss vs 3GPP models |

### Frontend → Backend Integration

| Frontend Component | API Call | Real Data? |
|-------------------|----------|------------|
| UploadStep | `uploadDataset()`, `getPresets()`, `setColumnMapping()` | ✅ Yes |
| RangeCheck | `runStep1()` | ✅ Yes |
| ConsistencyCheck | `runStep2()` | ✅ Yes |
| ConstantCheck | `runStep3()` | ✅ Yes |
| CompletenessCheck | `runStep4()` | ✅ Yes |
| UnitCheck | `runStep5()` | ✅ Yes |
| CleanExport | `applyCorrections()`, `exportCsv()`, `getQualityReport()` | ✅ Yes |
| PathLossPlot | `getPathLossAnalysis()` | ✅ Yes |
| ReadinessGauge | Receives `score` props from `getReadinessScore()` | ✅ Yes |

### Disconnected Components
- **`GET /pipeline/readiness/:sessionId`** exists in the Node.js backend but the `api.js` calls it and `App.jsx` uses it — **connected** ✅
- The **Python `main.py`** backend is a complete duplicate that is NOT connected to the frontend (frontend hardcoded to port 8000, and `main.py` also runs on 8000 — they cannot coexist)
- The Vite proxy at `/api` is configured but `api.js` uses direct `http://localhost:8000` URLs, so the proxy is **unused**

---

## 5. FUNCTIONALITY TEST (Code Review)

| Capability | Works? | Notes |
|------------|--------|-------|
| **Upload CSV and see it parsed** | ✅ Yes | PapaParse with `dynamicTyping: true`, returns preview + NaN counts + columns |
| **Column mapping** | ✅ Yes | Presets auto-fill, manual dropdowns, validation before proceeding |
| **Range validation produces real results** | ✅ Yes | `getNumericColumn()` handles type coercion, compliance rates, histograms |
| **Consistency produces real results** | ✅ Yes | Mode A/B with correlation and ±3dB analysis |
| **Constants produces real results** | ✅ Yes | Mode % detection with 95% threshold |
| **Completeness produces real results** | ✅ Yes | Per-column and per-vehicle NaN profiling |
| **Units produces real results** | ✅ Yes | Scale detection heuristics + PL consistency |
| **Corrections can be applied** | ✅ Yes | Offset subtraction, unit conversion, flagging all functional |
| **Cleaned CSV exported** | ✅ Yes | PapaParse `unparse()` served as download |
| **DT-Readiness score computes** | ✅ Yes | Weighted average of 5 components (range 25%, consistency 25%, constants 15%, completeness 25%, units 10%) |

> **Overall:** The end-to-end flow from upload → mapping → 5 validations → corrections → export is **fully wired** and should work with real data, pending `npm install` and server start.

---

## 6. SUMMARY TABLE

| Component | Status | Completeness | Notes |
|-----------|--------|-------------|-------|
| Project scaffolding | ✅ | 85% | Frontend + backend both scaffolded; no tests, no Docker, no env config |
| Express server | ✅ | 95% | Port 8000, CORS, multer, all routes registered; all in one file |
| Domain registry | ❌ | 0% | No plugin system; ranges/presets hardcoded in server.js |
| ITS/V2X plugin | ⚠️ | 40% | Presets and ranges exist as constants, not as a pluggable config.yaml |
| UAV plugin | ❌ | 0% | Does not exist |
| Step 0 – Upload | ✅ | 95% | Drag-drop, CSV parsing, presets, column mapping, validation |
| Step 1 – Range | ✅ | 85% | Compliance bar chart, summary cards, systematic offsets; missing per-param histograms in frontend |
| Step 2 – Consistency | ✅ | 90% | Mode A/B scatter, verdict card, residual histogram; well implemented |
| Step 3 – Constants | ✅ | 80% | Status table, mode % bars, warnings; no flat-line time-series charts |
| Step 4 – Completeness | ✅ | 80% | Column/vehicle bars, heatmap; missing missingness correlation matrix display |
| Step 5 – Units | ✅ | 90% | Scale indicators, mini histograms, PL scatter; complete |
| Step 6 – Clean/Export | ✅ | 85% | 5 correction toggles, CSV + report download, readiness gauge; no before/after data previews |
| Path Loss tab | ✅ | 90% | Scatter + 3 model curves + binned median, MAE cards, model equations |
| ReadinessGauge | ✅ | 95% | Animated SVG arc gauge, 3-tier coloring, score + status label |
| API integration | ✅ | 95% | All frontend steps call real backend; no mock data anywhere |
| End-to-end flow | ✅ | 85% | Full pipeline wired; in-memory storage means data lost on restart; dual backends (Python unused) |

---

## Key Gaps for Next Steps

1. **Domain plugin system** — The entire `domains/` directory, registry pattern, and `config.yaml` files are missing. Ranges and presets are hardcoded.
2. **UAV domain** — No additional domain support beyond ITS/V2X.
3. **Before/after data previews** in Step 6 — User cannot visually compare pre- vs post-correction data.
4. **Per-parameter distribution histograms** in Step 1 — Backend computes them, frontend doesn't render.
5. **Missingness correlation matrix** in Step 4 — Python backend computes it, Node.js doesn't.
6. **Persistent storage** — In-memory only; sessions lost on server restart.
7. **Shared components** (`SummaryCard`, `DataTable`, `ChartWrapper`) — Not extracted; duplicated inline across components.
8. **Python backend cleanup** — `main.py` is a complete duplicate that is unused and may cause confusion.
9. **Vite proxy mismatch** — Proxy configured at `/api` but `api.js` calls `http://localhost:8000` directly.
10. **No tests** — Zero unit, integration, or E2E tests.
