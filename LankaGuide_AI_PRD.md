# Product Requirements Document
## AI-Powered Immersive Tourism Companion for Sri Lanka

**Prepared by:** Gautham B.K
**Registration:** CS/2020/055
**Supervisor:** Ms. R.M.S.L. Rathnayake
**Faculty:** Faculty of Computing and Technology, University of Kelaniya
**Date:** August 2025
**Version:** 1.0 — Confidential — For Academic Submission Only

---

### Tech Stack Summary

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js (latest) + Shadcn UI |
| Backend | Django REST Framework |
| Database | MySQL |
| Vector DB | ChromaDB |
| LLM | Gemini API (gemini-1.5-pro/flash) |
| Streaming | Apache Kafka (selective use) |
| Deployment | AWS EC2 (bare-metal, no Docker) |

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Insights from Literature Review](#2-insights-from-literature-review)
3. [Product Strategy](#3-product-strategy)
4. [Feature Breakdown](#4-feature-breakdown)
5. [User Flows](#5-user-flows)
6. [System Architecture](#6-system-architecture)
7. [Database Design](#7-database-design-mysql)
8. [API Design](#8-api-design)
9. [AI / RAG Pipeline](#9-ai--rag-pipeline-detailed)
10. [Real-Time Streaming](#10-real-time-streaming-apache-kafka)
11. [UI/UX Guidelines](#11-uiux-guidelines)
12. [Development Roadmap](#12-development-roadmap)
13. [Deployment Plan](#13-deployment-plan-aws-ec2-no-docker)
14. [Risks & Challenges](#14-risks--challenges)
- [Appendix: Cursor AI Development Plan](#appendix-cursor-ai-development-plan)

---

## 1. Product Overview

### 1.1 Problem Statement

Sri Lanka's tourism sector is one of the country's primary economic engines, contributing significantly to foreign exchange earnings and employment. Yet, the digital infrastructure supporting tourists remains largely fragmented and primitive. While destinations like Japan, Singapore, and Dubai deploy AI-powered chatbots, smart itinerary engines, and real-time translation, Sri Lanka's tourism apps are overwhelmingly static — confined to hotel bookings and generic travel guides.

Tourists arriving in Sri Lanka lack access to a unified, intelligent companion that can answer contextual questions about local culture, generate dynamic itineraries based on individual preferences, assist in real-time translation, surface trending attractions from social media, and deliver cinematographic multimedia experiences. This gap translates directly into reduced visitor satisfaction and a weakened competitive position in the global tourism market.

The absence of such a system means Sri Lanka risks leaving economic value on the table — fewer repeat visitors, missed opportunities to surface hidden gems, and no mechanism for aggregating visitor feedback to benefit local stakeholders.

### 1.2 Target Users

| User Segment | Description | Primary Need |
|---|---|---|
| International Tourists | First-time and repeat visitors from abroad | Personalized itineraries, real-time translation, cultural context |
| Domestic Travelers | Sri Lankan citizens exploring their own country | Curated local experiences, budget planning, off-the-beaten-path suggestions |
| Solo Backpackers | Budget-conscious independent travelers | Safety tips, cost optimization, community reviews |
| Group & Family Tourists | Families or groups with varied preferences | Consensus itinerary planning, family-friendly filtering |
| Travel Agencies | Local operators and guides | Trend analytics, demand forecasting, client data insights |

### 1.3 Value Proposition

LankaGuide AI delivers the only unified, AI-native tourism companion purpose-built for Sri Lanka. Unlike global platforms (TripAdvisor, Google Travel) that offer generic suggestions, this system combines deep local knowledge, curated multimedia, and a Gemini-powered RAG engine to deliver responses grounded in verified, Sri Lanka-specific data. It transforms the tourist's mobile device into an intelligent travel companion that understands context, adapts to preferences, and enriches every aspect of the journey.

---

## 2. Insights from Literature Review

### 2.1 Key Findings

- Tourism applications globally are transitioning from static rule-based systems to intelligent, AI-enabled platforms driven by NLP, image recognition, recommendation systems, and real-time analytics (Li & Gretzel, 2021).
- LLMs and RAG pipelines (Lewis et al., 2020) have produced context-aware conversational agents that overcome the limitations of brittle rule-based chatbots — enabling dynamic, personalized responses grounded in verifiable knowledge.
- Sentiment analysis of social media reviews has been validated as a mechanism for surfacing emerging tourist hotspots and visitor concerns at scale (Haque et al., 2022), providing strategic intelligence that static platforms cannot deliver.
- Collaborative filtering and neural recommender systems show measurable improvements in itinerary personalization when augmented with contextual signals (budget, season, group size) over purely rule-based approaches (Zhang et al., 2020).
- Multilingual machine translation and voice interfaces significantly reduce friction for non-English-speaking tourists, with demonstrable impact on satisfaction metrics (Lu, 2021).
- Computer vision models for landmark recognition (Kang et al., 2022) enable intelligent photo-tagging, discovery features, and augmented reality-style information overlays.
- Seasonal time-series forecasting of tourist hotspots enables demand prediction and proactive recommendation adjustment, particularly valuable in a market with strong monsoon-driven seasonality.

### 2.2 Existing Solutions & Their Limitations

| Platform | What It Does | Critical Limitation |
|---|---|---|
| TripAdvisor | Reviews, hotel/restaurant booking, generic suggestions | No LLM-powered context; not Sri Lanka-specific; no RAG |
| Google Travel | Trip planning, flights, hotels, generic AI suggestions | No local cultural depth; no cinematographic multimedia; generic |
| Sri Lanka Tourism (SLTDA) | Static promotional website | No AI, no personalization, no conversational interface |
| Local Booking Apps | Transport/hotel booking | No trip intelligence, no content recommendations, siloed |
| Global AI Chatbots | General-purpose LLM assistants | No Sri Lanka-specific knowledge base; high hallucination risk |

### 2.3 Identified Research Gaps

The following gaps, directly extracted from the literature review, drive every feature in this PRD:

1. **Gap 1:** No unified multi-modal AI system (text + voice + image) exists for Sri Lanka tourism.
2. **Gap 2:** No LLM + RAG implementation grounded in Sri Lanka-specific curated knowledge.
3. **Gap 3:** No real-time social media sentiment analysis integrated into tourism recommendations.
4. **Gap 4:** No context-aware itinerary generator accounting for seasonal variation, budget, and preferences.
5. **Gap 5:** No cinematographic/immersive multimedia layer within a digital guide.
6. **Gap 6:** No multilingual real-time translation tool built for Sri Lankan languages (Sinhala, Tamil).
7. **Gap 7:** No health, safety, and regional alert system for tourists.
8. **Gap 8:** No time-series demand forecasting to predict peak seasons and attraction crowd levels.
9. **Gap 9:** No analytics dashboard for local tourism stakeholders to act on visitor data.

---

## 3. Product Strategy

### 3.1 How This Product Closes the Gaps

Every product feature maps 1:1 to a documented research gap. The strategy is not to be another general-purpose travel app but to be the definitive AI companion for Sri Lanka specifically — deeply contextual, locally curated, and technically differentiated through its RAG architecture.

| Research Gap | Product Response |
|---|---|
| No unified multimodal AI (Gap 1) | AI Assistant supporting text, voice input, and image queries |
| No LLM + RAG for Sri Lanka (Gap 2) | Gemini API + ChromaDB RAG with curated local knowledge base |
| No social media sentiment (Gap 3) | Trend Mining Module with live social media ingestion via Kafka |
| No context-aware itinerary (Gap 4) | Smart Itinerary Builder with seasonal, budget, preference signals |
| No immersive multimedia (Gap 5) | Cinematographic Gallery with curated video and photo content |
| No multilingual translation (Gap 6) | Real-Time Translation powered by Gemini multilingual models |
| No health/safety alerts (Gap 7) | Regional Alert System with government API and curated feeds |
| No demand forecasting (Gap 8) | Seasonal Trend Predictor using time-series ML |
| No stakeholder analytics (Gap 9) | Analytics Dashboard for local agencies and SLTDA |

### 3.2 Competitive Differentiation

- **Accuracy:** RAG-grounded responses — unlike ChatGPT or Gemini used raw, every AI response is grounded in verified Sri Lanka data, eliminating hallucination about local facts.
- **Immersion:** Cinematographic experience — no existing Sri Lanka travel platform includes curated cinematic video content embedded within AI-contextual recommendations.
- **Localization:** Trilingual support (Sinhala, Tamil, English) — no existing platform delivers this for Sri Lanka.
- **Network Effects:** Stakeholder intelligence — the analytics dashboard creates a B2B2C flywheel where local agency value drives continued content quality.
- **Timeliness:** Seasonal intelligence — real-time crowd and demand forecasting is absent from all existing Sri Lanka tourism tools.

---

## 4. Feature Breakdown

### 4.1 Core Features

#### 4.1.1 AI Conversational Assistant *(Maps to Gap 1, 2)*

A Gemini-powered chat interface enabling tourists to ask natural language questions about Sri Lanka. The assistant retrieves relevant context from ChromaDB before generating a response, ensuring all answers are grounded in curated local knowledge rather than relying on the model's pretrained weights alone.

- Text input with rich markdown-rendered responses
- Voice input (Web Speech API in browser; processed as text before LLM call)
- Follow-up question support via conversation history management
- Confidence indicators and source attribution on responses

#### 4.1.2 Smart Itinerary Builder *(Maps to Gap 4)*

A multi-step wizard that collects user preferences (number of days, budget range, travel style, district interests, group composition) and generates a full day-by-day itinerary using Gemini with RAG context injection. The itinerary adapts based on real-time seasonal data.

- Preference capture: days, budget (LKR/USD), interests (nature/culture/adventure/food), districts
- Seasonal adjustment: monsoon calendars, peak crowd predictions injected into prompt
- Itinerary output: day-by-day schedule with attraction details, estimated times, travel tips
- Export to PDF / share via link
- Edit and regenerate individual days

#### 4.1.3 Destination Explorer *(Maps to Gap 5)*

A browse-first interface for discovering Sri Lanka's 25 districts, major attractions, hidden gems, and cultural events. Each destination page includes curated cinematographic video, high-quality photography, AI-generated summaries, and user reviews.

- District-level and attraction-level pages
- Embedded cinematic video from curated library
- AI-generated contextual summaries (Gemini + RAG)
- Filterable by category: beach, wildlife, cultural, religious, adventure

#### 4.1.4 Landmark Image Recognition *(Maps to Gap 1)*

Users can upload a photo of an attraction, landmark, or artifact. The system uses a lightweight computer vision model (MobileNet-based) to classify the landmark and then triggers a RAG-powered Gemini response with historical and contextual information.

- Upload image → classify landmark → retrieve knowledge → generate contextual explanation
- Confidence threshold display
- Fallback to manual search if confidence < 70%

#### 4.1.5 Real-Time Translation *(Maps to Gap 6)*

In-app translation between English, Sinhala, and Tamil powered by Gemini's multilingual capabilities. Supports both typed input and voice input for tourist-to-local communication scenarios.

- Text translation (EN ↔ SI ↔ TA)
- Common phrases phrasebook (pre-embedded, offline-capable)
- Pronunciation guide with text-to-speech

### 4.2 AI-Powered Features (Gemini-centric)

#### 4.2.1 Sentiment-Driven Attraction Trending *(Maps to Gap 3)*

A background pipeline ingests recent Google Reviews and public social media mentions of Sri Lanka tourism sites. Sentiment scores are computed using a fine-tuned BERT model (pre-trained, via Hugging Face) and aggregated into a trending score per attraction. Gemini synthesizes these signals into natural language trend summaries visible in the app.

- Data sources: Google Places Reviews API, Reddit (tourism subreddits), X/Twitter public search
- Sentiment model: `cardiffnlp/twitter-roberta-base-sentiment` (Hugging Face)
- Trend scores updated every 6 hours via Kafka pipeline
- Gemini-generated natural language: *"Tourists are raving about Ella Rock this week due to..."*

#### 4.2.2 Seasonal Forecasting Module *(Maps to Gap 8)*

A time-series forecasting module trained on historical visitor counts (from SLTDA data) and weather data to predict crowd levels and optimal visit timing per district per month. Built with Facebook Prophet (lightweight, reliable for seasonal data).

- Per-district monthly crowd index (1–10 scale)
- Best time to visit recommendations injected into itinerary builder and destination pages
- Peak season warnings with alternative suggestions

#### 4.2.3 Personalized Recommendation Engine *(Maps to Gap 4)*

After a user's first itinerary or session, a lightweight preference profile is built. Subsequent recommendations use collaborative filtering signals (attractions liked by similar users) combined with content-based signals from ChromaDB embeddings.

- Anonymous preference profiles (no PII required)
- Session-based similarity clustering
- Gemini prompt enrichment with user preference tags

#### 4.2.4 Health & Safety Alert System *(Maps to Gap 7)*

Monitors government advisories (Ministry of Health Sri Lanka, Weather APIs, and the SLTDA emergency feeds) and surfaces location-relevant alerts in the app. Gemini summarizes verbose government text into actionable tourist-friendly notifications.

- Data sources: Sri Lanka Met Department API, SLTDA official feeds, WHO country alerts
- In-app notification banner and dedicated alerts page
- Gemini summarization of raw advisory text

### 4.3 Future Scope

- Augmented Reality (AR) landmark overlays using device camera
- Offline mode with pre-downloaded district knowledge packs
- Group trip collaboration (shared itinerary editing)
- Integration with local transport APIs (PickMe, Uber Sri Lanka)
- Booking integration with verified local hotels and experience providers

---

## 5. User Flows

### 5.1 Flow 1: First-Time Visitor Onboarding & AI Chat

1. User lands on app homepage → clicks "Start Exploring"
2. Quick onboarding: select language (EN/SI/TA), travel dates, rough budget, interests (multi-select checkboxes)
3. Profile stored in localStorage + anonymous session created in backend
4. User lands on dashboard: trending attractions, weather widget, quick-start chat
5. User types: *"What are the best things to do in Sigiriya?"*
6. Frontend sends query + session history to `/api/chat/`
7. Backend embeds query → ChromaDB retrieval (top-5 chunks) → prompt construction → Gemini API call
8. Streaming response rendered in chat UI with source citations
9. User follows up: *"How do I get there from Colombo?"*
10. Conversation history sent with new query → context-aware response generated

### 5.2 Flow 2: Smart Itinerary Generation

1. User clicks "Build My Trip" from navbar
2. Step 1: Enter travel dates (date range picker)
3. Step 2: Budget selection (slider: LKR 5,000 – 500,000+ per day)
4. Step 3: Interests multi-select (Beach, Wildlife, Culture, Adventure, Food, Religious)
5. Step 4: Districts of interest (map-based selector showing Sri Lanka's 25 districts)
6. Step 5: Group size and composition (solo/couple/family/group)
7. Submit → `POST /api/itinerary/generate/` with all parameters
8. Backend constructs enriched prompt: user preferences + seasonal forecast data + RAG context
9. Gemini generates structured JSON itinerary (day → attractions → timing → tips)
10. Frontend renders day-by-day accordion with embedded attraction cards and videos
11. User can regenerate a specific day, export PDF, or save to profile

### 5.3 Flow 3: Image-Based Landmark Discovery

1. User sees an interesting building or statue → taps camera icon in app
2. Image captured/uploaded → `POST /api/vision/identify/`
3. Backend runs MobileNet classification → top-3 landmark predictions returned
4. If confidence > 70%: auto-select top prediction
5. ChromaDB retrieval using landmark name as query
6. Gemini generates rich contextual response: history, significance, visiting tips
7. Response displayed with landmark name, confidence badge, and AI narrative
8. User can "Add to Itinerary" from the result card

### 5.4 Flow 4: Sentiment Trend Discovery

1. User browses "What's Trending" section on homepage
2. Frontend fetches `GET /api/trends/attractions/`
3. Response: list of attractions sorted by `trend_score` with Gemini-generated summaries
4. User taps trending card → full destination page with curated multimedia
5. User reads AI-synthesized review summary: *"85% of recent visitors mention the sunset views..."*

---

## 6. System Architecture

### 6.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER                                │
│           Next.js Frontend (Vercel / AWS EC2)                   │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Chat UI     │  │ Itinerary    │  │ Destination Explorer │  │
│  │ (Shadcn)    │  │ Builder      │  │ + Video Gallery      │  │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼────────────────┼──────────────────────┼─────────────┘
          │    HTTPS REST  │                       │
┌─────────▼────────────────▼──────────────────────▼─────────────┐
│                    API GATEWAY LAYER                           │
│              Django REST Framework (Gunicorn + Nginx)           │
│  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ /chat/   │ │/itinerary/ │ │ /vision/ │ │ /trends/      │  │
│  └──────┬───┘ └─────┬──────┘ └────┬─────┘ └──────┬────────┘  │
└─────────┼───────────┼─────────────┼───────────────┼───────────┘
          │           │             │               │
┌─────────▼───────────▼─────────────▼───────────────▼───────────┐
│                    SERVICE LAYER                               │
│  ┌────────────────┐   ┌──────────────────┐  ┌──────────────┐ │
│  │  RAG Service   │   │  Vision Service  │  │Trend Service │ │
│  │  (Core AI)     │   │  (MobileNet)     │  │(Sentiment)   │ │
│  └───────┬────────┘   └──────────────────┘  └──────┬───────┘ │
│          │                                           │         │
│  ┌───────▼────────────────────────────────┐        │         │
│  │           Gemini API Layer              │◄───────┘         │
│  │  (Text Gen / Summarization / Translation) │                │
│  └───────┬────────────────────────────────┘                  │
└──────────┼─────────────────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────┐
│               DATA & STORAGE LAYER                          │
│  ┌────────────────┐   ┌──────────────────────────────────┐  │
│  │  MySQL (RDS)   │   │    ChromaDB (Vector Store)       │  │
│  │  - Users       │   │    - Attraction embeddings       │  │
│  │  - Itineraries │   │    - District knowledge chunks   │  │
│  │  - Sessions    │   │    - Review embeddings           │  │
│  │  - Attractions │   │    - Multimedia metadata         │  │
│  └────────────────┘   └──────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│             STREAMING LAYER (Selective)                      │
│  Apache Kafka: Review Ingestion → Sentiment → Trend Update   │
│  Topics: [raw_reviews] → [sentiment_scores] → [trend_cache]  │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Technology Justification

| Technology | Role | Justification |
|---|---|---|
| Next.js 14 | Frontend framework | Server-side rendering for SEO, app router for clean routing, optimal for dynamic content |
| Shadcn UI | Component library | Accessible, unstyled primitives — avoids bloated icon libraries, minimal aesthetic |
| Django DRF | REST API backend | Mature Python ecosystem, seamless Hugging Face/PyTorch integration, excellent ORM |
| MySQL | Relational data | Reliable ACID compliance for user data, itineraries, sessions; well-supported on EC2 |
| ChromaDB | Vector database | Lightweight, runs in-process on EC2 (no managed service needed), Python-native |
| Gemini API | LLM + multimodal | Superior multilingual support (Sinhala/Tamil), competitive pricing, vision capabilities |
| Apache Kafka | Event streaming | Needed ONLY for the async sentiment pipeline — decouples review ingestion from processing |
| Facebook Prophet | Time-series forecasting | Handles seasonality well; simple to deploy on EC2 without GPU |
| Hugging Face | Sentiment NLP model | Pre-trained RoBERTa model, no training cost, fast inference on CPU |

---

## 7. Database Design (MySQL)

### 7.1 Schema

```sql
-- ── USERS & SESSIONS ──────────────────────────────────────────
CREATE TABLE users (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  session_token VARCHAR(128) UNIQUE NOT NULL,  -- anonymous sessions
  language      ENUM('en','si','ta') DEFAULT 'en',
  budget_range  VARCHAR(32),
  interests     JSON,                           -- ["beach","culture"]
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ── GEOGRAPHIC DATA ────────────────────────────────────────────
CREATE TABLE districts (
  id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(100) NOT NULL,
  province      VARCHAR(100) NOT NULL,
  description   TEXT,
  climate_zone  ENUM('wet','dry','intermediate') NOT NULL,
  peak_months   JSON,                           -- [3,4,7,8]
  lat           DECIMAL(9,6),
  lng           DECIMAL(9,6)
);

CREATE TABLE attractions (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  district_id     INT UNSIGNED NOT NULL,
  name            VARCHAR(200) NOT NULL,
  slug            VARCHAR(220) UNIQUE NOT NULL,
  category        ENUM('beach','wildlife','cultural','religious','adventure','food') NOT NULL,
  description     TEXT,
  address         VARCHAR(300),
  lat             DECIMAL(9,6),
  lng             DECIMAL(9,6),
  entry_fee_lkr   DECIMAL(10,2),
  best_season     JSON,
  crowd_index     TINYINT UNSIGNED DEFAULT 5,   -- 1-10
  trend_score     FLOAT DEFAULT 0.0,
  chroma_doc_id   VARCHAR(128),                 -- reference to ChromaDB
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (district_id) REFERENCES districts(id)
);

-- ── MULTIMEDIA ──────────────────────────────────────────────────
CREATE TABLE media_assets (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  attraction_id   BIGINT UNSIGNED,
  type            ENUM('image','video') NOT NULL,
  s3_key          VARCHAR(500) NOT NULL,        -- S3 object key
  cdn_url         VARCHAR(500),
  is_featured     BOOLEAN DEFAULT FALSE,
  caption         TEXT,
  attribution     VARCHAR(300),
  FOREIGN KEY (attraction_id) REFERENCES attractions(id)
);

-- ── ITINERARIES ─────────────────────────────────────────────────
CREATE TABLE itineraries (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NOT NULL,
  title           VARCHAR(200),
  start_date      DATE NOT NULL,
  end_date        DATE NOT NULL,
  budget_lkr      DECIMAL(12,2),
  group_size      TINYINT UNSIGNED DEFAULT 1,
  group_type      ENUM('solo','couple','family','group') DEFAULT 'solo',
  status          ENUM('draft','saved','shared') DEFAULT 'draft',
  share_token     VARCHAR(64) UNIQUE,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE itinerary_days (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  itinerary_id    BIGINT UNSIGNED NOT NULL,
  day_number      TINYINT UNSIGNED NOT NULL,
  district_id     INT UNSIGNED,
  notes           TEXT,
  ai_generated    BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (itinerary_id) REFERENCES itineraries(id),
  FOREIGN KEY (district_id) REFERENCES districts(id)
);

CREATE TABLE itinerary_stops (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  day_id          BIGINT UNSIGNED NOT NULL,
  attraction_id   BIGINT UNSIGNED NOT NULL,
  stop_order      TINYINT UNSIGNED NOT NULL,
  arrival_time    TIME,
  duration_mins   SMALLINT UNSIGNED,
  tip             TEXT,
  FOREIGN KEY (day_id) REFERENCES itinerary_days(id),
  FOREIGN KEY (attraction_id) REFERENCES attractions(id)
);

-- ── CHAT / SESSIONS ─────────────────────────────────────────────
CREATE TABLE chat_sessions (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id         BIGINT UNSIGNED NOT NULL,
  started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE chat_messages (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  session_id      BIGINT UNSIGNED NOT NULL,
  role            ENUM('user','assistant') NOT NULL,
  content         TEXT NOT NULL,
  retrieved_docs  JSON,     -- [{chroma_id, score}, ...]
  tokens_used     INT UNSIGNED,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
);

-- ── REVIEWS & SENTIMENT ─────────────────────────────────────────
CREATE TABLE reviews (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  attraction_id   BIGINT UNSIGNED NOT NULL,
  source          ENUM('google','reddit','twitter','manual') NOT NULL,
  external_id     VARCHAR(200),
  body            TEXT NOT NULL,
  sentiment_score FLOAT,          -- -1.0 to 1.0
  sentiment_label ENUM('positive','neutral','negative'),
  published_at    TIMESTAMP,
  ingested_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_source_id (source, external_id),
  FOREIGN KEY (attraction_id) REFERENCES attractions(id)
);

-- ── FORECASTING ─────────────────────────────────────────────────
CREATE TABLE crowd_forecasts (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  attraction_id   BIGINT UNSIGNED NOT NULL,
  forecast_month  DATE NOT NULL,  -- first day of month
  crowd_index     FLOAT NOT NULL, -- 1.0 - 10.0
  confidence      FLOAT,
  model_version   VARCHAR(32),
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_forecast (attraction_id, forecast_month),
  FOREIGN KEY (attraction_id) REFERENCES attractions(id)
);

-- ── ALERTS ──────────────────────────────────────────────────────
CREATE TABLE safety_alerts (
  id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  district_id     INT UNSIGNED,  -- NULL = nationwide
  title           VARCHAR(300) NOT NULL,
  body            TEXT NOT NULL,
  severity        ENUM('info','warning','danger') DEFAULT 'info',
  source_url      VARCHAR(500),
  active          BOOLEAN DEFAULT TRUE,
  expires_at      TIMESTAMP,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (district_id) REFERENCES districts(id)
);
```

---

## 8. API Design

### 8.1 Base URL & Conventions

- **Base URL:** `https://api.lankaguide.lk/api/v1/`
- All endpoints return JSON.
- Authentication uses session tokens passed in the `X-Session-Token` header (anonymous sessions; no OAuth required for MVP).
- All POST bodies are `application/json`.

### 8.2 Core Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat/message/` | Send a chat message; returns streaming AI response |
| GET | `/chat/sessions/{id}/history/` | Retrieve conversation history for a session |
| POST | `/itinerary/generate/` | Generate a new AI itinerary from preferences |
| GET | `/itinerary/{id}/` | Retrieve a saved itinerary |
| PATCH | `/itinerary/{id}/day/{day_num}/regenerate/` | Regenerate a specific day |
| GET | `/attractions/` | List attractions with filters (district, category, season) |
| GET | `/attractions/{slug}/` | Full attraction detail with media and AI summary |
| POST | `/vision/identify/` | Upload image for landmark recognition |
| GET | `/trends/attractions/` | Get trending attractions sorted by trend_score |
| POST | `/translate/` | Translate text between EN, SI, TA |
| GET | `/alerts/` | Get active safety alerts (filterable by district) |
| GET | `/districts/` | List all districts with seasonal data |
| GET | `/forecasts/{attraction_id}/` | Get crowd forecast for attraction by month |
| GET | `/analytics/dashboard/` | Stakeholder analytics (role-protected) |

### 8.3 Request / Response Examples

#### POST `/chat/message/`

```json
// Request
{
  "session_id": "sess_abc123",
  "message": "What is the best time to visit Yala National Park?",
  "language": "en"
}

// Response
{
  "message_id": "msg_xyz789",
  "response": "The best time to visit Yala National Park is from February to July...",
  "sources": [
    { "doc_id": "yala_001", "title": "Yala National Park Guide", "relevance": 0.94 }
  ],
  "tokens_used": 312,
  "session_id": "sess_abc123"
}
```

#### POST `/itinerary/generate/`

```json
// Request
{
  "start_date": "2025-12-01",
  "end_date": "2025-12-07",
  "budget_lkr": 50000,
  "interests": ["wildlife", "cultural", "beach"],
  "district_ids": [1, 5, 12],
  "group_type": "couple",
  "group_size": 2
}

// Response
{
  "itinerary_id": 1042,
  "title": "7-Day Wildlife & Culture Journey",
  "days": [
    {
      "day": 1,
      "district": "Colombo",
      "stops": [
        {
          "attraction_id": 55,
          "name": "Gangaramaya Temple",
          "arrival_time": "09:00",
          "duration_mins": 90,
          "tip": "Arrive early to avoid crowds; dress modestly."
        }
      ]
    }
  ],
  "share_token": "shr_a1b2c3"
}
```

#### POST `/vision/identify/`

```json
// Request: multipart/form-data
// image: <binary file>

// Response
{
  "predictions": [
    { "label": "Sigiriya Rock Fortress", "confidence": 0.92 },
    { "label": "Pidurangala Rock", "confidence": 0.06 }
  ],
  "top_match": "Sigiriya Rock Fortress",
  "ai_summary": "Sigiriya, often called the Eighth Wonder of the World, is a 5th-century royal citadel...",
  "attraction_slug": "sigiriya-rock-fortress"
}
```

---

## 9. AI / RAG Pipeline (Detailed)

### 9.1 Data Ingestion & Knowledge Base Creation

The knowledge base is the foundation of the RAG system. It must be curated, structured, and rich enough to ground Gemini's responses in verifiable Sri Lanka facts.

#### 9.1.1 Data Sources

- Government sources: SLTDA attraction database, district profiles, event calendars
- Academic sources: cultural and historical texts (digitized, CC-licensed)
- Custom authored content: researcher-written attraction guides for all 25 districts
- Multimedia metadata: attraction photo/video captions and descriptions
- Review aggregates: sanitized, de-identified visitor review summaries

#### 9.1.2 Document Processing Pipeline

```
Raw Content (PDF, Word, Web)
    ↓
Text Extraction (pdfplumber, python-docx, BeautifulSoup)
    ↓
Chunking Strategy:
  - Chunk size: 512 tokens (optimal for Gemini context + retrieval precision)
  - Overlap: 64 tokens (preserves context at boundaries)
  - Chunking unit: paragraph-aware (never split mid-sentence)
    ↓
Metadata Tagging per chunk:
  { attraction_id, district_id, category, language, source_type, date_created }
    ↓
Embedding Generation:
  Model: models/text-embedding-004 (Gemini Embedding API)
  Dimension: 768
    ↓
Storage: ChromaDB collection 'sri_lanka_tourism'
  - Document: chunk text
  - Embedding: 768-dim vector
  - Metadata: {attraction_id, district_id, category, ...}
```

### 9.2 Query Pipeline (User Query → Gemini Response)

```
User Query: "What are the best wildlife experiences near Yala?"
    ↓
Step 1: Query Embedding
  embed_query = gemini.embed_content(
    model='models/text-embedding-004',
    content=user_query
  )  # → 768-dim vector
    ↓
Step 2: ChromaDB Retrieval
  results = chroma_collection.query(
    query_embeddings=[embed_query],
    n_results=5,
    where={'category': {'$in': ['wildlife', 'general']}}  # metadata filter
  )  # → top-5 most semantically similar chunks
    ↓
Step 3: Context Construction
  context = "\n\n".join([doc for doc in results['documents'][0]])
    ↓
Step 4: Prompt Engineering (see 9.3)
    ↓
Step 5: Gemini API Call
  response = gemini.generate_content(final_prompt)
    ↓
Step 6: Response Post-Processing
  - Extract source references
  - Strip hallucinated URLs
  - Apply language formatting (if SI/TA requested)
    ↓
Return to Frontend: { response_text, sources, tokens_used }
```

### 9.3 Prompt Engineering Strategy

All prompts use a four-part structure: **System Role → Retrieved Context → Conversation History → User Query**.

```python
SYSTEM_PROMPT = """
You are LankaGuide AI, an expert tourism companion for Sri Lanka.
You ONLY answer questions about travel in Sri Lanka.
You MUST base all factual claims on the CONTEXT provided below.
If the context does not contain enough information, say so clearly.
Do NOT invent attraction names, prices, or contact details.
Respond in {language}. Be concise, friendly, and practical.
"""

RETRIEVAL_CONTEXT = """
=== RETRIEVED KNOWLEDGE ===
{retrieved_chunks}
=== END RETRIEVED KNOWLEDGE ===
"""

CONVERSATION_HISTORY = """
=== PREVIOUS CONVERSATION ===
{last_4_turns}
=== END CONVERSATION ===
"""

USER_QUERY = "Tourist Question: {user_query}"

FINAL_PROMPT = SYSTEM_PROMPT + RETRIEVAL_CONTEXT + CONVERSATION_HISTORY + USER_QUERY
```

### 9.4 Itinerary Generation Prompt

```python
ITINERARY_SYSTEM = """
You are a Sri Lanka travel planning expert.
Generate a day-by-day itinerary as valid JSON matching the schema provided.
Use ONLY attractions mentioned in the CONTEXT below.
Respect the user's budget, interests, group type, and travel dates.
Factor in the seasonal data provided: avoid flooded roads and monsoon-heavy areas.
Output ONLY the JSON object. No additional commentary.
"""

SEASONAL_CONTEXT = """
Current season data for selected districts:
{district_seasonal_data}  # injected from DB crowd_forecasts
"""

OUTPUT_SCHEMA = """
{ days: [ { day: int, district: str, stops: [
  { attraction_id, name, arrival_time, duration_mins, tip } ] } ] }
"""
```

### 9.5 Context Window Management

- Maximum context per call: 12,000 tokens (leaves headroom in Gemini 1.5 Flash's 1M context)
- Conversation history: retain last 4 turns only (~800 tokens)
- Retrieved chunks: 5 chunks × 512 tokens = ~2,560 tokens
- System prompt: ~300 tokens
- **Total managed context: ~3,660 tokens per call** — well within budget
- If user query is long (>200 tokens), summarize query before embedding to maintain precision

### 9.6 Cost Optimization Strategy

- Use `gemini-1.5-flash` for chat and itinerary (cheaper, sufficient quality) — reserve `gemini-1.5-pro` for complex multi-day itinerary generation only
- Cache embeddings: re-embed knowledge base chunks only when content changes (not per query)
- Cache ChromaDB results: for identical or near-identical queries (Redis TTL 15 min)
- Cache full responses: for top-50 most-asked questions (Redis TTL 1 hour)
- Token budgeting: enforce `max_output_tokens=1024` for chat, `2048` for itineraries
- Batch embeddings: when ingesting new content, use Gemini batch embedding API

### 9.7 Caching Strategy

| Cache Layer | What is Cached | TTL | Implementation |
|---|---|---|---|
| Query result cache | ChromaDB retrieval results for repeated queries | 15 min | Django cache (Redis) |
| Response cache | Full Gemini responses for top FAQs | 1 hour | Django cache (Redis) |
| Trend cache | Trending attraction scores + summaries | 6 hours | Django cache (Redis) |
| Embedding cache | Knowledge chunk embeddings | Persistent | ChromaDB (on-disk) |
| Forecast cache | Crowd prediction results | 30 days | MySQL crowd_forecasts table |

---

## 10. Real-Time Streaming (Apache Kafka)

### 10.1 When Kafka is Needed

Kafka is used **only** for the sentiment analysis and trend mining pipeline. This is the one component where data volume (potentially thousands of reviews per day) and processing latency justify an async event streaming architecture. All other features use synchronous Django REST calls.

### 10.2 Kafka Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  KAFKA PIPELINE                             │
│                                                             │
│  Data Producers (run every 6 hours via cron):              │
│  - Google Places Reviews scraper (Python)                  │
│  - Reddit API consumer (r/srilanka, r/travel)              │
│  - Twitter/X API (hashtag: #VisitSriLanka, #SriLankaTour)  │
│         ↓  Produce to topic: [raw_reviews]                 │
│                                                             │
│  Kafka Broker (single node, EC2 t3.medium)                 │
│  Topics:                                                    │
│    - raw_reviews    (partitioned by attraction_id)          │
│    - sentiment_done (partitioned by attraction_id)          │
│                                                             │
│  Consumer Group 1: sentiment_worker (Django management cmd) │
│    - Consumes from [raw_reviews]                           │
│    - Runs RoBERTa sentiment model                          │
│    - Saves review + score to MySQL reviews table           │
│    - Produces to [sentiment_done]                          │
│         ↓                                                  │
│  Consumer Group 2: trend_aggregator                        │
│    - Consumes from [sentiment_done]                        │
│    - Recalculates attraction trend_score (rolling 7-day)   │
│    - Triggers Gemini summarization of top-5 reviews        │
│    - Updates attractions.trend_score in MySQL              │
│    - Invalidates trend Redis cache                         │
└─────────────────────────────────────────────────────────────┘
```

### 10.3 Trend Score Calculation

```python
import math

def calculate_trend_score(recent_reviews: list[dict]) -> float:
    """
    recent_reviews: last 7 days of reviews for an attraction
    Each review: { sentiment_score: float (-1 to 1), published_at: datetime }
    Returns: trend_score (0.0 - 10.0)
    """
    if not recent_reviews:
        return 0.0

    # Time decay: recent reviews weighted more heavily
    now = datetime.utcnow()
    weighted_scores = []
    for r in recent_reviews:
        age_hours = (now - r['published_at']).total_seconds() / 3600
        decay_weight = math.exp(-0.01 * age_hours)  # exponential decay
        weighted_scores.append(r['sentiment_score'] * decay_weight)

    avg_sentiment = sum(weighted_scores) / len(weighted_scores)
    volume_bonus = min(len(recent_reviews) / 50, 1.0)  # cap at 50 reviews
    raw_score = (avg_sentiment + 1) / 2  # normalize to 0-1
    trend_score = (raw_score * 0.7 + volume_bonus * 0.3) * 10
    return round(trend_score, 2)
```

---

## 11. UI/UX Guidelines

### 11.1 Design Philosophy

The interface must feel calm, authoritative, and distinctly Sri Lankan without being decorative. Every pixel of chrome (navigation, labels, icons) must justify its existence. The content — photography, video, AI responses — is the hero.

### 11.2 Color & Typography

| Token | Value | Usage |
|---|---|---|
| Primary | `#1B4F72` (deep ocean blue) | Navigation, CTAs, headings |
| Accent | `#D4A017` (golden-amber) | Highlights, badges, trending indicators |
| Surface | `#F8F9FA` | Page backgrounds |
| Surface-elevated | `#FFFFFF` | Cards, modals |
| Text-primary | `#1A1A2E` | Body text |
| Text-muted | `#6C757D` | Captions, metadata |
| Heading font | Inter (Google Fonts) | All headings |
| Body font | Inter | Body text, UI labels |
| Mono font | JetBrains Mono | Code, API keys |

### 11.3 Key Layout Patterns

- **Navigation:** Left sidebar on desktop (collapsed to icon rail on <1024px); bottom tab bar on mobile
- **Chat UI:** Full-height split panel — attraction context card on left (collapsed on mobile), chat thread on right
- **Itinerary Builder:** Wizard-style multi-step form using Shadcn Stepper — one decision per screen
- **Destination Pages:** Full-bleed hero video/image at top; scrollable content below with sticky attraction metadata card
- **Trending Section:** Horizontal scroll carousel on mobile; masonry grid on desktop

### 11.4 Shadcn Components Used

- Chat input: `Textarea` + `Button` + `ScrollArea`
- Itinerary wizard: `Tabs` (steps) + `Slider` (budget) + `Checkbox` (interests) + `Calendar` (date range)
- Attraction cards: `Card` + `Badge` (category) + `Progress` (crowd index)
- Alert system: `Alert` with severity-mapped color variants
- Translation: `Select` (language picker) + `Textarea`
- Analytics: Recharts (time series) + `Table` + `DataTable`

### 11.5 Accessibility & Performance

- All interactive elements keyboard navigable; ARIA labels on all icon-only buttons
- Images served via Next.js `Image` component with lazy loading and responsive srcset
- Videos: lazy-loaded with poster frames; autoplay disabled by default
- Target Core Web Vitals: LCP < 2.5s, FID < 100ms, CLS < 0.1
- First meaningful paint optimized via Next.js SSR for destination pages (SEO critical)

---

## 12. Development Roadmap

### 12.1 Phase Overview

| Phase | Duration | Focus | Deliverable |
|---|---|---|---|
| Phase 0: Foundation | Weeks 1–2 | Project setup, tooling, DB schema, EC2 init | Dev environment running, MySQL schema deployed |
| Phase 1: Knowledge Base | Weeks 3–4 | Data collection, document processing, ChromaDB ingestion | All 25 districts embedded; basic RAG query working |
| Phase 2: Core AI | Weeks 5–7 | Chat API, itinerary API, RAG pipeline, Gemini integration | Working chat and itinerary generation endpoints |
| Phase 3: Frontend MVP | Weeks 8–10 | Next.js app, Shadcn UI, chat UI, destination explorer | Functional web app (chat + explore) |
| Phase 4: Advanced AI | Weeks 11–13 | Vision module, sentiment pipeline, Kafka, forecasting | Landmark ID, trending feed, seasonal predictions |
| Phase 5: Integration | Weeks 14–15 | End-to-end testing, performance tuning, caching | Stable integrated system |
| Phase 6: Deployment | Weeks 16–17 | AWS EC2 production setup, Nginx, SSL, monitoring | Live production URL |
| Phase 7: Evaluation | Weeks 18–20 | User testing, accuracy eval, documentation, report | Final submission-ready system |

### 12.2 MVP Scope (Phase 0–3)

The Minimum Viable Product consists of: AI Conversational Assistant (text only), Smart Itinerary Builder (5 districts), Destination Explorer (top 50 attractions), basic user sessions, and the core RAG pipeline. Voice input, image recognition, Kafka pipeline, and analytics dashboard are post-MVP.

### 12.3 Timeline Estimation

Total development: **20 weeks (5 months)** — aligned with the university project timeline. Solo developer with supervisor support. The most technically complex phase is Phase 4 (Advanced AI) — allocate extra buffer here.

---

## 13. Deployment Plan (AWS EC2, No Docker)

### 13.1 EC2 Instance Architecture

| Server | EC2 Type | OS | Purpose |
|---|---|---|---|
| App Server | t3.large (2 vCPU, 8GB RAM) | Ubuntu 22.04 LTS | Django (Gunicorn) + ChromaDB + ML models |
| Web Server | Same instance (Nginx) | Ubuntu 22.04 LTS | Reverse proxy + SSL termination + static files |
| DB Server | db.t3.medium (RDS MySQL) | Managed | MySQL 8.0 (AWS RDS for reliability) |
| Kafka Broker | t3.medium (separate instance) | Ubuntu 22.04 LTS | Kafka + Zookeeper for sentiment pipeline |
| Media Storage | AWS S3 + CloudFront CDN | Managed | Images, videos — served via CDN globally |

### 13.2 Backend Deployment (Django)

```bash
# 1. System setup
sudo apt update && sudo apt upgrade -y
sudo apt install python3.11 python3.11-venv python3-pip nginx gcc g++ -y

# 2. App setup
cd /var/www/lankaguide
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Environment variables (.env file — never commit to git)
GEMINI_API_KEY=<your-key>
DJANGO_SECRET_KEY=<generated-key>
DB_HOST=<rds-endpoint>
DB_NAME=lankaguide
DB_USER=lankaguide_user
DB_PASSWORD=<secure-password>
REDIS_URL=redis://127.0.0.1:6379/0
CHROMA_PERSIST_DIR=/var/data/chroma
AWS_S3_BUCKET=lankaguide-media

# 4. Gunicorn systemd service
# /etc/systemd/system/lankaguide.service
[Unit]
Description=LankaGuide AI Django App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/lankaguide
ExecStart=/var/www/lankaguide/venv/bin/gunicorn \
    --workers 4 \
    --worker-class gthread \
    --threads 2 \
    --timeout 120 \
    --bind unix:/run/gunicorn.sock \
    config.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

### 13.3 Frontend Deployment (Next.js on EC2)

```bash
# Option A: Build static export (simpler, no Node server needed)
npm run build && npm run export
# Serve /out directory via Nginx

# Option B: Next.js Node server (required for SSR/API routes) — RECOMMENDED
npm run build

# /etc/systemd/system/lankaguide-next.service
[Service]
WorkingDirectory=/var/www/lankaguide-frontend
ExecStart=/usr/bin/node server.js
Environment=NODE_ENV=production
Environment=PORT=3000
Restart=always
```

### 13.4 Nginx Configuration

```nginx
# /etc/nginx/sites-available/lankaguide
server {
    listen 80;
    server_name lankaguide.lk www.lankaguide.lk;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name lankaguide.lk www.lankaguide.lk;

    ssl_certificate /etc/letsencrypt/live/lankaguide.lk/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/lankaguide.lk/privkey.pem;

    # Next.js frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }

    # Django API
    location /api/ {
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
    }

    # Static files (Django admin, DRF browsable API)
    location /static/ {
        alias /var/www/lankaguide/staticfiles/;
    }
}
```

### 13.5 Environment & Secrets Management

- Use AWS Systems Manager Parameter Store for all secrets (`GEMINI_API_KEY`, `DB_PASSWORD`)
- Load secrets into environment at service startup — never store in `.env` files in production
- Use separate `.env` files for dev/staging/production (git-ignored)
- Enable AWS CloudWatch for log aggregation and error alerting
- Set up AWS SNS email alerts for EC2 CPU > 80% or service restarts

---

## 14. Risks & Challenges

### 14.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|---|---|---|---|
| ChromaDB instability under load | High | Low | Persist data to disk; daily backups to S3; monitor memory |
| EC2 OOM with ML models loaded | High | Medium | Use t3.large; load sentiment model lazily; offload to separate worker |
| Gemini API rate limits exceeded | Medium | Medium | Implement exponential backoff; cache top queries; use batch API for ingestion |
| MySQL connection pool exhaustion | High | Low | Use Django's persistent connections; set connection pooling via django-db-geventpool |
| Kafka single-node failure | Medium | Low | Acceptable for academic project; note in limitations; use persistence (log.dirs) |
| Next.js SSR memory on EC2 | Medium | Medium | Monitor Node.js heap; use `--max-old-space-size=2048`; static export for simple pages |

### 14.2 AI-Specific Risks

| AI Risk | Description | Mitigation Strategy |
|---|---|---|
| Hallucination | Gemini fabricates attraction names, prices, or historical facts | Strict RAG-grounding prompt; "answer only from context" instruction; source attribution in responses |
| Response latency | Gemini API round-trip + ChromaDB retrieval = 3–8 seconds per query | Show streaming response character-by-character; cache top 50 FAQs; use Flash model for speed |
| Embedding drift | Knowledge base content changes but cached embeddings are stale | Version embeddings by content hash; re-embed on content update via admin command |
| Sentiment model bias | RoBERTa trained on English Twitter may misclassify Sinhala/Tamil reviews | Filter non-English reviews before sentiment scoring; flag low-confidence scores |
| API cost overrun | High query volume drives unexpected Gemini billing | Set Google Cloud billing alerts; daily token budget cap via middleware; monitor cost dashboard |
| Irrelevant retrieval | ChromaDB returns low-relevance chunks due to query mismatch | Set minimum cosine similarity threshold (0.65); fallback to keyword search if below threshold |

### 14.3 Non-Technical Risks

- **Data licensing:** ensure all knowledge base content is open-licensed or original — document attribution for every source
- **Cultural sensitivity:** AI responses about religious sites and customs must be reviewed by a human before deployment
- **Privacy compliance:** no PII collected without consent; anonymous session model by default; GDPR-aware design
- **Scope creep:** the feature set is ambitious for a final year project — strictly enforce MVP boundaries and defer post-MVP features

---

## Appendix: Cursor AI Development Plan

This section breaks the PRD into a sequenced series of Cursor AI prompts for efficient implementation. Each prompt is self-contained and builds on the previous deliverable.

> **How to use:** Give Cursor the **complete PRD** alongside each prompt. The prompts reference specific sections (e.g., "schema from Section 7", "prompt structure from Section 9.3"). Without the PRD in context, Cursor will produce generic code. Save this file as `docs/PRD.md` in your repo and use Cursor's `@file` feature to reference it.

---

### Prompt Sequence 1: Project Setup

**Prompt 1A — Django Project Scaffold**
> Create a new Django project named `lankaguide` with apps: `core`, `attractions`, `chat`, `itinerary`, `vision`, `sentiment`, `alerts`, `analytics`. Configure settings for MySQL (use `django-environ` for `.env` loading), set up CORS headers for Next.js on `localhost:3000`, and create a `requirements.txt` including: `djangorestframework`, `django-cors-headers`, `google-generativeai`, `chromadb`, `pillow`, `django-environ`, `gunicorn`, `redis`, `django-redis`, `kafka-python`, `prophet`, `transformers`, `torch` (CPU only).

**Prompt 1B — Next.js Project Scaffold**
> Create a new Next.js 14 project using the App Router. Install and configure: `shadcn/ui` (init with slate theme), `tailwindcss`, `axios`, `zustand` (for global state), and `react-query` (for server state). Create the folder structure: `app/(dashboard)/layout.tsx`, `app/(dashboard)/chat/page.tsx`, `app/(dashboard)/explore/page.tsx`, `app/(dashboard)/itinerary/page.tsx`, `components/ui/` (shadcn), `components/chat/`, `components/itinerary/`, `components/explore/`. Set up environment variables: `NEXT_PUBLIC_API_URL=http://localhost:8000`.

---

### Prompt Sequence 2: Django Backend APIs

**Prompt 2A — Attractions App**
> In the `attractions` app, create Django models matching the exact MySQL schema in Section 7 of the PRD (districts, attractions, media_assets tables). Create serializers for each model. Create ViewSets with filtering: `AttractionsViewSet` (filter by `district_id`, `category`, `season`), `DistrictsViewSet`, `MediaAssetsViewSet`. Register all routes with a DRF `DefaultRouter` under `/api/v1/`.

**Prompt 2B — Chat App**
> In the `chat` app, create models for `chat_sessions` and `chat_messages` (see Section 7 schema). Create a POST endpoint at `/api/v1/chat/message/` that: (1) validates the request body `{session_id, message, language}`, (2) creates or retrieves a `ChatSession`, (3) saves the user message, (4) calls a `RAGService.query()` method (stub for now), (5) saves the assistant response, (6) returns `{message_id, response, sources, tokens_used}`.

**Prompt 2C — Itinerary App**
> In the `itinerary` app, create models for `itineraries`, `itinerary_days`, `itinerary_stops`. Create a POST endpoint at `/api/v1/itinerary/generate/` that accepts `{start_date, end_date, budget_lkr, interests, district_ids, group_type, group_size}` and calls an `ItineraryService.generate()` stub. Create GET endpoints for retrieving and sharing itineraries.

---

### Prompt Sequence 3: Database & ChromaDB Setup

**Prompt 3A — Knowledge Base Ingestion**
> Create a Django management command `ingest_knowledge_base` that: (1) reads all `.txt` and `.pdf` files from a `/data/knowledge/` directory, (2) splits them into 512-token chunks with 64-token overlap using a simple token counter, (3) tags each chunk with metadata extracted from filename (`attraction_id`, `district_id`, `category`), (4) calls the Gemini embedding API (`models/text-embedding-004`) for each chunk, (5) stores in ChromaDB collection `sri_lanka_tourism` with metadata. Handle rate limiting with exponential backoff.

**Prompt 3B — Seed Database**
> Create a Django management command `seed_database` that populates the districts table with all 25 Sri Lanka districts (name, province, lat, lng, climate_zone, peak_months) and inserts 10 sample attractions per district (minimum 5 districts for MVP). Include realistic data for Colombo, Kandy, Galle, Sigiriya, and Ella districts.

---

### Prompt Sequence 4: AI Integration (Gemini + ChromaDB)

**Prompt 4A — RAG Service**
> Create a `RAGService` class in `lankaguide/services/rag_service.py`. Implement: (1) `__init__`: initialize ChromaDB client, load collection `sri_lanka_tourism`, initialize Gemini client. (2) `query(user_message, session_history, language)`: embed `user_message` using `text-embedding-004`, query ChromaDB for top-5 results filtered by metadata if possible, construct the four-part prompt (system + context + history + query) exactly as specified in PRD Section 9.3, call `gemini-1.5-flash` `generate_content`, return `{response_text, sources, tokens_used}`. Implement Redis caching on the response for identical queries (TTL 15 min).

**Prompt 4B — Itinerary Service**
> Create an `ItineraryService` class in `lankaguide/services/itinerary_service.py`. Implement `generate(preferences_dict)`: (1) fetch `crowd_forecast` data for selected districts from MySQL, (2) fetch relevant attraction chunks from ChromaDB filtered by category matching user interests, (3) construct the itinerary prompt with the schema defined in PRD Section 9.4, (4) call `gemini-1.5-pro` with `response_mime_type='application/json'`, (5) parse the JSON response and save itinerary + days + stops to MySQL, (6) return the itinerary ID. Handle Gemini JSON parsing errors with a retry.

**Prompt 4C — Vision Service**
> Create a `VisionService` in `lankaguide/services/vision_service.py`. Implement `identify(image_file)`: (1) load a pre-trained MobileNetV2 model from TensorFlow Hub, fine-tuned on Sri Lanka landmark classes (use a placeholder 50-class classifier for MVP), (2) preprocess the uploaded image to 224×224, (3) run inference and return top-3 predictions with confidence, (4) if confidence > 0.7, call `RAGService.query()` with the landmark name as query, (5) return `{predictions, top_match, ai_summary, attraction_slug}`.

---

### Prompt Sequence 5: Frontend (Next.js + Shadcn)

**Prompt 5A — Chat Interface**
> Create the main chat interface at `app/(dashboard)/chat/page.tsx`. Use Shadcn `ScrollArea` for the message thread, Shadcn `Textarea` for input, and Shadcn `Button` for send. Implement: message state with `useReducer` (messages array of `{id, role, content, sources}`), API call to `POST /api/v1/chat/message/` via axios, optimistic UI update (show user message immediately), render assistant messages with `react-markdown` for formatted text, show source attribution chips below each AI response. Store `session_id` in `localStorage`.

**Prompt 5B — Itinerary Builder**
> Create the Itinerary Builder wizard at `app/(dashboard)/itinerary/page.tsx` with 5 steps using Shadcn Tabs: Step 1: `DateRangePicker` (Shadcn Calendar). Step 2: Budget slider (Shadcn `Slider`, range 5,000–500,000 LKR). Step 3: Interests multi-select (Shadcn `Checkbox` grid: Beach, Wildlife, Culture, Adventure, Food, Religious). Step 4: District selector (simple grid of 25 district cards with checkbox). Step 5: Group type (Shadcn `RadioGroup`) + group size (Shadcn `Input`). On submit: POST to `/api/v1/itinerary/generate/` and render the returned day-by-day itinerary as an `Accordion`.

**Prompt 5C — Destination Explorer**
> Create the Destination Explorer at `app/(dashboard)/explore/page.tsx`. Fetch `GET /api/v1/attractions/` with filters. Render attractions as Shadcn `Card` components in a responsive grid (3 cols desktop, 2 tablet, 1 mobile). Each card: featured image (Next.js `Image`), name, district badge, category badge, crowd index as Shadcn `Progress` bar. Add filter controls: Shadcn `Select` for category + district. Implement a dynamic route `app/(dashboard)/explore/[slug]/page.tsx` for individual attraction pages with hero media, AI summary, and related attractions.

---

### Prompt Sequence 6: Integration & Testing

**Prompt 6A — Tests**
> Write pytest tests for the `RAGService`: (1) test that a query returns a response with sources, (2) test that Redis caching works (second identical call should not hit ChromaDB), (3) test error handling when Gemini API returns an error. Mock the Gemini API client using `pytest-mock`. Write DRF API tests for `POST /api/v1/chat/message/` covering: valid request, missing `session_id`, empty message.

**Prompt 6B — Kafka Sentiment Pipeline**
> Set up the Kafka sentiment pipeline. Create a Django management command `start_sentiment_worker` that: starts a `KafkaConsumer` on topic `raw_reviews`, for each message: loads the RoBERTa model (`cardiffnlp/twitter-roberta-base-sentiment`), runs inference on review text, saves result to MySQL `reviews` table with `sentiment_score` and `sentiment_label`, produces to `sentiment_done` topic. Create a separate `trend_aggregator` command that consumes `sentiment_done` and updates `attraction.trend_score` using the formula in PRD Section 10.3.

---

### Prompt Sequence 7: Deployment

**Prompt 7A — Backend Deployment**
> Provide step-by-step commands to deploy the Django backend on AWS EC2 Ubuntu 22.04 without Docker: (1) install Python 3.11, pip, venv, nginx, redis-server; (2) clone repo, create venv, install requirements; (3) set up `.env` with production values; (4) run `collectstatic`, `migrate`; (5) create the systemd service file for Gunicorn as specified in PRD Section 13.2; (6) configure Nginx as a reverse proxy to Gunicorn socket; (7) install certbot and configure Let's Encrypt SSL; (8) enable and start all services; (9) set up a cron job to run the sentiment scraper every 6 hours.

**Prompt 7B — Frontend Deployment**
> Provide commands to build and deploy the Next.js frontend on the same EC2 instance: install Node.js 20 LTS via nvm; `npm install && npm run build`; create systemd service for the Next.js production server on port 3000; configure Nginx to proxy `/` to port 3000 and `/api/` to Gunicorn socket (as per Section 13.4). Ensure Next.js environment variables are set correctly for production API URL.

---

*End of Document — CS/2020/055 — Gautham B.K — University of Kelaniya — August 2025*
