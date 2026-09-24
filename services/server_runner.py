from __future__ import annotations

import threading
from typing import Callable

import uvicorn


class UvicornServerRunner:
    def __init__(self, app, host: str, port: int, on_log: Callable[[str], None] | None = None) -> None:
        self.app = app
        self.host = host
        self.port = port
        self.on_log = on_log or (lambda _message: None)
        self.server: uvicorn.Server | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        if self.thread and self.thread.is_alive():
            return
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info", access_log=False)
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self) -> None:
        self.on_log(f"Starting FastAPI server on {self.host}:{self.port}")
        if self.server is not None:
            self.server.run()
        self.on_log("FastAPI server stopped")

    def stop(self) -> None:
        if self.server is not None:
            self.server.should_exit = True
        if self.thread is not None:
            self.thread.join(timeout=5)
        self.thread = None
        self.server = None

