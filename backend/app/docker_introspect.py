"""Helpers for discovering this container's own Docker mounts (DooD).

docker-compose.yml mounts `semgrep_rules` and `trivy_cache` into the worker
WITHOUT giving them an explicit top-level `name:` (unlike `scan_data`, which
is pinned to `scr_scan_data`). Compose therefore creates them as
`<project>_semgrep_rules` / `<project>_trivy_cache`, where `<project>` is the
Compose project name (normally the repo directory name) — not a fixed,
predictable string we can hardcode or rely on an env var for.

Since the worker has `/var/run/docker.sock` mounted, it can ask the Docker
daemon for its own container's mount list and read off the *actual* volume
name backing `/rules` / `/trivy-cache`, then pass that name to sibling
containers. This works regardless of the Compose project name.
"""

from __future__ import annotations

import logging
import os
import socket

import docker
from docker.errors import APIError, NotFound

logger = logging.getLogger(__name__)


def _own_container_id() -> str | None:
    """Best-effort container ID for the currently running container.

    `HOSTNAME` is the container ID (short form) in Docker by default. Falls
    back to parsing `/proc/self/cgroup` for older cgroup v1 setups.
    """
    hostname = os.environ.get("HOSTNAME") or socket.gethostname()
    if hostname:
        return hostname

    try:
        with open("/proc/self/cgroup") as f:
            for line in f:
                parts = line.strip().split("/")
                if len(parts) > 1 and len(parts[-1]) == 64:
                    return parts[-1]
    except OSError:
        pass

    return None


def find_mounted_volume_name(target_path: str) -> str | None:
    """Return the named volume mounted at `target_path` in this container, if any."""
    container_id = _own_container_id()
    if not container_id:
        return None

    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
    except (NotFound, APIError, Exception):  # noqa: BLE001
        logger.warning("could not introspect own container mounts", exc_info=True)
        return None

    for mount in container.attrs.get("Mounts", []):
        if mount.get("Destination") == target_path and mount.get("Type") == "volume":
            return mount.get("Name")

    return None
