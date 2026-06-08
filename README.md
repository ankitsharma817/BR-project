# 🔍 BR Matching System

> **AI-Powered Intelligent Proposal Evaluation Platform**  
> Automatically match vendor proposals against business requirements using semantic AI, neural reranking, and LLM-generated explanations.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.2-61DAFB?style=flat&logo=react)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=flat&logo=postgresql)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7.2-DC382D?style=flat&logo=redis)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=flat&logo=celery)](https://docs.celeryq.dev)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat)](LICENSE)

---

## 📋 Table of Contents

- [What It Does](#-what-it-does)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Frontend Pages](#-frontend-pages)
- [AI Models](#-ai-models)
- [Database Schema](#-database-schema)
- [Celery Workers](#-celery-workers)
- [Export Reports](#-export-reports)
- [Webhooks](#-webhooks)
- [Security](#-security)
- [Testing](#-testing)
- [Deployment](#-deployment)

---

## 🎯 What It Does

Organizations receive dozens of vendor proposals in response to a Business Requirement (BR) document. Evaluating them manually takes weeks, is error-prone, and is subjective.

**BR Matching System** automates this entire pipeline:

```
BR Document (PDF/DOCX)          Vendor Proposals (PDF/DOCX)
       │                                    │
       ▼                                    ▼
Extract Requirements              Extract Features
Categorize & Prioritize           Map to Categories
Generate Embeddings               Generate Embeddings
       │                                    │
       └──────────── AI Matching ───────────┘
                          │
              ┌───────────▼───────────┐
              │   Cosine Similarity   │
              │   Cross-Encoder Rerank│
              │   LLM Explanations    │
              └───────────┬───────────┘
                          ▼
            Overall Score: 87.5%
            ├── Functional:   89.2%
            ├── Technical:    85.6%
            ├── Compliance:   88.1%
            ├── Security:     91.3%
            ├── Timeline:     82.4%
            ├── Resource:     84.7%
            └── Deliverables: 87.8%
```

### Scoring Labels

| Score | Label | Meaning |
|-------|-------|---------|
| 80–100% | ✅ Strong Match | Requirement fully met |
| 60–79% | ⚠️ Partial Match | Partially addressed |
| 30–59% | 🔶 Gap Identified | Related but insufficient |
| 0–29% | ❌ Missing | Not addressed at all |

### Business Impact

| | Manual Process | BR Match |
|--|--|--|
| **Time** | 30–40 days | 7 days |
| **Error Rate** | High (subjective) | Low (AI-objective) |
| **Bias** | Evaluator bias | Neutral scoring |
| **Reports** | Manual spreadsheets | Auto PDF + Excel |
| **Auditability** | None | Full audit trail |

---

## 🛠 Tech Stack

### Backend
| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Framework | **FastAPI** | 0.109.0 | REST API, async routes |
| Language | **Python** | 3.12 | Core language |
| Server | **Uvicorn** | 0.27.0 | ASGI server |
| ORM | **SQLAlchemy** | 2.0.23 | Database abstraction |
| Migrations | **Alembic** | 1.13.1 | Schema versioning |
| Queue | **Celery** | 5.3.6 | Async task processing |
| Cache | **Redis** | 7.2.3 | Session cache, rate limiting, blacklist |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **React** | 18.2 | UI framework |
| **TypeScript** | 5.3 | Type-safe JavaScript |
| **Ant Design** | 5.x | UI component library |
| **Vite** | 5.1 | Build tool |
| **Axios** | 1.6 | API client with interceptors |
| **React Router** | 6.x | Client-side routing |

### AI / ML
| Model | Purpose | Performance |
|-------|---------|-------------|
| **BAAI/bge-small-en-v1.5** | 384-dim semantic embeddings | 500+ texts/sec on GPU |
| **cross-encoder/ms-marco** | Neural reranking | 100+ comparisons/sec |
| **Qwen2.5-14B-Instruct** | LLM explanations | FP16, 10-20 tokens/sec |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| **PostgreSQL 16** | Primary database |
| **Redis 7.2** | Cache, Celery broker/backend, token blacklist |
| **NVIDIA L4 GPU** | 24GB VRAM — all AI inference |
| **Flower** | Celery monitoring dashboard |
| **ReportLab** | PDF generation |
| **OpenPyXL** | Excel generation |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                        │
│                    Port 3000 → proxy to 8000                    │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP / JSON
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Application (Port 8000)                │
│                  4 Uvicorn Workers                              │
├─────────────────────────────────────────────────────────────────┤
│  Middleware Stack:                                              │
│  GZip → SecurityHeaders → RequestLogger → RedisRateLimit → CORS│
├─────────────────────────────────────────────────────────────────┤
│  Routes:                                                        │
│  /auth  /br-projects  /proposals  /matching  /feedback          │
│  /search  /analytics  /export  /webhooks  /admin  /tasks        │
├─────────────────────────────────────────────────────────────────┤
│  Services:                                                      │
│  AuthService  FileService  EmbeddingService  MatchingService    │
│  FeedbackService  AdminService  EmailService  TokenBlacklist    │
└──────┬──────────┬──────────┬──────────┬──────────┬─────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
  PostgreSQL   Redis      NVIDIA     Upload     Celery
  Port 5432   Port 6379   L4 GPU     Files      Workers
                        (24GB VRAM)
                         │
               ┌─────────┼────────────┐
               ▼         ▼            ▼
          Embeddings  Reranker      Qwen LLM
          (BAAI)   (ms-marco)  (14B, FP16)

┌─────────────────────────────────────────────────────────────────┐
│                    Celery Workers                               │
│  Queue: matching   → run_matching_task (GPU inference)         │
│  Queue: embedding  → embed_br/proposal_requirements_task       │
│  Queue: email      → send_email_task (SMTP)                    │
│  Queue: webhooks   → fire_event_task (HMAC signed HTTP POST)   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
br-match/
│
├── api/                          # FastAPI backend
│   ├── main.py                   # App factory, middleware, router registration
│   ├── config.py                 # Settings (pydantic-settings + .env)
│   ├── database.py               # SQLAlchemy engine + session factory
│   ├── dependencies.py           # JWT guard, DB injection, blacklist check
│   │
│   ├── models/                   # SQLAlchemy ORM models (17 tables)
│   │   ├── user.py               # User, Session, LoginAttempt
│   │   ├── br.py                 # BRProject, BRDocument, BRRequirement
│   │   ├── proposal.py           # Proposal, ProposalRequirement
│   │   ├── matching.py           # MatchingResult, RequirementMatching, MatchAnalysis, MatchHistory
│   │   ├── feedback.py           # Feedback, AILearningLog
│   │   ├── audit.py              # AuditLog
│   │   └── webhook.py            # Webhook, WebhookDelivery
│   │
│   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── auth.py               # Login, Register, Token, PasswordReset
│   │   ├── br.py                 # BR CRUD + Requirement schemas
│   │   ├── proposal.py           # Proposal upload + detail schemas
│   │   ├── matching.py           # MatchingResult, Analysis, Compare schemas
│   │   ├── feedback.py           # Feedback CRUD schemas
│   │   └── common.py             # ApiResponse<T>, PaginatedResponse<T>
│   │
│   ├── routes/                   # API route handlers (10 files)
│   │   ├── auth.py               # /auth/* — login, logout, profile, refresh
│   │   ├── br.py                 # /br-projects/* — CRUD + doc upload + requirements
│   │   ├── proposals.py          # /br-projects/{id}/proposals — upload + manage
│   │   ├── matching.py           # /proposals/{id}/match|analysis|history|compare
│   │   ├── feedback.py           # /proposals/{id}/feedback — submit, update
│   │   ├── admin.py              # /dashboard, /admin/* — stats, audit, AI learning
│   │   ├── export.py             # /proposals/{id}/export — PDF + Excel
│   │   ├── search.py             # /search, /match/filter, /proposals/ranked
│   │   ├── analytics.py          # /analytics/* — trends, distribution, leaderboard
│   │   └── webhooks.py           # /webhooks — CRUD + delivery log + test
│   │
│   ├── services/                 # Business logic layer (8 services)
│   │   ├── auth_service.py       # Login, JWT, lockout, refresh, password
│   │   ├── file_service.py       # PDF/DOCX extraction, storage, dedup
│   │   ├── embedding_service.py  # BAAI embeddings, cosine similarity, reranking
│   │   ├── matching_service.py   # Full AI matching pipeline
│   │   ├── feedback_service.py   # Score corrections, quality metrics
│   │   ├── admin_service.py      # Dashboard stats, health checks, audit
│   │   ├── email_service.py      # SMTP + console fallback, reset tokens
│   │   ├── token_blacklist.py    # Redis JWT blacklist
│   │   └── export/
│   │       ├── pdf_export.py     # ReportLab PDF reports
│   │       └── excel_export.py   # OpenPyXL Excel reports + comparison
│   │
│   ├── tasks/                    # Celery async tasks (4 queues)
│   │   ├── celery_app.py         # Celery config, queue routing
│   │   ├── matching_tasks.py     # run_matching_task, recalculate_all_for_br
│   │   ├── embedding_tasks.py    # embed_br/proposal_requirements_task
│   │   ├── email_tasks.py        # welcome, reset, match-complete, lockout emails
│   │   └── webhook_tasks.py      # fire_event_task (HMAC-SHA256 delivery)
│   │
│   ├── middleware/               # Custom middleware (5 layers)
│   │   ├── logging.py            # Request/response timing logger
│   │   ├── error_handler.py      # Global exception → JSON responses
│   │   ├── security_headers.py   # CSP, HSTS, X-Frame-Options, etc.
│   │   ├── redis_rate_limiter.py # Sliding-window, 100 req/min per IP
│   │   └── rate_limiter.py       # In-memory fallback rate limiter
│   │
│   └── utils/
│       ├── constants.py          # Enums, score thresholds, category weights
│       ├── validators.py         # Email, password, score, file, pagination
│       └── security.py           # bcrypt, JWT encode/decode, reset tokens
│
├── alembic/                      # Database migrations
│   ├── env.py                    # Migration environment
│   ├── script.py.mako            # Migration template
│   └── versions/
│       ├── 001_initial_schema.py # All 15 Phase 1 tables
│       └── 002_phase2_tables.py  # Webhook tables
│
├── frontend/                     # React 18 + TypeScript + Ant Design
│   ├── src/
│   │   ├── main.tsx              # React entry point
│   │   ├── App.tsx               # Router + protected routes
│   │   ├── index.css             # Global styles
│   │   ├── types/index.ts        # Full TypeScript type definitions
│   │   ├── api/client.ts         # Axios client + interceptors + all API calls
│   │   ├── store/AuthContext.tsx # JWT auth state + login/logout
│   │   ├── components/
│   │   │   ├── AppLayout.tsx     # Sidebar nav + header + user menu
│   │   │   ├── ProtectedRoute.tsx# JWT-guarded route wrapper
│   │   │   └── ScoreBadge.tsx    # Color-coded score tag/progress
│   │   └── pages/
│   │       ├── Login.tsx         # Login form with error handling
│   │       ├── Dashboard.tsx     # Stats, health, activity (30s auto-refresh)
│   │       ├── BRList.tsx        # BR projects table with search + filter
│   │       ├── BRCreate.tsx      # New BR form + document upload
│   │       ├── BRDetails.tsx     # Requirements + proposals tabbed view
│   │       ├── ProposalUpload.tsx# Drag-drop upload + vendor metadata
│   │       ├── MatchingAnalysis.tsx # Score circles, risks, req breakdown
│   │       ├── ComparisonView.tsx# Side-by-side proposal comparison
│   │       └── AdminPanel.tsx    # Health, feedback, AI stats, audit logs
│   ├── package.json
│   ├── vite.config.ts            # Dev proxy → :8000
│   └── tsconfig.json
│
├── tests/                        # Full test suite (~90 test cases)
│   ├── conftest.py               # SQLite fixtures, TestClient, user/token fixtures
│   ├── unit/
│   │   ├── test_auth_service.py  # Password hashing, JWT, login/lockout/refresh
│   │   ├── test_validators.py    # Email, password strength, score, pagination
│   │   ├── test_matching_service.py # Extraction, classification, scoring, labels
│   │   └── test_file_service.py  # Text extraction, file hashing
│   ├── integration/
│   │   ├── test_auth_api.py      # All auth endpoints end-to-end
│   │   ├── test_br_api.py        # BR CRUD + requirements CRUD
│   │   ├── test_proposals_api.py # Upload, list, delete + file validation
│   │   └── test_feedback_api.py  # Submit, update, score correction
│   └── load/
│       └── test_performance.py   # Latency budgets, concurrency, throughput
│
├── scripts/
│   ├── start_api.sh              # Linux: migrate + start uvicorn
│   ├── start_api.ps1             # Windows: migrate + start uvicorn
│   ├── start_workers.sh          # Linux: start all 4 Celery queues + Flower
│   └── start_workers.ps1         # Windows: start workers in separate terminals
│
├── .env.example                  # All environment variable templates
├── alembic.ini                   # Alembic configuration
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Dev + test dependencies
└── pytest.ini                   # Test configuration
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 16
- Redis 7.2
- (Optional) NVIDIA GPU with CUDA 13.2

### 1. Clone & Setup

```bash
git clone https://github.com/ankitsharma817/BR-project.git
cd BR-project

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
.\venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database credentials and settings
```

### 3. Database Setup

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE USER br_matching WITH PASSWORD 'yourpassword';"
psql -U postgres -c "CREATE DATABASE br_matching_db OWNER br_matching;"

# Run migrations
alembic upgrade head
```

### 4. Start the API

```bash
# Linux/Mac
bash scripts/start_api.sh

# Windows
.\scripts\start_api.ps1

# Or manually
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start Celery Workers

```bash
# Linux/Mac
bash scripts/start_workers.sh

# Windows (opens separate terminals)
.\scripts\start_workers.ps1
```

### 6. Start the Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 7. Access the App

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **API Docs** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/health |
| **Flower (Celery)** | http://localhost:5555 |

---

## ⚙️ Environment Variables

```env
# Application
APP_NAME=BR Matching System
APP_VERSION=1.0.0
DEBUG=false

# Security — CHANGE THIS IN PRODUCTION
SECRET_KEY=replace-with-a-long-random-secret-key-at-least-32-chars

# Database
DATABASE_URL=postgresql://br_matching:password@localhost:5432/br_matching_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://localhost:6379/0

# File Storage
UPLOAD_DIR=uploads
MAX_FILE_SIZE_MB=50

# AI Models (auto-downloaded on first run)
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
LLM_MODEL=Qwen/Qwen2.5-14B-Instruct
MODEL_CACHE_DIR=.model_cache

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Email (optional — logs to console if not set)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@email.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@brmatch.local
```

---

## 📡 API Reference

All endpoints are prefixed with `/api/v1`. Full interactive docs at `/docs`.

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Create new account |
| `POST` | `/auth/login` | Login → returns access + refresh tokens |
| `POST` | `/auth/logout` | Revoke session + blacklist access token |
| `POST` | `/auth/refresh-token` | Get new access token |
| `GET`  | `/auth/profile` | Get current user profile |
| `POST` | `/auth/request-password-reset` | Send reset email |
| `POST` | `/auth/reset-password` | Reset with token |

### BR Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/br-projects` | Create BR project |
| `GET`  | `/br-projects` | List all BR projects (paginated) |
| `GET`  | `/br-projects/{id}` | Get BR project + requirements |
| `PUT`  | `/br-projects/{id}` | Update BR project |
| `DELETE` | `/br-projects/{id}` | Soft delete |
| `POST` | `/br-projects/{id}/documents` | Upload BR document (auto-extracts requirements) |
| `GET`  | `/br-projects/{id}/requirements` | List requirements |
| `POST` | `/br-projects/{id}/requirements` | Add manual requirement |
| `PUT`  | `/br-projects/{id}/requirements/{req_id}` | Edit requirement |
| `DELETE` | `/br-projects/{id}/requirements/{req_id}` | Delete requirement |

### Proposals

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/br-projects/{id}/proposals` | Upload proposal (triggers async matching) |
| `GET`  | `/br-projects/{id}/proposals` | List proposals with scores |
| `GET`  | `/br-projects/{id}/proposals/{pid}` | Get proposal detail |
| `DELETE` | `/br-projects/{id}/proposals/{pid}` | Soft delete |
| `GET`  | `/br-projects/{id}/proposals/ranked` | Proposals sorted by score |

### Matching

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/proposals/{id}/match` | Full matching result + breakdown |
| `GET`  | `/proposals/{id}/analysis` | Risks, recommendations, gaps |
| `POST` | `/proposals/{id}/recalculate` | Re-run matching pipeline |
| `GET`  | `/proposals/{id}/history` | Score version history |
| `POST` | `/proposals/compare` | Compare multiple proposals |
| `GET`  | `/proposals/{id}/match/filter` | Filter by label/category/score |

### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/proposals/{id}/export?format=pdf` | Download PDF report |
| `GET`  | `/proposals/{id}/export?format=excel` | Download Excel report |
| `GET`  | `/proposals/compare/export?ids=id1,id2` | Comparison Excel workbook |

### Search & Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/search?q=...&type=br\|proposal\|all` | Global full-text search |
| `GET`  | `/analytics/overview?days=30` | System-wide trends |
| `GET`  | `/analytics/br/{id}/summary` | Per-BR stats + coverage |
| `GET`  | `/analytics/score-distribution` | Score histogram |
| `GET`  | `/analytics/vendor-performance` | Cross-BR vendor leaderboard |

### Feedback

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/proposals/{id}/feedback` | Submit feedback + score correction |
| `GET`  | `/proposals/{id}/feedback` | List all feedback |
| `PUT`  | `/proposals/{id}/feedback/{fid}` | Update feedback |
| `POST` | `/feedback/{id}/mark-useful` | Mark feedback as useful |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/dashboard` | System-wide statistics |
| `GET`  | `/dashboard/system-health` | DB, Redis, GPU status |
| `GET`  | `/dashboard/activities` | Recent activity feed |
| `GET`  | `/admin/audit-logs` | Paginated audit trail |
| `GET`  | `/admin/feedback-quality-report` | Feedback metrics |
| `GET`  | `/admin/ai-learning/stats` | Score correction analytics |

### Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/webhooks` | Register webhook (returns secret once) |
| `GET`  | `/webhooks` | List your webhooks |
| `PUT`  | `/webhooks/{id}` | Update URL/events/active status |
| `DELETE` | `/webhooks/{id}` | Delete webhook |
| `GET`  | `/webhooks/{id}/deliveries` | Last 50 delivery attempts |
| `POST` | `/webhooks/{id}/test` | Send test delivery |

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/tasks/{task_id}` | Poll Celery task status |

---

## 🖥 Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| **Login** | `/login` | JWT auth, error handling, redirect |
| **Dashboard** | `/dashboard` | Stats cards, system health, activity feed (30s refresh) |
| **BR List** | `/br-projects` | Search, filter by status, paginated CRUD table |
| **BR Create** | `/br-projects/new` | Form + drag-drop document upload |
| **BR Details** | `/br-projects/:id` | Tabbed: requirements CRUD + proposals table |
| **Proposal Upload** | `/br-projects/:brId/upload-proposal` | Drag-drop, vendor metadata, progress indicator |
| **Matching Analysis** | `/proposals/:id/analysis` | Score circles, risks, recommendations, requirement breakdown, feedback modal |
| **Comparison View** | `/comparison` | Select proposals → side-by-side category chart, winner badge |
| **Admin Panel** | `/admin` | Health, feedback quality, AI learning stats, audit logs |

---

## 🤖 AI Models

### 1. BAAI/bge-small-en-v1.5 (Embeddings)
- Converts text → 384-dimensional semantic vectors
- Enables meaning-based matching (not just keywords)
- "OAuth 2.0 auth" ≈ "OpenID Connect" = matched ✅
- **Performance:** 500+ texts/sec on NVIDIA L4

### 2. cross-encoder/ms-marco (Reranking)
- Takes (requirement, proposal) pairs and scores them
- More accurate than embeddings alone
- Blended score = 40% embedding + 60% reranker
- **Performance:** 100+ comparisons/sec

### 3. Qwen2.5-14B-Instruct (LLM Explanations)
- Generates human-readable match explanations
- Runs in FP16 precision (fits in 24GB VRAM)
- Optional — falls back to rule-based explanations
- **Performance:** 10-20 tokens/sec

### Score Calculation

```
Category Score = average(best_match_score per BR requirement in category)

Overall Score = Σ (category_score × category_weight)

Weights:
  Functional:   25%
  Technical:    20%
  Compliance:   15%
  Security:     15%
  Timeline:     10%
  Resource:      8%
  Deliverables:  7%
```

---

## 🗄 Database Schema

17 tables across 5 domains:

```
Users & Auth          BR Projects           Proposals
─────────────         ────────────          ─────────────
users                 br_projects           proposals
sessions              br_documents          proposal_requirements
login_attempts        br_requirements

Matching              Feedback & Audit      Webhooks
────────              ────────────────      ────────
matching_results      feedbacks             webhooks
requirement_matchings ai_learning_logs      webhook_deliveries
match_analyses        audit_logs
match_histories
```

All tables use:
- UUID primary keys (`uuid-ossp`)
- `created_at` / `updated_at` timestamps
- Soft deletes (`is_deleted`) where applicable
- JSONB for embeddings and flexible data

---

## ⚙️ Celery Workers

4 dedicated queues for different workloads:

```
Queue: matching     concurrency=2   GPU-intensive matching pipeline
Queue: embedding    concurrency=1   Single GPU embedding generation
Queue: email        concurrency=4   SMTP delivery with retry
Queue: webhooks     concurrency=4   HMAC-signed HTTP delivery with retry
```

### Task Retry Policy

| Task | Max Retries | Retry Delay |
|------|------------|-------------|
| `run_matching_task` | 3 | 30 seconds |
| `send_email_task` | 3 | 60 seconds |
| `fire_event_task` | 3 | 60 seconds |

### Monitor Workers

Flower dashboard at **http://localhost:5555** shows:
- Active/queued/failed tasks
- Worker status and load
- Task history and timing

---

## 📊 Export Reports

### PDF Report (ReportLab)
- Overall score with color coding
- Category score table
- Executive summary
- Risks & recommendations
- Requirement-by-requirement breakdown

### Excel Report (OpenPyXL)
- **Sheet 1: Summary** — overall score, category scores
- **Sheet 2: Requirements** — full breakdown with color-coded scores
- **Sheet 3: Analysis** — risks, recommendations, strengths, gaps
- **Comparison workbook** — multiple vendors side-by-side

---

## 🔔 Webhooks

Register a webhook to receive real-time event notifications:

```bash
POST /api/v1/webhooks
{
  "url": "https://your-server.com/webhook",
  "events": ["match.completed", "proposal.uploaded"],
  "project_id": "optional-filter-by-project"
}
```

### Supported Events

| Event | When fired |
|-------|-----------|
| `match.completed` | AI matching pipeline finishes |
| `proposal.uploaded` | New proposal uploaded |
| `proposal.failed` | Matching pipeline fails |
| `br.created` | New BR project created |
| `br.deleted` | BR project deleted |
| `score.threshold_crossed` | Score crosses a threshold |

### Signature Verification

Every delivery includes a signature header:

```
X-BRMatch-Event: match.completed
X-BRMatch-Signature: sha256=<hmac-sha256-hex>
```

Verify in your server:
```python
import hmac, hashlib
expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
assert hmac.compare_digest(expected, request.headers["X-BRMatch-Signature"])
```

---

## 🔒 Security

| Feature | Implementation |
|---------|---------------|
| **Password Hashing** | bcrypt (salted, slow) |
| **Authentication** | JWT (access 60min + refresh 7 days) |
| **Token Blacklist** | Redis SET — revoked on logout |
| **Rate Limiting** | Redis sliding window — 100 req/min/IP |
| **Account Lockout** | 5 failed attempts → 30min lockout + email alert |
| **Security Headers** | CSP, HSTS, X-Frame-Options, X-Content-Type-Options |
| **File Validation** | Extension + MIME type + size (max 50MB) |
| **SQL Injection** | Prevented by SQLAlchemy ORM |
| **XSS** | React escapes by default + CSP header |
| **Webhook Integrity** | HMAC-SHA256 signature on all deliveries |

---

## 🧪 Testing

### Run All Tests

```bash
pip install -r requirements-dev.txt

# Unit tests (fast, no DB needed)
pytest tests/unit/ -v

# Integration tests (SQLite in-memory, no Postgres needed)
pytest tests/integration/ -v

# Load / performance tests
pytest tests/load/ -v

# All tests
pytest -v
```

### Test Coverage

| Suite | Tests | What's Covered |
|-------|-------|---------------|
| **Unit** | ~40 | Password hashing, JWT, validators, requirement extraction, classification, scoring |
| **Integration** | ~35 | All auth endpoints, BR CRUD, requirements CRUD, proposal upload, feedback |
| **Load** | ~6 | P95 latency budgets, concurrent requests, throughput |

### Performance Budgets

| Endpoint | P95 Target |
|----------|-----------|
| `GET /health` | < 200ms |
| `GET /br-projects` | < 500ms |
| Concurrent BR creates (20) | 0 failures |
| Concurrent logins (25) | ≥ 20 success |
| Proposal upload | < 3s each |

---

## 🚢 Deployment

### Development

```bash
# API with hot reload
uvicorn api.main:app --reload --port 8000

# Frontend with HMR
cd frontend && npm run dev
```

### Production (Linux)

```bash
# 1. Set environment variables
export DATABASE_URL=postgresql://...
export SECRET_KEY=your-production-secret
export REDIS_URL=redis://...

# 2. Run migrations
alembic upgrade head

# 3. Start API (4 workers)
bash scripts/start_api.sh

# 4. Start Celery workers
bash scripts/start_workers.sh

# 5. Build frontend
cd frontend && npm run build
# Serve dist/ with nginx or caddy
```

### Windows

```powershell
# API
.\scripts\start_api.ps1

# Workers (opens 4 terminal windows)
.\scripts\start_workers.ps1
```

---

## 📈 Project Stats

| Metric | Count |
|--------|-------|
| Total files | 114 |
| Lines of code | ~8,000 |
| API endpoints | 45+ |
| Database tables | 17 |
| Frontend pages | 9 |
| React components | 12 |
| Test cases | ~90 |
| Celery tasks | 8 |
| Webhook events | 6 |
| Git commits | 3 |

---

## 🗓 Development Phases

| Phase | Status | What was built |
|-------|--------|---------------|
| **Phase 1 — Backend** | ✅ Complete | FastAPI routes, services, ORM models, schemas, middleware, JWT auth |
| **Phase 2 — Frontend** | ✅ Complete | React 9-page SPA, typed API client, auth context, Ant Design UI |
| **Phase 3 — Tests** | ✅ Complete | Unit + integration + load test suites |
| **Phase 4 — Production** | ✅ Complete | Alembic, Celery, Export, Email, Security hardening, Search, Analytics, Webhooks |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Ankit Sharma**  
GitHub: [@ankitsharma817](https://github.com/ankitsharma817)  
Repo: [BR-project](https://github.com/ankitsharma817/BR-project)

---

<div align="center">
  <sub>Built with ❤️ using FastAPI, React, and AI</sub>
</div>
