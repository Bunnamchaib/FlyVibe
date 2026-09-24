from __future__ import annotations

import re
import subprocess
import threading
from pathlib import Path
from typing import Callable


TRYCLOUDFLARE_RE = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")


def extract_trycloudflare_url(text: str) -> str | None:
    match = TRYCLOUDFLARE_RE.search(text)
    return match.group(0) if match else None


class CloudflareTunnel:
    def __init__(
        self,
        executable: Path,
        local_url: str,
        on_log: Callable[[str], None],
        on_url: Callable[[str], None],
        on_exit: Callable[[int | None], None],
    ) -> None:
        self.executable = executable
        self.local_url = local_url
        self.on_log = on_log
        self.on_url = on_url
        self.on_exit = on_exit
        self.process: subprocess.Popen[str] | None = None
        self._thread: threading.Thread | None = None
        self.public_url: str | None = None

    def start(self) -> None:
        if self.process is not None:
            return
        if not self.executable.exists():
            raise FileNotFoundError(f"cloudflared.exe not found: {self.executable}")
        command = [str(self.executable), "tunnel", "--url", self.local_url]
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        self._thread = threading.Thread(target=self._read_output, daemon=True)
        self._thread.start()

    def _read_output(self) -> None:
        assert self.process is not None
        if self.process.stdout is not None:
            for line in self.process.stdout:
                line = line.rstrip()
                if line:
                    self.on_log(line)
                    url = extract_trycloudflare_url(line)
                    if url and url != self.public_url:
                        self.public_url = url
                        self.on_url(url)
        code = self.process.wait()
        self.on_exit(code)

    def stop(self) -> None:
        proc = self.process
        if proc is None:
            return
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        self.process = None

