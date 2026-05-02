# LankaGuide — Django REST API

AI-assisted tourism backend for Sri Lanka: JWT authentication, Gemini RAG over ChromaDB, itineraries, weather (OpenWeatherMap), OSRM drive-time estimates, translation, and operator APIs for the Next.js admin console.

The Next.js app lives in [`../frontend/`](../frontend/). Deployment helpers are under [`../deploy/`](../deploy/).

## Stack

| Layer | Choice |
|-------|--------|
| Framework | Django 5 + Django REST Framework |
| Auth | SimpleJWT + Google ID token verification |
| Database | MySQL 8 (SQLite optional for local dev) |
| Cache | Redis (`django-redis`) |
| Vector | ChromaDB (persistent) |
| LLM | Google Gemini (chat, itinerary JSON, embeddings, translation) |

## Local setup (PowerShell)

```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
Copy-Item .env.example .env
# Set GEMINI_API_KEY, OPENWEATHER_API_KEY, Redis, optional Google OAuth, SMTP for password reset.
python manage.py migrate
python manage.py seed_database
python manage.py fetch_wikimedia_images
python manage.py build_knowledge_corpus
python manage.py ingest_knowledge_base
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

### Tests

```powershell
python -m pytest apps -v
```

### Useful URLs

- `http://127.0.0.1:8000/` — API root
- `http://127.0.0.1:8000/api/v1/ping/` — health
- `http://127.0.0.1:8000/healthz/` — load-balancer probe
- `http://127.0.0.1:8000/admin/` — Django admin

## Environment

See [`.env.example`](.env.example). Important variables:

- `GEMINI_API_KEY` — required for chat, itinerary, RAG, translation
- `JWT_SIGNING_KEY` — optional; defaults to `DJANGO_SECRET_KEY`
- `OPENWEATHER_API_KEY` — weather widget (503 if missing)
- `GOOGLE_OAUTH_CLIENT_ID` — validates Google sign-in tokens
- `EMAIL_BACKEND` / `DEFAULT_FROM_EMAIL` — password reset emails (console backend logs to stdout by default)
- `FRONTEND_URL` — links inside reset emails

## MySQL

Set `USE_SQLITE_FALLBACK=False` and provide `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`. Run `migrate` again.

## CORS

Add production origins to `CORS_ALLOWED_ORIGINS` in `.env` (comma-separated).
