#!/bin/bash
set -e

echo "============================================"
echo "  MedRights Portal - Test Suite"
echo "============================================"

echo ""
echo "=== Backend Unit + Integration Tests ==="
# Uses testing settings (SQLite in-memory, no external deps needed).
# --no-deps skips starting db/redis since tests are self-contained.
docker compose run --rm \
  -e DJANGO_SETTINGS_MODULE=medrights.settings.testing \
  -e MEDRIGHTS_MASTER_KEY=dGVzdGluZy1rZXktMzItYnl0ZXMtbG9uZw== \
  -e MEDRIGHTS_SECRET_KEY=test-secret-key-not-for-production \
  --no-deps \
  backend \
  python -m pytest --tb=short -v

echo ""
echo "=== Frontend Unit Tests ==="
docker compose run --rm \
  --no-deps \
  frontend-tests \
  npx vitest run

echo ""
echo "=== E2E Tests ==="
# E2E tests need the full stack (db, redis, backend, frontend) running.
# The audit pipeline starts the stack before calling this script.

# 1. Wait for backend health endpoint to be ready
echo "  Waiting for backend to be healthy..."
for i in $(seq 1 30); do
  if docker compose exec -T backend python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/')" 2>/dev/null; then
    echo "  Backend is healthy."
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "  WARNING: Backend health check timed out. Attempting E2E anyway..."
  fi
  echo "    attempt $i/30..."
  sleep 2
done

# 2. Seed E2E test users (idempotent - skips if they already exist)
echo "  Seeding E2E test users..."
docker compose exec -T backend python manage.py seed_initial_data \
  --e2e --admin-password 'MedRights2026!'

# 3. Run E2E tests
docker compose run --rm --no-deps e2e npx playwright test --workers=1 --reporter=line

echo ""
echo "============================================"
echo "  All tests passed"
echo "============================================"
