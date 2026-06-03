"""SSRF guard: validate an outbound URL targets a public host before fetching.

Used by any code path that fetches a caller-supplied URL (image rendering,
webhooks). Blocks server-side request forgery to cloud metadata
(169.254.169.254), loopback, private ranges, link-local and reserved space.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

ALLOWED_SCHEMES = {"http", "https"}


class UnsafeURLError(ValueError):
    """Raised when a URL is rejected as unsafe (disallowed scheme or non-public host)."""


def _is_public_ip(ip: str) -> bool:
    addr = ipaddress.ip_address(ip)
    return not (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local  # 169.254.0.0/16 (cloud metadata) + fe80::/10
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    )


def validate_public_url(url: str) -> str:
    """Return ``url`` if it targets a public host over http(s); else raise UnsafeURLError.

    Resolves the hostname and rejects the URL if ANY resolved address is
    non-public. Callers should also disable redirect-following so a public URL
    cannot bounce to an internal one.
    """
    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeURLError(f"scheme not allowed: {parsed.scheme!r}")

    host = parsed.hostname
    if not host:
        raise UnsafeURLError("URL has no host")

    port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"DNS resolution failed for host {host!r}") from exc

    addresses = {info[4][0] for info in infos}
    if not addresses:
        raise UnsafeURLError(f"no addresses resolved for host {host!r}")

    for ip in addresses:
        if not _is_public_ip(ip):
            raise UnsafeURLError(f"host {host!r} resolves to non-public address {ip}")

    return url


__all__ = ["validate_public_url", "UnsafeURLError"]
