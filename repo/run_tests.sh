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

# echo ""
# echo "=== E2E Tests (requires running stack) ==="
# # E2E tests need the full stack (db, redis, backend, frontend) running.
# # They are run with --workers=1 for sequential execution stability.
# # To run manually: docker compose up -d && docker compose run --rm --no-deps e2e npx playwright test --workers=1
# if docker compose ps backend --status running -q 2>/dev/null | grep -q .; then
#   docker compose run --rm --no-deps e2e npx playwright test --workers=1 --reporter=line
# else
#   echo "  SKIPPED: backend not running. Start stack first with 'docker compose up -d'."
# fi

echo ""
echo "============================================"
echo "  All tests passed"
echo "============================================"
