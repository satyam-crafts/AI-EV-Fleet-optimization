# AI EV Fleet Optimization

**From Fleet Data to Intelligent Energy Decisions**

---

## What this project is for

Commercial electric fleets need answers every day:

- Which vehicle should take which delivery route?
- Does that vehicle have enough battery (SOC) to finish safely?
- When and where should it charge?
- How do we avoid expensive peak electricity rates?

**AI EV Fleet Optimization** is a full-stack demo that turns fleet telemetry into clear operational decisions: vehicle–route assignment, charging schedules, cost estimates, and plain-English recommendations.

```text
Fleet → Battery → Route → Charging → Cost → Optimization → Recommendation
```

---

## Aim of the project

| Goal | What it means in practice |
|------|---------------------------|
| **Cut charging cost** | Shift charging into cheaper Time-of-Use (TOU) windows instead of plugging in at peak. |
| **Keep routes feasible** | Only assign vehicles that can complete a route within battery and schedule limits. |
| **Protect batteries** | Enforce a hard minimum SOC safety floor (demo default: 15%). |
| **Explain decisions** | Show *why* a vehicle or charge window was chosen — not just a black-box score. |
| **Stay trustworthy** | Math and constraints come from a **deterministic engine**. AI only explains and answers questions; it does not invent feasibility or prices. |

In the included demo scenario, smart load-shifting can reduce charging cost by roughly **~65%** vs. unmanaged peak charging.

---

## Who it’s for

- **Fleet operators / dispatchers** exploring smarter EV energy decisions  
- **Judges & reviewers** evaluating an end-to-end energy + optimization demo  
- **Developers** learning how UI + API + optimization + explainability fit together  

---

## What you get

- **Fleet dashboard** — KPIs, SOC, availability, attention flags  
- **Vehicles & routes** — status, range, assignments, feasibility  
- **Charging** — stations, power, planned sessions, load-shift insight  
- **Analytics** — baseline vs optimized cost, energy impact  
- **Optimization workspace** — run the engine, inspect assignments & plans  
- **AI Fleet Copilot** — ask questions about the fleet; works without an LLM API key (template mode)

---

## How it works (high level)

```text
React dashboard  →  FastAPI REST API  →  Deterministic optimization engine
                                              ↓
                                    Recommendations + AI explanations
```

1. Load demo fleet data (vehicles, routes, chargers, energy prices).  
2. Run optimization — assign vehicles, schedule charging, compute cost.  
3. Review results in the UI or ask the copilot to explain them.

**Stack:** Python / FastAPI · React / TypeScript / Vite · Recharts · Docker-ready  

---

## Important design principle

> **Deterministic code is the source of truth.**  
> Battery limits, route energy, charger availability, and cost calculations are computed by the optimization engine.  
> The AI layer may summarize and chat — it must not override those results.

---

## Quick start

### Local (API + UI)

**Backend** (from repo root, Python 3.11+):

```bash
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd ..
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend** (Node 20+):

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173  
- API docs: http://localhost:8000/docs  

### Docker (UI + API on one port)

```bash
docker build -t ai-ev-fleet .
docker run --rm -p 8000:8000 ai-ev-fleet
```

Open http://localhost:8000  

---

## Main API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/fleet` | Fleet overview & KPIs |
| GET | `/api/v1/vehicles` | Vehicles & battery state |
| GET | `/api/v1/routes` | Routes |
| GET | `/api/v1/charging-stations` | Charging infrastructure |
| GET | `/api/v1/energy-prices` | TOU energy prices |
| POST | `/api/v1/optimize` | Run optimization |
| GET | `/api/v1/recommendations` | Explainable recommendations |
| POST | `/api/v1/agent/query` | Ask the Fleet Copilot |
| POST | `/api/v1/demo/reset` | Reset demo data |

---

## Repository layout

```text
backend/     Domain models, calculations, optimizer, agent, REST API
frontend/    Operations dashboard (React)
data/        Sample reference fixtures
Dockerfile   Production-style single-service build
```

---

## Configuration

Optional settings live in `.env` (see `.env.example`):

- `LLM_PROVIDER=template` — works offline with no API key  
- Optional OpenAI / other keys for richer natural-language answers  
- Fleet defaults: min SOC buffer, max SOC target, charging efficiency  

Do not commit secrets.

---

## Status

Implemented: demo fleet data, deterministic heuristic optimizer, recommendations, API, dashboard, AI copilot (template fallback), Docker packaging.

Not the focus of this demo: production auth, database persistence, or a full MILP solver (the engine is a documented heuristic that can be swapped later).
