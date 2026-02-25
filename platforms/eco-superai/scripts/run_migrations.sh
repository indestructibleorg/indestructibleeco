#!/usr/bin/env bash
# SuperAI Platform — Migration runner
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

ACTION="${1:-upgrade}"

case "$ACTION" in
    upgrade)
        echo "▶ Running migrations (upgrade head)..."
        alembic upgrade head
        echo "✅ Migrations applied"
        ;;
    downgrade)
        STEPS="${2:-1}"
        echo "▶ Rolling back $STEPS migration(s)..."
        alembic downgrade "-$STEPS"
        echo "✅ Rollback complete"
        ;;
    generate)
        MESSAGE="${2:-auto_migration}"
        echo "▶ Generating migration: $MESSAGE"
        alembic revision --autogenerate -m "$MESSAGE"
        echo "✅ Migration generated"
        ;;
    history)
        echo "▶ Migration history:"
        alembic history --verbose
        ;;
    current)
        echo "▶ Current revision:"
        alembic current
        ;;
    seed)
        echo "▶ Seeding database..."
        python -m scripts.seed_data
        echo "✅ Seed complete"
        ;;
    reset)
        echo "⚠️  Resetting database (downgrade to base + upgrade + seed)..."
        alembic downgrade base
        alembic upgrade head
        python -m scripts.seed_data
        echo "✅ Database reset complete"
        ;;
    *)
        echo "Usage: $0 {upgrade|downgrade [steps]|generate [message]|history|current|seed|reset}"
        exit 1
        ;;
esac