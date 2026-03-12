# DT-QUEST — Digital Twin Quality Evaluation & Standardization Toolkit

Automated data quality assessment platform for Digital Twin datasets. Currently supports **ITS/V2X** (vehicular communication) with plans for **UAV** and other domains.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Node.js + Express |
| Frontend | React 18 + Vite 5 |
| Styling | TailwindCSS 3.4 |
| Charts | Recharts |
| File Parsing | PapaParse |
| Statistics | simple-statistics |

## Pipeline Steps

| Step | Description |
|------|-------------|
| 0 — Upload | CSV upload, column mapping, dataset presets |
| 1 — Range | 3GPP compliance validation per parameter |
| 2 — Consistency | Cross-parameter relationship verification |
| 3 — Constants | Detect hardcoded placeholder values |
| 4 — Completeness | NaN profiling per-vehicle, per-column |
| 5 — Units | Detect linear vs dBm scale mismatches |
| 6 — Clean/Export | Apply corrections, export cleaned CSV + quality report |
| Bonus — Path Loss | Measured vs 3GPP reference model comparison |

## Quick Start

### Backend

```bash
cd backend
npm install
npm run dev    # starts on port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # starts on port 3000
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
dt-quest/
├── backend/
│   ├── server.js          # Express API (all routes + validation logic)
│   ├── package.json
│   └── domains/           # (planned) domain plugin configs
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Main app with state management
│   │   ├── utils/api.js   # API client
│   │   └── components/    # React components for each pipeline step
│   ├── index.html
│   ├── vite.config.js
│   └── tailwind.config.js
├── AUDIT_REPORT.md         # Project audit findings
├── DT_QUEST_BUILD_PROMPTS.md  # Development roadmap
└── README.md
```

## License

Research use — IIT Hyderabad / TiHAN
