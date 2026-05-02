# LankaGuide AI

> **AI-Powered Immersive Tourism Companion for Sri Lanka**
> Final-year research project — Gautham B.K (CS/2020/055), University of Kelaniya.

A mono-repo containing the full LankaGuide AI stack: a Django REST Framework
backend with a RAG pipeline, a Next.js 14 conversational web client, and the
deployment scripts that ship them to AWS. Built end-to-end against the Cursor
AI Development Plan in [`LankaGuide_AI_PRD.md`](./LankaGuide_AI_PRD.md).

---

## Repository Layout

```
final-research-project/
├── backend/              # Django REST Framework API + AI services
│   ├── apps/             # 8 feature apps (chat, itinerary, vision, sentiment, …)
│   ├── lankaguide/       # Django project (settings, urls, wsgi)
│   ├── data/             # Curated knowledge base (TXT/PDF) for RAG ingestion
│   ├── var/chroma/       # ChromaDB persistent store (gitignored)
│   ├── venv/             # Python virtual env (gitignored)
│   ├── manage.py
│   ├── requirements.txt
│   └── README.md         # Backend setup, MySQL switch, tests
│
├── frontend/             # Next.js 14 + Tailwind + manual shadcn primitives
│   ├── app/              # App-router pages: /chat, /explore, /itinerary
│   ├── components/       # Chat panel, itinerary wizard, explore grid, UI kit
│   ├── lib/              # Axios client, session token, Zustand store
│   ├── package.json
│   └── README.md         # Frontend setup
│
├── deploy/               # Production deployment (Ubuntu / EC2)
│   ├── install_backend.sh
│   ├── install_frontend.sh
│   ├── nginx.conf
│   └── README.md         # Bring-up sequence
│
├── LankaGuide_AI_PRD.md  # Single source of truth: requirements + plan
└── README.md             # ← you are here
```

## Tech Stack at a Glance

| Layer            | Choice                                                          |
| ---------------- | --------------------------------------------------------------- |
| Web framework    | Django 5.1 + Django REST Framework 3.17                         |
| Frontend         | Next.js 14 (App Router) + Tailwind + shadcn-style components    |
| Relational DB    | MySQL 8 (SQLite fallback for local dev)                         |
| Vector DB        | ChromaDB (persistent, on-disk)                                  |
| Cache            | Redis 7 (via `django-redis`)                                    |
| LLM              | Gemini API (`gemini-1.5-flash` / `pro`) with offline fallback   |
| Streaming        | Apache Kafka (sentiment → trends pipeline)                      |
| Sentiment model  | `cardiffnlp/twitter-roberta-base-sentiment` (Hugging Face)      |
| Vision backbone  | torchvision MobileNetV2 + placeholder landmark head             |
| Forecasting      | Facebook Prophet                                                |
| Hosting          | AWS EC2 + Nginx + Gunicorn + systemd                            |

## Quick Start

> Each tier has its own README with full instructions; this is the 5-second tour.

### 1) Backend

```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_database
python manage.py ingest_knowledge_base
python manage.py runserver 127.0.0.1:8000
```

### 2) Frontend (in a second terminal)

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev   # http://localhost:3000
```

### 3) Run all tests

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest apps -v
```

### 4) Deploy to EC2

```bash
# On the EC2 host
git clone https://github.com/your-org/lankaguide.git /tmp/repo
cd /tmp/repo
sudo bash deploy/install_backend.sh
sudo bash deploy/install_frontend.sh
sudo certbot --nginx -d lankaguide.lk -d www.lankaguide.lk \
     -m ops@lankaguide.lk --agree-tos --non-interactive
```

See [`deploy/README.md`](./deploy/README.md) for the full topology.

## What Works End-to-End

| Capability                                | Endpoint / Page                                  |
| ----------------------------------------- | ------------------------------------------------ |
| Anonymous-session chat (RAG over Chroma)  | `POST /api/v1/chat/message/` · `/chat`           |
| Day-by-day itinerary generation           | `POST /api/v1/itinerary/generate/` · `/itinerary`|
| Single-day regeneration                   | `PATCH /api/v1/itinerary/{id}/day/{n}/regenerate/`|
| Landmark identification (image upload)    | `POST /api/v1/vision/identify/`                  |
| Districts + attraction filters + search   | `GET /api/v1/attractions/?…` · `/explore`        |
| Attraction detail (SSR)                   | `GET /api/v1/attractions/{slug}/` · `/explore/{slug}` |
| Trending attractions                      | `GET /api/v1/trends/attractions/`                |
| Manual review ingestion                   | `POST /api/v1/trends/reviews/`                   |
| Kafka sentiment + trend workers           | `manage.py start_sentiment_worker` / `start_trend_aggregator` |

Without `GEMINI_API_KEY`, every AI endpoint degrades to a deterministic
offline fallback so the API contract is preserved end-to-end.

## License & Acknowledgement

Academic project — University of Kelaniya, Department of Industrial Management.
PRD content, architecture, and final implementation © 2026 Gautham B.K.
