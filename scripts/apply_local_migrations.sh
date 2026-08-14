#!/usr/bin/env bash
# Apply local PostgreSQL migrations as superuser and grant ownership to the app user.
# Usage: ./scripts/apply_local_migrations.sh [migration.sql ...]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB_NAME="${DB_NAME:-fpredict_db}"
APP_USER="${DB_USER:-Nevy11}"

if [[ $# -eq 0 ]]; then
  MIGRATIONS=("$ROOT"/supabase/migrations/*.sql)
else
  MIGRATIONS=("$@")
fi

echo "Applying migrations to ${DB_NAME} as superuser, owner -> ${APP_USER}"

for file in "${MIGRATIONS[@]}"; do
  echo "==> ${file}"
  psql -d "${DB_NAME}" -v ON_ERROR_STOP=1 -f "${file}"
done

psql -d "${DB_NAME}" -v ON_ERROR_STOP=1 <<SQL
ALTER TABLE IF EXISTS players OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS teams OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS fantasy_player_status OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS player_impact_metrics OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS player_performance OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS player_metadata OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS squad_membership OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS match_records OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS feature_store OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS h2h_history OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS predictions OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS prediction_requests OWNER TO "${APP_USER}";
ALTER TABLE IF EXISTS unstructured_news OWNER TO "${APP_USER}";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "${APP_USER}";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "${APP_USER}";
SQL

echo "Done."
