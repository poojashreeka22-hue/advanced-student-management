"""
Simple in-memory rate limiter middleware for authentication endpoints.
"""

import time
from collections import defaultdict
from typing import Dict, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.request_records: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Only rate limit auth login endpoints
        if request.url.path.endswith("/login") and request.method == "POST":
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            window_start = now - settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS

            # Filter records in current window
            self.request_records[client_ip] = [
                t for t in self.request_records[client_ip] if t > window_start
            ]

            if len(self.request_records[client_ip]) >= settings.RATE_LIMIT_LOGIN_MAX:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many login attempts. Please wait before retrying."}
                )

            self.request_records[client_ip].append(now)

        return await call_next(request)
