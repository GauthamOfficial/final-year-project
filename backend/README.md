# LankaGuide AI — Backend (Django)

> AI-Powered Immersive Tourism Companion for Sri Lanka.
> Final-year research project — Gautham B.K (CS/2020/055), University of Kelaniya.

This is the **Django REST Framework backend** of the LankaGuide mono-repo.
The companion Next.js client lives at `../frontend/` and the production
deployment scripts at `../deploy/`. See the project root [`README.md`](../README.md)
and [`LankaGuide_AI_PRD.md`](../LankaGuide_AI_PRD.md) for the full picture.

---

## 1. Tech Stack (this slice)

| Layer | Choice |
|-------|--------|
| Web framework | Django 5.1 + Django REST Framework |
| Database | MySQL 8 (SQLite fallback for first-boot dev) |
| Vector DB | ChromaDB (persistent, on-disk) |
| Cache | Redis (via `django-redis`) |
| LLM | Gemini API (`gemini-1.5-flash` / `pro`) |
| Streaming | Apache Kafka (sentiment pipeline only) |
| Sentiment | `cardiffnlp/twitter-roberta-base-sentiment` (Hugging Face) |
| Forecasting | Facebook Prophet |

## 2. Project Layout

```
backend/
├── lankaguide/            # Django project (settings, urls, wsgi, asgi)
├── apps/
│   ├── core/              # Health/root endpoints, shared utilities
│   ├── attractions/       # Districts + attractions (Prompt 2A)
│   ├── chat/              # Conversational AI (Prompt 2B + 4A RAG)
│   ├── itinerary/         # Itinerary builder (Prompt 2C + 4B)
│   ├── vision/            # Landmark recognition (Prompt 4C)
│   ├── sentiment/         # Trend mining + Kafka workers (Prompt 6B)
│   ├── alerts/            # Health & safety alerts
│   └── analytics/         # Stakeholder dashboard
├── data/                  # Knowledge-base text/PDF source files
├── var/chroma/            # ChromaDB persistent store (gitignored)
├── manage.py
├── requirements.txt
├── requirements.lock.txt
├── pytest.ini
├── conftest.py
└── .env.example
```

Each feature app ships with `urls.py`, `models.py`, `views.py`, and
DRF serializers. RAGService, ItineraryService, and VisionService hold the
AI logic; sentiment workers run as `manage.py` commands.

## 3. First-Time Setup (Windows / PowerShell)

> **Run all commands from the `backend/` folder** (not the repo root).

```powershell
cd backend

# 1. Create the venv (Python 3.12 strongly recommended — torch/prophet wheels)
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Upgrade pip, then install PyTorch CPU and the rest
python -m pip install --upgrade pip setuptools wheel
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 3. Copy the env template and edit values you care about
Copy-Item .env.example .env
notepad .env

# 4. Apply migrations (uses SQLite fallback by default)
python manage.py migrate

# 5. Seed the curated district + attraction data (PRD §7.1)
python manage.py seed_database

# 6. Ingest the knowledge base into ChromaDB
python manage.py ingest_knowledge_base

# 7. Run the dev server
python manage.py runserver 0.0.0.0:8000
```

### Run the test suite

```powershell
python -m pytest apps -v
```

Visit:

- `http://127.0.0.1:8000/`           — API discovery root
- `http://127.0.0.1:8000/api/v1/ping/` — liveness ping
- `http://127.0.0.1:8000/healthz/`   — plain health-check (for load balancers)
- `http://127.0.0.1:8000/admin/`     — Django admin (`createsuperuser` first)

## 4. Switching to MySQL

1. Provision MySQL 8 locally or on AWS RDS.
2. Create the database + user:

   ```sql
   CREATE DATABASE lankaguide CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'lankaguide_user'@'%' IDENTIFIED BY 'strong-password';
   GRANT ALL ON lankaguide.* TO 'lankaguide_user'@'%';
   FLUSH PRIVILEGES;
   ```

3. Edit `.env`:

   ```env
   USE_SQLITE_FALLBACK=False
   DB_HOST=127.0.0.1
   DB_PASSWORD=strong-password
   ```

4. `python manage.py migrate` again.

> If `pip install mysqlclient` fails on your machine, install the prebuilt
> wheel for your Python version from PyPI or fall back to PyMySQL by adding
> `pymysql.install_as_MySQLdb()` to `manage.py`.

## 5. CORS

The Next.js client at `http://localhost:3000` is whitelisted by default via
`CORS_ALLOWED_ORIGINS`. Add additional origins in `.env` (comma-separated) when
you deploy a staging or production frontend.

## 6. Roadmap to Full PRD

Subsequent Cursor prompts (sequences 2 → 7 in the PRD Appendix) build on this
scaffold:

| Prompt | Adds |
|--------|------|
| 2A | `attractions` models, serializers, ViewSets, router |
| 2B | `chat` models + `/chat/message/` endpoint |
| 2C | `itinerary` models + `/itinerary/generate/` endpoint |
| 3A | `ingest_knowledge_base` management command (ChromaDB) |
| 3B | `seed_database` management command (25 districts) |
| 4A | `RAGService` (Gemini + ChromaDB + Redis cache) |
| 4B | `ItineraryService` (Gemini structured-JSON output) |
| 4C | `VisionService` (MobileNet landmark classifier) |
| 6B | Kafka sentiment + trend-aggregator workers |
| 7A | EC2 + Gunicorn + Nginx + certbot deployment |
