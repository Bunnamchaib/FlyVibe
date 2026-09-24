from __future__ import annotations

import socket


def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    probe_host = "127.0.0.1" if host == "0.0.0.0" else host
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((probe_host, int(port)))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def preferred_lan_ip() -> str:
    candidates: list[str] = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        candidates.append(sock.getsockname()[0])
        sock.close()
    except OSError:
        pass
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            candidates.append(info[4][0])
    except OSError:
        pass
    for ip in candidates:
        if ip.startswith("127.") or ip.startswith("169.254."):
            continue
        parts = ip.split(".")
        if len(parts) == 4 and all(part.isdigit() for part in parts):
            return ip
    return "127.0.0.1"

