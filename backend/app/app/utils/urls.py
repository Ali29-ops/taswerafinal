"""Helpers for building public URLs behind proxies/tunnels."""

import json

from fastapi import Request

from app.config import get_settings

settings = get_settings()


def public_base_url(request: Request | None = None) -> str:
    if request:
        host = request.headers.get("x-forwarded-host") or request.headers.get("host")
        scheme = _forwarded_scheme(request) or request.url.scheme
        if host and not _is_local_host(host):
            return f"{scheme}://{host}".rstrip("/")
    return settings.frontend_url.rstrip("/")


def _forwarded_scheme(request: Request) -> str | None:
    cf_visitor = request.headers.get("cf-visitor")
    if cf_visitor:
        try:
            scheme = json.loads(cf_visitor).get("scheme")
            if scheme:
                return scheme
        except json.JSONDecodeError:
            pass
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        return forwarded_proto.split(",")[0].strip()
    return None


def _is_local_host(host: str) -> bool:
    clean_host = host.split(":")[0].lower()
    return clean_host in {"localhost", "127.0.0.1", "::1"}
