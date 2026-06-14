#!/bin/sh
# One-time, network-allowed prefetch of offline scanner data:
#  - semgrep_rules volume <- curated semgrep rule packs (mounted at /rules)
#  - trivy_cache volume   <- trivy vulnerability DB (mounted at /trivy-cache)
#
# Run from the repo root, AFTER `docker compose up -d` has created the named
# volumes (e.g. `docker compose up -d db redis backend worker`):
#
#   bash backend/scripts/prefetch.sh
#
# Safe to re-run; both steps are idempotent (re-downloads/overwrites in place).
#
# NOTE: docker-compose.yml does not give `semgrep_rules`/`trivy_cache` an
# explicit top-level `name:` (unlike `scan_data` -> `scr_scan_data`), so
# Compose creates them as `<project>_semgrep_rules` / `<project>_trivy_cache`
# (project name = compose project, normally the repo directory name). We
# resolve the real volume names via `docker volume ls` so this script works
# regardless of the project name Compose picked.

set -e

resolve_volume() {
    # $1 = bare volume name (e.g. "semgrep_rules")
    suffix="$1"
    # Prefer an exact match, then fall back to "<anything>_<suffix>".
    docker volume ls --format '{{.Name}}' | grep -E "^${suffix}$|_${suffix}$" | head -n1
}

SEMGREP_VOL="$(resolve_volume semgrep_rules)"
TRIVY_VOL="$(resolve_volume trivy_cache)"

if [ -z "$SEMGREP_VOL" ] || [ -z "$TRIVY_VOL" ]; then
    echo "ERROR: could not find semgrep_rules / trivy_cache volumes." >&2
    echo "Run 'docker compose up -d db redis backend worker' first to create them." >&2
    exit 1
fi

echo "Using volumes: semgrep_rules -> $SEMGREP_VOL, trivy_cache -> $TRIVY_VOL"
echo

echo "=== Prefetching semgrep rules into '$SEMGREP_VOL' ==="
docker run --rm \
  -v "$SEMGREP_VOL":/rules \
  --entrypoint sh \
  semgrep/semgrep:latest \
  -c '
    set -e
    rm -rf /rules/* /rules/.[!.]* 2>/dev/null || true
    mkdir -p /tmp/rules-src
    cd /tmp/rules-src
    git clone --depth 1 https://github.com/semgrep/semgrep-rules.git .
    # Curated subset: python, javascript/typescript, secrets, generic security.
    mkdir -p /rules
    cp -r python /rules/
    cp -r javascript /rules/
    cp -r typescript /rules/
    cp -r generic /rules/
    cp -r security /rules/ 2>/dev/null || true
    echo "Rules installed under /rules:"
    find /rules -maxdepth 1
  '

echo
echo "=== Prefetching trivy vulnerability DB into '$TRIVY_VOL' ==="
docker run --rm \
  -v "$TRIVY_VOL":/trivy-cache \
  aquasec/trivy:latest \
  image --download-db-only --cache-dir /trivy-cache

echo
echo "=== Prefetch complete ==="
