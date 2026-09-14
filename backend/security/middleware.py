"""WebSecKit — FastAPI/Starlette middleware."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .config.security_config import ENABLED, MODULES
from .cors.cors import resolve_cors
from .headers.security_headers import security_header_map
from .https.enforce_https import https_redirect_url, is_https_request, should_enforce_https


class WebSecKitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, trust_proxy: bool = False) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.trust_proxy = trust_proxy

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        if ENABLED.get("https") and should_enforce_https() and not is_https_request(
            request.url.scheme,
            request.headers.get("x-forwarded-proto"),
            self.trust_proxy,
        ):
            host = request.headers.get("host", request.url.hostname or "localhost")
            return Response(status_code=308, headers={"Location": https_redirect_url(host, request.url.path)})

        if request.method == "OPTIONS":
            allowed, headers = resolve_cors(request.headers.get("origin"))
            headers.update(security_header_map())
            return Response(status_code=204 if allowed else 403, headers=headers)

        if MODULES.get("rateLimiting"):
            from .rate_limit.rate_limiter import client_ip, rate_limit

            ip = client_ip({k.lower(): v for k, v in request.headers.items()}, self.trust_proxy)
            limited = rate_limit("ip", ip=ip, route=request.url.path)
            if not limited["allowed"]:
                headers = security_header_map()
                headers["Retry-After"] = str(limited["retry_after"])
                return Response("Too Many Requests", status_code=429, headers=headers)

        if MODULES.get("csrf"):
            from .csrf.csrf import verify_csrf

            csrf_ok = verify_csrf(
                request.method,
                request.cookies.get("csrf") or request.cookies.get("__Host-csrf"),
                request.headers.get("x-csrf-token"),
            )
            if not csrf_ok:
                return Response("Forbidden", status_code=403, headers=security_header_map())

        response = await call_next(request)
        if ENABLED.get("headers"):
            for key, value in security_header_map().items():
                response.headers.setdefault(key, value)
        if ENABLED.get("cors"):
            allowed, cors_headers = resolve_cors(request.headers.get("origin"))
            if allowed:
                for key, value in cors_headers.items():
                    response.headers[key] = value
        return response
