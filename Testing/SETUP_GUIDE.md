# MenuVision — Complete Testing & CI/CD Setup Guide

## What's included

```
menuvision/
├── backend/
│   ├── app/                    ← FastAPI application
│   │   ├── core/config.py      ← Settings (env vars)
│   │   ├── core/security.py    ← JWT + bcrypt
│   │   ├── db/session.py       ← SQLAlchemy async engine
│   │   ├── models/__init__.py  ← All DB models
│   │   ├── schemas/__init__.py ← Pydantic v2 schemas
│   │   └── main.py             ← FastAPI app + health route
│   ├── tests/
│   │   ├── conftest.py         ← Shared fixtures (SQLite in-memory)
│   │   ├── unit/
│   │   │   ├── test_security.py   ← 25 tests: JWT, bcrypt
│   │   │   ├── test_schemas.py    ← 20 tests: Pydantic validation
│   │   │   └── test_models.py     ← 17 tests: SQLAlchemy models
│   │   ├── integration/
│   │   │   ├── test_auth_api.py   ← 16 tests: login/refresh/me
│   │   │   ├── test_menu_api.py   ← 22 tests: full menu CRUD
│   │   │   ├── test_devices_api.py← 15 tests: device lifecycle
│   │   │   ├── test_rbac.py       ← 20 tests: role access matrix
│   │   │   └── test_security.py   ← 18 tests: OWASP checks
│   │   ├── e2e/
│   │   │   └── test_user_flows.py ← 14 Playwright browser tests
│   │   └── performance/
│   │       └── locustfile.py      ← Locust load test scenarios
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini              ← asyncio_mode=auto, cov≥80%
│   └── bandit.yaml             ← SAST config
└── .github/workflows/
    ├── ci.yml                  ← Lint→Unit→Integration→Security→Build
    ├── cd.yml                  ← Staging auto + Production manual
    └── performance.yml         ← Locust on staging
```

---

## PHASE 1 — Prerequisites

Install these on your machine:

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.12+ | `python --version` |
| pip | latest | `pip --version` |
| Node.js | 20+ | `node --version` |
| Docker Desktop | latest | `docker --version` |
| Git | any | `git --version` |

---

## PHASE 2 — Project Setup

```bash
# Clone your repo (or unzip the downloaded archive)
git clone https://github.com/YOUR_USERNAME/menuvision.git
cd menuvision

# Verify structure
ls backend/tests/
# Should show: conftest.py  unit/  integration/  e2e/  performance/
```

---

## PHASE 3 — Backend: Python Environment

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate it
# macOS / Linux:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install ALL dependencies (app + dev/test)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify
python -c "import fastapi, sqlalchemy, pytest, bcrypt; print('✅ All packages OK')"
```

---

## PHASE 4 — Run Unit Tests (No Docker needed)

Unit tests use SQLite in-memory — no Postgres, no Redis required.

```bash
# From backend/ with venv activated:
pytest tests/unit/ -v

# Expected output:
# 62 passed  ·  Coverage: 87%
# (takes ~7 seconds)
```

**What these test:**
- `test_security.py` — bcrypt hashing, JWT create/decode/expire/tamper
- `test_schemas.py` — Pydantic validation: prices, MAC addresses, roles, passwords
- `test_models.py`  — SQLAlchemy defaults, unique constraints, enums

---

## PHASE 5 — Run Integration Tests (Needs Docker)

```bash
# Start Postgres + Redis (from project root, not backend/)
cd ..
docker-compose up -d postgres redis

# Wait ~5 seconds, verify they're running
docker-compose ps

# Back to backend
cd backend

# Run integration tests
pytest tests/integration/ -v

# Expected output:
# ~90 passed  ·  Coverage: 75%+
# (takes ~20–30 seconds)
```

**What these test:**
- `test_auth_api.py`    — Full HTTP login/refresh/me flows
- `test_menu_api.py`    — Complete CRUD for groups → items → publish
- `test_devices_api.py` — Device registration, heartbeat, status
- `test_rbac.py`        — Role permission matrix (super_admin / manager / staff / anonymous)
- `test_security.py`    — OWASP: SQL injection, JWT alg:none, IDOR, privilege escalation

---

## PHASE 6 — Run Full Test Suite

```bash
# Run everything together with coverage report
pytest tests/unit/ tests/integration/ -v --cov=app --cov-report=html

# Open coverage report in browser
open htmlcov/index.html      # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html     # Windows
```

---

## PHASE 7 — Security Scan (Local)

```bash
# Python SAST — checks for hardcoded secrets, unsafe functions
bandit -r app/ -c bandit.yaml

# Dependency vulnerability check
pip-audit --requirement requirements.txt

# Frontend (from frontend-admin/)
cd ../frontend-admin
npm audit --audit-level=high
```

---

## PHASE 8 — E2E Tests (Playwright)

E2E tests need the full app running.

```bash
# Terminal 1: start backend
cd backend && uvicorn app.main:app --reload

# Terminal 2: start frontend
cd frontend-admin && npm run dev

# Terminal 3: install Playwright and run
pip install playwright pytest-playwright
playwright install chromium

pytest tests/e2e/ -v --base-url http://localhost:3000
```

---

## PHASE 9 — Performance Tests (Locust)

Run on staging only, not every PR.

```bash
pip install locust

# Interactive UI (open http://localhost:8089)
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Headless CI mode (50 users, 2 minutes)
locust -f tests/performance/locustfile.py \
  --host=https://staging.menuvision.app \
  --headless -u 50 -r 5 --run-time 120s \
  --html=performance-report.html
```

---

## PHASE 10 — GitHub Actions CI/CD Setup

### Step 1: Push to GitHub

```bash
git init  # if not already a repo
git add .
git commit -m "feat: add test suite and CI/CD pipelines"
git remote add origin https://github.com/YOUR_USERNAME/menuvision.git
git push -u origin main
```

### Step 2: Add GitHub Secrets

Go to: **GitHub repo → Settings → Secrets and variables → Actions → New repository secret**

Add these one by one:

| Secret Name | Value |
|-------------|-------|
| `AWS_ACCESS_KEY_ID` | Your AWS IAM key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS IAM secret |
| `AWS_REGION` | e.g. `ap-south-1` |
| `ECR_REGISTRY` | e.g. `123456789.dkr.ecr.ap-south-1.amazonaws.com` |
| `SECRET_KEY_STAGING` | Random 64-char string |
| `SECRET_KEY_PROD` | Different random 64-char string |
| `POSTGRES_PASSWORD_STAGING` | Strong password |
| `POSTGRES_PASSWORD_PROD` | Different strong password |
| `STAGING_HOST` | IP of your staging server |
| `STAGING_USER` | SSH username (e.g. `ubuntu`) |
| `STAGING_SSH_KEY` | Contents of your `~/.ssh/id_rsa` private key |
| `CODECOV_TOKEN` | From codecov.io (free for public repos) |
| `SLACK_WEBHOOK_URL` | From Slack → Apps → Incoming Webhooks |

### Step 3: Set up GitHub Environments

Go to: **GitHub repo → Settings → Environments**

Create two environments:
1. **staging** — no protection rules (auto-deploy on develop push)
2. **production** — add "Required reviewers" (your username) so every prod deploy needs manual approval

### Step 4: Branch Strategy

```bash
# Create develop branch
git checkout -b develop
git push origin develop

# From now on:
# Feature work → PR to develop → auto-deploys to staging
# When staging looks good → PR to production → requires approval
```

### Step 5: Watch the pipeline

Push any change to trigger CI:
```bash
git commit --allow-empty -m "trigger CI"
git push
```

Go to **GitHub repo → Actions** tab and watch it run.

---

## Quick Reference — Test Commands

```bash
# Unit only (fast, no Docker)
pytest tests/unit/ -v

# Integration only (needs docker-compose up)
pytest tests/integration/ -v

# All backend tests
pytest tests/unit/ tests/integration/ -v

# Single file
pytest tests/unit/test_security.py -v

# Single test
pytest tests/unit/test_security.py::TestPasswordHashing::test_verify_correct_password -v

# With coverage HTML report
pytest tests/unit/ tests/integration/ --cov=app --cov-report=html

# Stop on first failure
pytest tests/ -x

# Show print output
pytest tests/ -s

# Security scan
bandit -r app/ -c bandit.yaml -ll
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError: app` | Run pytest from `backend/` folder, not root |
| `ImportError: aiosqlite` | `pip install aiosqlite` |
| `Connection refused (5432)` | `docker-compose up -d postgres` |
| `asyncio_mode` warning | Already set in `pytest.ini` — update pytest-asyncio to 0.23+ |
| Coverage below 80% | Check `htmlcov/index.html` to see uncovered lines |
| Bandit HIGH finding | Read the finding, add `# nosec` with justification if false positive |
