# AI EV Fleet Optimization

**From Fleet Data to Intelligent Energy Decisions**

Full-stack demo for EV fleet operators: vehicle assignment, route feasibility, battery/SOC constraints, TOU-aware charging schedules, cost optimization, and explainable recommendations.

```text
Fleet → Battery → Route → Charging → Cost → Optimization → Recommendation
```

Deterministic optimization is the source of truth. The AI layer explains verified results and answers operator questions — it does not invent feasibility, costs, or constraints.

---

## For judges & reviewers

### Important about `localhost`

Links like `http://localhost:5173` or `http://localhost:8000` **only work on the computer that is running the app**.  
They **cannot** be opened by judges from a GitHub README on another machine.

To let anyone open the project in a browser, you need a **public Live Demo URL** (hosted online). See [Deploy the Live Demo](#deploy-the-live-demo-public-url) below.

| What judges need | What to put in the README |
|------------------|---------------------------|
| Instant view from anywhere | Public Live Demo URL (Render / similar) |
| Run on their own laptop | Steps below → then open **their** localhost |

### Live Demo

> **Live Demo:** _Deploy once using the steps below, then paste your public URL here, e.g._  
> `https://ai-ev-fleet-optimization.onrender.com`

After deploy, judges open **that one link** — dashboard + API on the same site.

### Option A — Run locally (2 terminals)

**Prerequisites:** Python 3.11+, Node.js 20+

```bash
# Terminal 1 — API (from repository root)
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd ..
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
# Terminal 2 — UI
cd frontend
npm install
npm run dev
```

Then open on **that same machine**:

- Dashboard: http://localhost:5173  
- API docs: http://localhost:8000/docs  

### Option B — One command with Docker (single URL)

```bash
docker build -t ai-ev-fleet .
docker run --rm -p 8000:8000 ai-ev-fleet
```

Open http://localhost:8000 — UI and API together.

---

## Deploy the Live Demo (public URL)

The app is packaged so **one Docker service** serves the React dashboard and the FastAPI API.

### Deploy on Render (free tier)

1. Push this repo to GitHub (already done if you cloned from here).
2. Open [Render](https://render.com) → **New** → **Blueprint**.
3. Connect the GitHub repo `AI-EV-Fleet-optimization`.
4. Render reads `render.yaml` and builds the `Dockerfile`.
5. When the service is live, copy the URL (example: `https://ai-ev-fleet-optimization.onrender.com`).
6. Paste that URL into the **Live Demo** section above and push again.

Free Render services may sleep after idle time; the first open can take ~30–60 seconds to wake.

---

## Architecture

```text
React (Vite)  →  FastAPI REST  →  FleetService  →  Agent Orchestrator
                                                      ↓
                                         Deterministic Heuristic Engine
                                                      ↓
                                         Domain models + calculations
                                                      ↓
                                         In-memory demo seed data
```

| Layer | Location |
|--------|----------|
| Frontend dashboard | `frontend/` |
| REST API | `backend/app/api/v1/` |
| Services | `backend/app/services/` |
| Agent / tools | `backend/app/agents/` |
| Optimization engine | `backend/app/domain/optimization/` |
| Calculations | `backend/app/domain/calculations/` |
| Sample fixtures (reference) | `data/samples/` |
| Production container | `Dockerfile`, `render.yaml` |

Runtime demo data is seeded from `backend/app/data/sample_data.py`. JSON files under `data/samples/` are reference fixtures and are not loaded by the API today.

---

## Prerequisites

- **Python** 3.11+
- **Node.js** 20+ (npm)
- Optional: OpenAI API key for richer natural-language answers (template mode works without a key)
- Optional: Docker (for single-URL local/prod runs)

---

## Quick start (development)

### 1. Backend

```bash
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
pip install -e ".[dev]"
```

Copy environment defaults from the repo root:

```bash
# from repo root
cp .env.example .env
```

Run the API from the **repository root** (so `backend.app` imports resolve):

```bash
# Windows (PowerShell)
.\backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# macOS / Linux
./backend/.venv/bin/python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

- API docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173 — Vite proxies `/api` and `/health` to the backend on port 8000.

### 3. Single-process mode (built UI + API)

```bash
cd frontend && npm run build && cd ..
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000

---

## Main API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/api/v1/fleet` | Fleet KPIs |
| GET | `/api/v1/vehicles` | Vehicles |
| GET | `/api/v1/routes` | Routes |
| GET | `/api/v1/charging-stations` | Stations |
| GET | `/api/v1/energy-prices` | TOU schedule |
| POST | `/api/v1/optimize` | Run optimization |
| GET | `/api/v1/optimization/latest` | Latest result |
| GET | `/api/v1/recommendations` | Active recommendations |
| POST | `/api/v1/agent/query` | Operator Q&A |
| POST | `/api/v1/demo/reset` | Reseed demo + re-optimize |

---

## Optimization note

The engine is a **deterministic multi-objective heuristic** (vehicle–route scoring, port occupancy, TOU load shifting). It is not a MILP solver. Methodology is documented in `backend/app/domain/optimization/optimizer.py`.

---

## Tests

```bash
# Backend (from backend/, venv active; run from repo root recommended)
python -m pytest backend/tests

# Frontend
cd frontend
npm test      # Vitest (add tests under src/)
npm run build
```

---

## Configuration

See `.env.example`:

- `LLM_PROVIDER=template` — works offline without keys
- Optional: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`
- Fleet defaults: SOC buffers, charging efficiency, `OPTIMIZATION_SOLVER=heuristic`

Never commit a real `.env` file.

---

## Project status

- Backend domain, calculations, heuristic optimizer, explainability, agent, and REST API are implemented and covered by pytest.
- Frontend operations dashboard (Fleet, Routes, Charging, Analytics, Optimization, AI assistant) is implemented.
- Docker + Render blueprint included for a public Live Demo URL.
- Not yet included: durable database, authentication, formal MILP solver, CI workflows.
