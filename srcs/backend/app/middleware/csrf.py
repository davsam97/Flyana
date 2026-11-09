"""Double-submit CSRF

The `csrf_token` cookie is readable by our JS, which echoes it in
`X-CSRF-Token`. A third-party site can make the browser send the cookie but
cannot read it, so it cannot forge the header.
"""

from __future__ import annotations

import secrets

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

# Exceptions : these routes happen before any session exists
EXEMPT_PREFIXES = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/oauth/",  # callback from provider without header
)


class CSRFMiddleware(BaseHTTPMiddleware):
    """Blocks writes that do not prove they came from our own frontend"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Runs on every request before the route does"""
        if request.method in SAFE_METHODS:
            return await call_next(request)

        if request.url.path.startswith(EXEMPT_PREFIXES):
            return await call_next(request)

        cookie = request.cookies.get("csrf_token", "")
        header = request.headers.get("x-csrf-token", "")

        # compare_digest, not `==`: a naive comparison stops at the first
        # differing byte, so how long it takes leaks the length of the correct
        # prefix an attacker has guessed so far.
        if not cookie or not header or not secrets.compare_digest(cookie, header):
            return JSONResponse(
                {"detail": "invalid CSRF token"},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        return await call_next(request)
