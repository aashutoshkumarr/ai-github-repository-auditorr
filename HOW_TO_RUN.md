# How to Run the AI GitHub Repository Auditor

There are three ways to run this project:
1. **Quick Start (Windows)** — One-click startup with built-in startup scripts
2. **Local Development** — Manual setup for development/debugging
3. **Production Mode** — Full Docker Compose with Postgres, Redis, MinIO

Choose the one that best fits your needs.

---

## Option 1: Quick Start (Windows) ⚡

The easiest way to run everything on Windows. Just double-click a batch file!

### Prerequisites
- **Python 3.11+** (installed and in PATH)
- **Node.js 20+** (installed and in PATH)
- **Virtual environment already set up** (should exist at `venv/`)

### Run it (3 seconds)
```batch
start_all.bat
```

**What this does:**
- Starts the FastAPI backend on http://localhost:8000
- Starts the Next.js frontend on http://localhost:3000
- Opens both in your browser automatically
- Logs are saved to `logs/backend.log` and `logs/frontend.log`

**To stop everything:**
- Close the console windows or press Ctrl+C in each

---

## Option 2: Local Development (Manual) 🛠️

Run each component separately for debugging and development.

### Prerequisites
- **Python 3.11+** (installed and in PATH)
- **Node.js 20+** (installed and in PATH)
- **Virtual environment** at `venv/` with dependencies installed

### Step 1: Activate Python venv
```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Or command prompt
venv\Scripts\activate.bat
```

### Step 2: Start the backend
```powershell
# From project root
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### Step 3: Start the frontend (in a new terminal)
```powershell
cd frontend
npm run dev
```

Expected output:
```
- Local:        http://localhost:3000
- Environments: .env.local
```

### Step 4: Open in browser
- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Backend Health:** http://localhost:8000/health

---

## Option 3: Production Mode (Docker Compose) 🐳

Full multi-service setup with Postgres, Redis, MinIO, and container sandboxing.

### Prerequisites
- **Docker Desktop** (installed and running)
- **Docker Compose v2** (usually included with Docker Desktop)

### Step 1: Create `.env` file
Create a `.env` file in the project root with these variables:
```env
# Database
DATABASE_URL=postgresql+asyncpg://auditor:auditorpass@postgres:5432/auditor
POSTGRES_PASSWORD=auditorpass

# Redis & Storage
REDIS_URL=redis://redis:6379/0
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=auditor-snapshots

# API & Workers
API_KEYS_RAW=demo-api-key-1,another-key
SANDBOX_ENABLED=false
JOB_VISIBILITY_SECONDS=600
JOB_RECLAIM_INTERVAL_SECONDS=60

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### Step 2: Start infrastructure (Postgres, Redis, MinIO)
```powershell
docker compose -f docker-compose.prod.yml up -d postgres redis minio
```

Wait for them to be healthy (check with `docker compose ps`).

### Step 3: Run database migrations
```powershell
docker compose -f docker-compose.prod.yml run --rm migrate
```

Expected output:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0001_initial, ...
```

### Step 4: Build and start all services
```powershell
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Step 5: Verify all services are running
```powershell
docker compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME              COMMAND                  SERVICE    STATUS
postgres          postgres                 postgres   Up (healthy)
redis             redis-server             redis      Up
minio             minio server             minio      Up
backend           python -m uvicorn ...    backend    Up
worker            python -m backend...     worker     Up
frontend          npm run dev              frontend   Up
```

### Step 6: Open in browser
- **Dashboard:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Metrics:** http://localhost:8000/metrics
- **MinIO Console:** http://localhost:9001 (admin/minioadmin)

### Step 7: Test the system
```powershell
# Enqueue a test audit job
curl -X POST "http://localhost:8000/api/v1/audits" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer demo-api-key-1" `
  -d '{
    "repo_url": "https://github.com/torvalds/linux",
    "options": {"depth": 1}
  }'

# Check job status (replace JOB_ID with the id from above)
curl "http://localhost:8000/api/v1/audits/{JOB_ID}" `
  -H "Authorization: Bearer demo-api-key-1"
```

### Step 8: View logs (if something goes wrong)
```powershell
# Follow all logs
docker compose -f docker-compose.prod.yml logs -f

# Or specific service
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f worker
docker compose -f docker-compose.prod.yml logs -f frontend
```

### Step 9: Stop everything
```powershell
docker compose -f docker-compose.prod.yml down

# To also remove volumes (database data)
docker compose -f docker-compose.prod.yml down -v
```

---

## Verify It's Working

### Quick Health Check
```powershell
# Backend
curl http://localhost:8000/health

# Frontend
curl http://localhost:3000
```

### Run Tests
```powershell
# Activate venv first
.\venv\Scripts\Activate.ps1

# Run backend tests
pytest -v backend/tests

# Run verification script
python scripts/verify_live.py
```

---

## Common Issues & Fixes

### "Python not found"
- Make sure Python 3.11+ is installed: `python --version`
- Add Python to PATH in Windows settings

### "npm: command not found"
- Make sure Node.js 20+ is installed: `node --version` and `npm --version`
- Add Node to PATH in Windows settings

### "Port 8000 already in use"
- Kill the process: `netstat -ano | findstr :8000` then `taskkill /PID <PID> /F`
- Or change BACKEND_PORT in `.env`

### "Port 3000 already in use"
- Kill the process: `netstat -ano | findstr :3000` then `taskkill /PID <PID> /F`
- Or change FRONTEND_PORT in `.env`

### "Virtual environment not found"
- Create it: `python -m venv venv`
- Install deps: `.\venv\Scripts\Activate.ps1` then `pip install -r backend/requirements.txt` and `cd frontend && npm ci`

### "Docker daemon not running"
- Open Docker Desktop application and wait for it to start

### "Postgres connection refused"
- Wait a few seconds for Postgres to initialize
- Check: `docker compose -f docker-compose.prod.yml ps`

---

## API Endpoints (Backend)

Once running, visit http://localhost:8000/docs for interactive API docs. Common endpoints:

- `POST /api/v1/audits` — Submit a repository for audit
- `GET /api/v1/audits/{job_id}` — Get audit job status and results
- `GET /api/v1/audits` — List all audit jobs
- `POST /api/v1/preview` — Get repository summary without full audit
- `GET /health` — Health check
- `GET /metrics` — Prometheus metrics

---

## Frontend Features

Once frontend is running at http://localhost:3000:

- 🎨 **Light/Dark Theme Toggle** — Top-right corner
- 📝 **Paste Repo URL** — Get quick summary: tech stack, risk score, architecture overview
- 🧹 **Audit Dashboard** — View ongoing and completed audits
- 🔧 **Settings** — Configure API keys, worker settings
- 📊 **Risk Graph** — Visual dependency and vulnerability relationships

---

## Next Steps

1. **Explore the API:** http://localhost:8000/docs
2. **Submit an audit:** Paste a GitHub repo URL in the frontend
3. **Check metrics:** http://localhost:8000/metrics (if using Docker Compose)
4. **Read code:** Backend is in `backend/app`, Frontend is in `frontend/`
5. **Scale workers:** In Docker Compose, run multiple worker services

---

## Questions?

- Check `RELEASE_NOTES.md` for deployment details
- Check `CHANGELOG.md` for what's new
- Check `logs/` folder for error messages
- View API docs at http://localhost:8000/docs

Enjoy! 🚀
