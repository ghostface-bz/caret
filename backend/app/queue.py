"""RQ queue helpers shared between the API process and the worker."""

from __future__ import annotations

import redis
from rq import Queue

from app.config import settings

SCAN_QUEUE_NAME = "scans"

redis_conn = redis.from_url(settings.REDIS_URL)
scan_queue = Queue(SCAN_QUEUE_NAME, connection=redis_conn)


def enqueue_scan(scan_id: str) -> None:
    """Enqueue the `run_scan` job for the given scan id."""
    scan_queue.enqueue("app.worker.run_scan", scan_id, job_timeout=1800)
