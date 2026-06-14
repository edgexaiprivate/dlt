#!/usr/bin/env bash
# MenuVision — One-command local dev setup
set -e

echo "🚀 MenuVision Dev Setup"
echo "========================"

# ── Backend ───────────────────────────────────────────────────────────────────
echo ""
echo "📦 Setting up Python backend..."
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt --quiet

# Copy env if not exists
[ ! -f .env ] && cp .env.example .env && echo "✅ Created .env from template"

# Start Postgres + Redis in Docker
echo "🐳 Starting Postgres + Redis..."
cd ..
docker-compose up -d postgres redis
sleep 3

cd backend
source .venv/bin/activate

# Run migrations
echo "🗄️  Running database migrations..."
alembic upgrade head 2>/dev/null || {
  echo "Alembic not initialized — running direct table creation..."
  python -c "
import asyncio
from app.db.session import engine
from app.models import Base
async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(main())
"
}

# Seed data
echo "🌱 Seeding database..."
python -m scripts.seed

echo ""
echo "✅ Backend ready!"
echo "   Start with: cd backend && source .venv/bin/activate && uvicorn app.main:app --reload"
echo "   API docs:    http://localhost:8000/docs"

# ── Frontend ──────────────────────────────────────────────────────────────────
echo ""
echo "📦 Setting up React admin panel..."
cd ../frontend-admin
npm install --silent

echo ""
echo "✅ Frontend ready!"
echo "   Start with: cd frontend-admin && npm run dev"
echo "   Admin URL:   http://localhost:3000"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Default credentials:"
echo "  Super Admin: admin / Admin@1234"
echo "  Manager:     manager1 / Manager@1234"
echo ""
