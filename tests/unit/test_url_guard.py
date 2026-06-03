"""Tests for the SSRF URL guard (deckforge.security.url_guard)."""

from __future__ import annotations

import pytest

from deckforge.security.url_guard import UnsafeURLError, validate_public_url


@pytest.mark.parametrize(
    "url",
    [
        "http://169.254.169.254/latest/meta-data/",  # cloud metadata (SSRF classic)
        "http://127.0.0.1/admin",
        "http://localhost/internal",
        "http://10.0.0.5/x",
        "http://172.16.0.1/x",
        "http://192.168.1.1/x",
        "http://[::1]/x",
        "http://0.0.0.0/x",
        "file:///etc/passwd",
        "ftp://example.com/resource",
        "gopher://127.0.0.1:6379/_INFO",
        "//example.com/no-scheme",
    ],
)
def test_rejects_unsafe_urls(url: str) -> None:
    with pytest.raises(UnsafeURLError):
        validate_public_url(url)


def test_allows_public_literal_ip() -> None:
    # A public literal IP resolves to itself (no external DNS needed in CI).
    assert validate_public_url("https://93.184.216.34/image.png") == "https://93.184.216.34/image.png"
