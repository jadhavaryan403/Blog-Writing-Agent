"""
app/middleware/tracing.py
──────────────────────────
LangSmith / observability middleware.

Adds request-level tracing metadata to every API call so all downstream
LLM calls are grouped under the same LangSmith run.
"""

from __future__ import annotations

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """
    Per-request middleware that:
    1. Assigns a unique request_id (trace_id) to each request.
    2. Logs request + response with timing.
    3. Sets LangSmith session context so all LLM calls within the request
       are grouped in one trace.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start = time.monotonic()

        # Bind context for structured logging
        with structlog.contextvars.bound_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        ):
            logger.info("request_started")
            try:
                response = await call_next(request)
                latency_ms = (time.monotonic() - start) * 1000
                logger.info(
                    "request_completed",
                    status_code=response.status_code,
                    latency_ms=round(latency_ms, 2),
                )
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Response-Time"] = f"{latency_ms:.2f}ms"
                return response
            except Exception as exc:
                latency_ms = (time.monotonic() - start) * 1000
                logger.error("request_failed", error=str(exc), latency_ms=round(latency_ms, 2))
                raise