#!/usr/bin/env bash
# Push FPredict SQL migrations to the linked Supabase project (EPL Data).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

PROJECT_REF="${SUPABASE_PROJECT_ID:-agojvvfjajkkpqohehcm}"
DB_PASSWORD="${SUPABASE_DB_PASSWORD:-${DB_PASSWORD:-}}"

echo "==> Linking Supabase project ${PROJECT_REF}"
if ! supabase link --project-ref "$PROJECT_REF"; then
  echo ""
  echo "Link failed. If the project is paused, unpause it first:"
  echo "  https://supabase.com/dashboard/project/${PROJECT_REF}"
  exit 1
fi

echo "==> Pushing migrations to remote Supabase"
if [[ -n "$DB_PASSWORD" ]]; then
  supabase db push --linked --yes -p "$DB_PASSWORD"
else
  echo "No SUPABASE_DB_PASSWORD or DB_PASSWORD in .env — you will be prompted for the database password."
  supabase db push --linked --yes
fi

echo "==> Done. Remote migration history:"
supabase migration list --linked
