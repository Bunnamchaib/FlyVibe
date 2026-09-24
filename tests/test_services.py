import socket

from services.cloudflare import extract_trycloudflare_url
from services.network import is_port_available, preferred_lan_ip


def test_extract_trycloudflare_url_from_mixed_log_output():
    text = "INFO ready https://quiet-river-123.trycloudflare.com more text"

    assert extract_trycloudflare_url(text) == "https://quiet-river-123.trycloudflare.com"


def test_extract_trycloudflare_url_returns_none_when_missing():
    assert extract_trycloudflare_url("cloudflared started without url yet") is None


def test_is_port_available_reports_bound_port_unavailable():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)
    port = sock.getsockname()[1]
    try:
        assert not is_port_available(port, "127.0.0.1")
    finally:
        sock.close()


def test_preferred_lan_ip_returns_ipv4_text():
    ip = preferred_lan_ip()

    parts = ip.split(".")
    assert len(parts) == 4
    assert all(0 <= int(part) <= 255 for part in parts)

