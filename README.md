# ModelSwitch Chat

> A resilient full-stack LLM chat application with automatic API-key failover, response caching, multi-turn session history, and per-request token tracking.

<p align="center">

**Live Demo:** https://modelswitch-chat.vercel.app/

**Backend API:** https://modelswitch-chat.onrender.com

</p>

---

## Live URLs

- **Frontend:** https://modelswitch-chat.vercel.app/
- **Backend:** https://modelswitch-chat.onrender.com
- **Health:** https://modelswitch-chat.onrender.com/health

The frontend is deployed on Vercel and communicates with the FastAPI backend deployed on Render.

---

## Demo Video

🎥 **[Watch the 6 minute demo on YouTube](https://youtu.be/LcUbepOmhIQ)**

The demo covers:

- Live LLM inference and response metadata
- Multi-turn session memory
- Cross-session response caching
- Automatic API-key failover
- Complete provider failure handling
- Health check
- Session history


---

## Overview

ModelSwitch Chat is a full-stack LLM chat application designed around **resilience and efficient inference**.

Instead of depending on a single API key, the backend maintains an ordered pool of LLM keys and automatically falls back to the next key when a provider request fails.

The application also uses LiteLLM caching to avoid unnecessary repeated inference and SQLite to maintain multi-turn conversation history.

### Core capabilities

- 🔄 Automatic API-key failover
- ⚡ Response caching with LiteLLM
- 💬 Multi-turn conversation history
- 📊 Per-request token tracking
- 🩺 Health monitoring
- 🧪 Controlled failure simulation
- 🐳 Docker and Docker Compose support
- 🚀 Vercel + Render deployment

---

## Architecture

```text
                         ┌─────────────────────┐
                         │    React + Vite     │
                         │       Vercel        │
                         └──────────┬──────────┘
                                    │ HTTPS
                                    ▼
                         ┌─────────────────────┐
                         │   FastAPI Backend   │
                         │       Render        │
                         └──────────┬──────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
           ┌──────────┐      ┌────────────┐    ┌───────────┐
           │  SQLite  │      │  LiteLLM   │    │  Config   │
           │ Sessions │      │   Cache    │    │ + Failure │
           │ & History│      │            │    │ Simulation│
           └──────────┘      └─────┬──────┘    └───────────┘
                                   │
                                   ▼
                              ┌─────────────┐
                              │  LLM Keys   │
                              │   key_1     │
                              │      ↓      │
                              │   key_2     │
                              └──────┬──────┘
                                     │
                                     ▼
                                  ┌───────┐
                                  │ Groq  │
                                  └───────┘
```

---

## Resilience Flow

Every chat request follows this general flow:

```text
                     Incoming Request
                            │
                            ▼
                    Load Session History
                            │
                            ▼
                       Cache Lookup
                       /          \
                    HIT            MISS
                     │               │
                     ▼               ▼
                Return Cache      Try key_1
                                     │
                                ┌────┴────┐
                             Success    Failure
                                │           │
                                │           ▼
                                │        Try key_2
                                │           │
                                │      ┌────┴────┐
                                │   Success    Failure
                                │      │           │
                                └──────┴──────┐     ▼
                                              │    503
                                              ▼
                                      Save Conversation
                                              │
                                              ▼
                                      Return Metadata
```

Provider failures such as `429`, `500`, `502`, and `503` trigger the next configured key.

If all configured keys fail, the backend returns HTTP `503`.

---

## Key Features

### 🔄 Automatic API-Key Failover

LLM API keys are attempted in a deterministic order.

For example:

```text
key_1
  │
  ├── success ──► response
  │
  └── failure ──► key_2
                    │
                    ├── success ──► response
                    │
                    └── failure ──► 503
```

The response metadata exposes:

- `key_id`
- `fallback_attempts`

This makes failover behavior observable rather than hidden.

---

### ⚡ Response Caching

LiteLLM caching is used to avoid repeated inference for identical requests.

The cache identity is based on:

```text
model + complete message list
```

The session ID is intentionally **not** part of the cache identity.

Therefore, the same initial prompt from a different session can still produce:

```text
resolution_source = LLM_CACHE
```

A request requiring actual model inference reports:

```text
resolution_source = LIVE_INFERENCE
```

Cache lookup occurs before failure simulation/failover, so an already-cached response does not require another provider request.

---

### 💬 Multi-Turn Sessions

Each browser session receives a session ID.

Conversation messages are persisted in SQLite and loaded when processing subsequent messages.

This allows interactions such as:

```text
User: My name is Deepanshu.

Assistant: Nice to meet you, Deepanshu.

User: What is my name?

Assistant: Your name is Deepanshu.
```

Sessions are isolated from one another.

---

### 📊 Token & Request Metadata

Successful chat responses expose:

| Field | Description |
|---|---|
| `resolution_source` | `LIVE_INFERENCE` or `LLM_CACHE` |
| `model` | Model used for the response |
| `latency_ms` | Request latency |
| `input_tokens` | Input token count |
| `output_tokens` | Output token count |
| `key_id` | Provider key used for live inference |
| `fallback_attempts` | Number of failed provider attempts |

---

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Backend health and configuration status |
| `POST` | `/chat` | Generate a response for a session |
| `GET` | `/sessions/{session_id}/messages` | Retrieve session history |

### `GET /health`

Example response:

```json
{
  "status": "ok",
  "keys_configured": 2,
  "cache_enabled": true
}
```

### `POST /chat`

Request:

```json
{
  "session_id": "example-session",
  "message": "Explain what an API is."
}
```

A successful response contains the generated reply together with request metadata.

### `GET /sessions/{session_id}/messages`

Returns the stored messages for a session.

An unknown session returns HTTP `404`.

---

## Failure Simulation

Failure simulation is controlled by:

```env
ENABLE_FAILURE_SIMULATION=true
```

It is intended for testing resilience without intentionally causing real provider failures.

### Simulate key 1 failure

```http
X-Simulate-Failure: key_1=429
```

Expected behavior:

```text
key_1 → simulated 429
       ↓
key_2 → successful inference
```

The response reports:

```text
key_id = key_2
fallback_attempts = 1
```

### Simulate failure for every key

```http
X-Simulate-Failure: *=429
```

Expected result:

```text
HTTP 503
```

Failed requests are not written to conversation history and are not cached as successful responses.

---

## Verification

The implementation was verified locally, inside Docker, and against the deployed backend/frontend.

### Health Check

The live backend was verified successfully:

```json
{
  "status": "ok",
  "keys_configured": 2,
  "cache_enabled": true
}
```

### Normal Chat

A live chat request successfully returned:

- Generated assistant response
- `LIVE_INFERENCE`
- Model name
- Latency
- Input tokens
- Output tokens
- Key ID
- Fallback attempts

### Multi-Turn Memory

The same session was used for multiple messages.

The assistant successfully referenced information from previous messages.

A separate session did not have access to the previous session's history.

### Cross-Session Cache

The same initial prompt was sent from a different session.

Results:

```text
First request:
resolution_source = LIVE_INFERENCE

Second session:
resolution_source = LLM_CACHE
```

The cached request also demonstrated significantly lower latency.

### API-Key Failover

With:

```http
X-Simulate-Failure: key_1=429
```

the verified result was:

```text
HTTP 200
key_id: key_2
fallback_attempts: 1
resolution_source: LIVE_INFERENCE
```

### Total Provider Failure

With:

```http
X-Simulate-Failure: *=429
```

the verified result was:

```text
HTTP 503
```

with:

```json
{
  "detail": "all providers unavailable"
}
```

The failed request was not persisted in session history.

### Session History

Successful conversation history was retrieved through:

```text
GET /sessions/{session_id}/messages
```

Unknown sessions returned HTTP `404`.

### Automated Tests

The backend test suite passed successfully with:

```text
13 passed
```

The test suite covers:

- Chat behavior
- Multi-turn sessions
- Session isolation
- Key failover
- Failure simulation
- Response caching
- Error handling

---

## Tech Stack Used

### Frontend

- React
- Vite
- JavaScript
- CSS

### Backend

- Python
- FastAPI
- Uvicorn
- LiteLLM
- SQLite
- python-dotenv

### Infrastructure

- Docker
- Docker Compose
- Nginx
- Vercel
- Render

### LLM Provider

- Groq
- `openai/gpt-oss-120b`

### Testing

- Pytest
- Docker-based integration testing
- Manual API verification
- Live deployment verification

---

## Run locally

### Docker

#### 1. Clone the repository

```bash
git clone https://github.com/Deepanshugupta8772/modelswitch-chat.git
cd modelswitch-chat
```

#### 2. Configure environment variables

Create a `.env` file in the project root:

```env
LLM_API_KEYS=key_1,key_2
LLM_MODEL=groq/openai/gpt-oss-120b
DATABASE_URL=sqlite:////data/app.db
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
ENABLE_FAILURE_SIMULATION=true
CACHE_ENABLED=true
```

Replace `key_1,key_2` with your own LLM API keys.

**Never commit `.env` or real API keys.**

#### 3. Start the application

```bash
docker compose up --build -d
```

The application will be available at:

```text
Frontend → http://localhost:3000
Backend  → http://localhost:8000
Health   → http://localhost:8000/health
```

Check running containers:

```bash
docker compose ps
```

Stop the application:

```bash
docker compose down
```

---

### Without Docker

#### Backend

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r backend/requirements.txt
```

Configure the required environment variables in `.env`.

Start FastAPI:

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

#### Frontend

Open another terminal:

```powershell
cd frontend
npm install
npm run dev
```

The Vite development server normally runs at:

```text
http://localhost:5173
```

Set:

```env
VITE_API_URL=http://localhost:8000
```

for local frontend-to-backend communication.

---

## Project Structure

```text
ModelSwitch-Chat/
│
├── backend/
│   ├── app/
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── llm.py
│   │   ├── main.py
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── simulate.py
│   │
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .dockerignore
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   │
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
├── Makefile
├── .env.example
├── .gitignore
└── README.md
```

---

## Bonus features

In addition to the core requirements, the implementation includes:

- 🐳 Docker Compose setup for the complete application
- Separate production Dockerfiles for frontend and backend
- Nginx reverse proxy
- Automated backend test suite
- Health check endpoint
- Configurable CORS origins
- Configurable failure simulation
- Non-root backend Docker container
- Environment-based configuration
- Frontend loading state
- Duplicate-send prevention
- Enter-to-send and Shift+Enter for multiline messages
- Response metadata displayed directly in the UI
- Session isolation
- Persistent SQLite volume in Docker Compose
- Production deployment on Vercel and Render

---


## Deployment

### Frontend — Vercel

Production frontend:

```text
https://modelswitch-chat.vercel.app/
```

The Vercel deployment uses:

```env
VITE_API_URL=https://modelswitch-chat.onrender.com
```

No LLM API keys are exposed to the frontend.

### Backend — Render

Production backend:

```text
https://modelswitch-chat.onrender.com
```

The backend uses Render's dynamically assigned `PORT`.

Required backend configuration:

```text
LLM_API_KEYS
LLM_MODEL
DATABASE_URL
ALLOWED_ORIGINS
ENABLE_FAILURE_SIMULATION
```

---

## Deployment Limitation

The application uses SQLite for conversation history.

### Local Docker deployment

Docker Compose mounts SQLite under a named Docker volume, allowing database data to survive normal container recreation.

### Render Free deployment

The current Render Free deployment does **not** provide a persistent disk for the SQLite database.

Therefore, SQLite data on the free production deployment should be considered **ephemeral** and may be lost when the service is recreated or redeployed.

For durable production conversation storage, the backend should be migrated to a managed persistent database such as PostgreSQL or deployed with persistent storage.

---