# AI EV Fleet Optimization

**From Fleet Data to Intelligent Energy Decisions**

Full-stack demo for EV fleet operators: vehicle assignment, route feasibility, battery/SOC constraints, TOU-aware charging schedules, cost optimization, and explainable recommendations.

```text
Fleet → Battery → Route → Charging → Cost → Optimization → Recommendation
```

Deterministic optimization is the source of truth. The AI layer explains verified results and answers operator questions — it does not invent feasibility, costs, or constraints.

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

Runtime demo data is seeded from `backend/app/data/sample_data.py`. JSON files under `data/samples/` are reference fixtures and are not loaded by the API today.

---

## Prerequisites

- **Python** 3.11+
- **Node.js** 20+ (npm)
- Optional: OpenAI API key for richer natural-language answers (template mode works without a key)

---

## Quick start

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
# Windows (PowerShell), venv active
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
# Backend (from backend/, venv active)
pytest

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
- Not yet included: Docker/CI, durable database, authentication, formal MILP solver.
