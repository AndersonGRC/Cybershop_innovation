#!/usr/bin/env bash
# Back up the control plane and every registered tenant database, including
# legacy/custom names and suspended tenants. Intended for the root cron job.
set -Eeuo pipefail
umask 077

DEST=/var/backups/cybershop
STAMP=$(date -u +%Y%m%d_%H%M%S)

case "${1:-}" in
  ''|--list|--no-prune) ;;
  *) echo 'Usage: cybershop-backup.sh [--list|--no-prune]' >&2; exit 2 ;;
esac

if [[ ! -d "$DEST" ]]; then
  echo "Backup directory missing: $DEST" >&2
  exit 1
fi

# A failed control-plane query must stop the job; an empty set must never be
# mistaken for a successful backup of all tenants.
tenant_dbs=$(sudo -u postgres psql -X -qAt -v ON_ERROR_STOP=1 \
  -d saas_control_plane \
  -c "SELECT DISTINCT db_name FROM tenant_databases WHERE db_name IS NOT NULL AND db_name <> '' ORDER BY db_name")
if [[ -z "$tenant_dbs" ]]; then
  echo 'No tenant databases returned by the control plane' >&2
  exit 1
fi
mapfile -t dbs <<< "$tenant_dbs"

if [[ "${1:-}" == '--list' ]]; then
  printf '%s\n' saas_control_plane "${dbs[@]}"
  exit 0
fi

failures=0
for db in saas_control_plane "${dbs[@]}"; do
  # PostgreSQL permits punctuation in quoted names; never use that name as an
  # unchecked filesystem path. Keep familiar filenames for simple names.
  if [[ "$db" =~ ^[A-Za-z0-9_]+$ ]]; then
    file_base=$db
  else
    file_base="db_$(printf '%s' "$db" | sha256sum | cut -c1-16)"
  fi
  target="$DEST/${file_base}_${STAMP}.sql.gz"
  if [[ -e "$target" ]]; then
    echo "Backup target already exists: $target" >&2
    failures=$((failures + 1))
    continue
  fi
  partial=$(mktemp "$DEST/.${file_base}_${STAMP}.XXXXXX.partial")
  if sudo -u postgres pg_dump -d "$db" | gzip -c > "$partial" && gzip -t "$partial"; then
    mv -- "$partial" "$target"
    echo "Backed up $db"
  else
    echo "Backup failed for $db; partial file retained at $partial" >&2
    failures=$((failures + 1))
  fi
done

if (( failures > 0 )); then
  echo "$failures database backup(s) failed; old backups were not pruned" >&2
  exit 1
fi

if [[ "${1:-}" != '--no-prune' ]]; then
  find "$DEST" -maxdepth 1 -type f -name '*.sql.gz' -mtime +7 -delete
fi
