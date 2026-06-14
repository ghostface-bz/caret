"""Centralized environment configuration."""

from __future__ import annotations

import os


class Settings:
    """Reads configuration from environment variables (set in docker-compose.yml)."""

    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://scr:scr@db:5432/scr"
    )
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://redis:6379/0")

    # Directory inside this container where scan code is materialized.
    SCAN_DATA_DIR: str = os.environ.get("SCAN_DATA_DIR", "/data")

    # Name of the named Docker volume backing SCAN_DATA_DIR — sibling scanner
    # containers mount this volume *by name* (DooD) to see the same files.
    SCAN_DATA_VOLUME: str = os.environ.get("SCAN_DATA_VOLUME", "scr_scan_data")

    # Named volumes with pre-fetched offline scanner data, mounted into the
    # worker container (at /rules and /trivy-cache) and re-mounted (by name)
    # into scanner siblings. docker-compose.yml does not pin these to a fixed
    # name (unlike scan_data -> scr_scan_data), so these env vars are
    # fallbacks; `get_semgrep_rules_volume()` / `get_trivy_cache_volume()`
    # below prefer introspecting the worker's own mounts at runtime.
    SEMGREP_RULES_VOLUME: str = os.environ.get("SEMGREP_RULES_VOLUME", "semgrep_rules")
    TRIVY_CACHE_VOLUME: str = os.environ.get("TRIVY_CACHE_VOLUME", "trivy_cache")

    MAX_UPLOAD_BYTES: int = 50 * 1024 * 1024  # 50 MB cap per API_CONTRACT.md


settings = Settings()


def get_semgrep_rules_volume() -> str:
    """Resolve the actual named volume mounted at /rules in this container."""
    from app.docker_introspect import find_mounted_volume_name

    return find_mounted_volume_name("/rules") or settings.SEMGREP_RULES_VOLUME


def get_trivy_cache_volume() -> str:
    """Resolve the actual named volume mounted at /trivy-cache in this container."""
    from app.docker_introspect import find_mounted_volume_name

    return find_mounted_volume_name("/trivy-cache") or settings.TRIVY_CACHE_VOLUME
