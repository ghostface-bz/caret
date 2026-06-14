"""Shared sandbox runner for ephemeral scanner sibling containers.

Implements the "Scanner sandbox contract" from docs/API_CONTRACT.md:
- `network_disabled=True` (`--network none`)
- code mounted read-only: named volume `SCAN_DATA_VOLUME` -> `/src:ro`, scan `/src/<scan_id>`
- `mem_limit="2g"`, ~1.5 CPU via `nano_cpus`, non-root `user="1000:1000"`
- `read_only=True` rootfs where possible (tools needing /tmp get a tmpfs)
- auto-remove; stdout captured and parsed by the caller

A uniform `run(scan_id, src_subpath)` is implemented per-tool in sibling modules;
this module provides the low-level `run_container` helper they share.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import docker
from docker.errors import APIError, ContainerError, ImageNotFound
from docker.types import Mount

from app.config import settings

logger = logging.getLogger(__name__)

ONE_AND_A_HALF_CPUS = 1_500_000_000  # nano_cpus


@dataclass
class ContainerResult:
    """Captured result of running an ephemeral scanner sibling container."""

    exit_code: int
    stdout: str
    stderr: str = ""


@dataclass
class ScannerError(Exception):
    """Raised when a scanner sibling container fails to run or produce output."""

    tool: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.tool} scanner failed: {self.detail}"


@dataclass
class ExtraMount:
    """A read-only extra volume mount (by name) into a scanner sibling."""

    volume_name: str
    target: str
    mode: str = "ro"


def run_scanner_container(
    *,
    tool_name: str,
    image: str,
    command: list[str],
    extra_mounts: list[ExtraMount] | None = None,
    allow_exit_codes: tuple[int, ...] = (0,),
    read_only_rootfs: bool = True,
    tmpfs_paths: tuple[str, ...] = ("/tmp",),
    environment: dict[str, str] | None = None,
) -> ContainerResult:
    """Run `image` as an ephemeral, network-disabled sibling container.

    Mounts the shared scan-data named volume read-only at `/src`, plus any
    `extra_mounts` (e.g. semgrep rules, trivy cache). Captures stdout/stderr
    and removes the container afterwards regardless of outcome.

    `allow_exit_codes` lets callers treat non-zero "findings present" exit
    codes (common for security scanners) as success.
    """
    client = docker.from_env()

    mounts = [
        Mount(
            target="/src",
            source=settings.SCAN_DATA_VOLUME,
            type="volume",
            read_only=True,
        )
    ]
    for extra in extra_mounts or []:
        mounts.append(
            Mount(
                target=extra.target,
                source=extra.volume_name,
                type="volume",
                read_only=(extra.mode == "ro"),
            )
        )

    tmpfs = (
        {path: "rw,size=512m,uid=1000,gid=1000" for path in tmpfs_paths}
        if read_only_rootfs
        else None
    )

    container = None
    try:
        container = client.containers.run(
            image=image,
            command=command,
            mounts=mounts,
            network_disabled=True,
            mem_limit="2g",
            nano_cpus=ONE_AND_A_HALF_CPUS,
            user="1000:1000",
            read_only=read_only_rootfs,
            tmpfs=tmpfs,
            environment=environment,
            detach=True,
        )
        exit_status = container.wait()
        exit_code = exit_status.get("StatusCode", -1)

        stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
        stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")

        if exit_code not in allow_exit_codes:
            raise ScannerError(
                tool=tool_name,
                detail=(
                    f"container exited with code {exit_code}; "
                    f"stderr={stderr[-2000:]!r}"
                ),
            )

        return ContainerResult(exit_code=exit_code, stdout=stdout, stderr=stderr)

    except ImageNotFound as exc:
        raise ScannerError(tool=tool_name, detail=f"image not found: {image} ({exc})") from exc
    except ContainerError as exc:
        raise ScannerError(tool=tool_name, detail=f"container error: {exc}") from exc
    except APIError as exc:
        raise ScannerError(tool=tool_name, detail=f"docker API error: {exc}") from exc
    finally:
        if container is not None:
            try:
                container.remove(force=True)
            except APIError:
                pass
