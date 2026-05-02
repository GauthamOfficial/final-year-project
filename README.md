# LankaGuide

> AI-powered travel companion for Sri Lanka. Plan trips, ask the local AI guide,
> translate on the fly, and explore every district with curated images and video.

LankaGuide is a SaaS-style web app that helps tourists discover, plan, and
navigate Sri Lanka in English, Sinhala, or Tamil. It pairs a Django REST API
backed by a 25-district knowledge base with a Next.js 14 client featuring
voice input, on-page translation, weather and drive-time widgets, a gallery of
curated photography and video, and downloadable PDF itineraries.

---

## Repository layout

```
final-research-project/
├── backend/              # Django REST API + Gemini RAG + Chroma vector store
│   ├── apps/             # accounts, attractions, chat, itinerary, vision, sentiment,
│   │                     # weather, routing, translation, alerts, analytics, core
│   ├── lankaguide/       # Django project (settings, urls, wsgi)
│   ├── data/knowledge/   # Curated knowledge base ingested into ChromaDB
│   ├── manage.py
│   ├── requirements.txt
│   └── README.md
│
├── frontend/             # Next.js 14 (App Router) + Tailwind
│   ├── app/              # Routes: /, /explore, /itinerary, /chat, /gallery, /admin, ...
│   ├── components/       # UI kit, marketing, voice, maps, weather, auth, admin
│   ├── lib/              # Axios + JWT auth + zustand stores
│   └── README.md
│
├── deploy/               # Production install scripts (Ubuntu / EC2)
└── README.md             # ← you are here
```

## Tech stack

| Layer            | Choice                                                          |
| ---------------- | --------------------------------------------------------------- |
| Web framework    | Django 5.1 + Django REST Framework 3.17                         |
| Frontend         | Next.js 14 App Router + Tailwind + shadcn-style components      |
| Auth             | JWT (SimpleJWT) + Google OAuth (id_token verification)          |
| Relational DB    | MySQL 8 (SQLite for dev)                                        |
| Vector DB        | ChromaDB (persistent, on-disk)                                  |
| Cache            | Redis 7 via `django-redis`                                      |
| LLM              | Gemini 2.5 Flash / Pro (chat + itinerary + translation)         |
| Voice            | Web Speech API (browser-native, all 3 languages)                |
| Maps             | Leaflet + OpenStreetMap                                         |
| Weather          | OpenWeatherMap (free tier)                                      |
| Drive-time       | Public OSRM with congestion heuristic                           |
| Streaming        | Apache Kafka (sentiment → trends pipeline)                      |
| Sentiment model  | `cardiffnlp/twitter-roberta-base-sentiment` (HuggingFace)       |
| Vision backbone  | torchvision MobileNetV2                                         |

## Quick start

> Each tier has its own README with full instructions. This is the 5-second tour.

### 1. Backend

```powershell
cd backend
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
Copy-Item .env.example .env   # fill in GEMINI_API_KEY, OPENWEATHER_API_KEY, GOOGLE_OAUTH_CLIENT_ID
python manage.py migrate
python manage.py seed_database
python manage.py fetch_wikimedia_images
python manage.py build_knowledge_corpus
python manage.py ingest_knowledge_base
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

### 2. Frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev   # http://localhost:3000
```

### 3. Run tests

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest apps -v
```

### 4. Deploy to EC2

```bash
git clone https://github.com/your-org/lankaguide.git /tmp/repo
cd /tmp/repo
sudo bash deploy/install_backend.sh
sudo bash deploy/install_frontend.sh
sudo certbot --nginx -d lankaguide.lk -d www.lankaguide.lk \
     -m ops@lankaguide.lk --agree-tos --non-interactive
```

## Feature summary

| Capability                                  | Endpoint / Page                                       |
| ------------------------------------------- | ----------------------------------------------------- |
| Email/password + Google sign-in             | `POST /api/v1/auth/{register,login,google}/` · `/login` |
| Account-bound chat history                  | `GET /api/v1/chat/sessions/` · `/account/history`     |
| RAG chat with no fallbacks (Gemini-only)    | `POST /api/v1/chat/message/` · `/chat`                |
| Day-by-day itinerary generation             | `POST /api/v1/itinerary/generate/` · `/itinerary`     |
| Itinerary PDF download                      | `GET /api/v1/itinerary/{id}/pdf/`                     |
| Voice input + text-to-speech (en/si/ta)     | Mic button on `/chat`                                 |
| On-page translation (en ↔ si ↔ ta)          | `POST /api/v1/translate/` · `/translate`              |
| Districts + attractions + filters + search  | `GET /api/v1/attractions/` · `/explore`               |
| Real Wikimedia photography per attraction   | `/explore/{slug}` · `/gallery/{district}`             |
| YouTube video embeds per district           | `/gallery/{district}`                                 |
| Live weather (OpenWeatherMap)               | `GET /api/v1/weather/?district_id=`                   |
| Drive-time ETA + congestion heuristic       | `GET /api/v1/routing/eta/?from=&to=`                  |
| Landmark identification (image upload)      | `POST /api/v1/vision/identify/`                       |
| Trending attractions                        | `GET /api/v1/trends/attractions/`                     |
| Admin dashboard (KPIs, CRUD, moderation)    | `/admin` (Next.js, RBAC-protected)                    |

## License

© 2026 LankaGuide. All rights reserved.
