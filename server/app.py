from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, WebSocket
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from services.paths import web_dir

from .rooms import RoomManager
from .signaling import SignalingHub


def public_ice_servers(config: dict[str, Any]) -> list[dict[str, Any]]:
    servers = list(config.get("webrtc", {}).get("iceServers", []))
    turn = config.get("turn", {})
    if turn.get("enabled"):
        entry: dict[str, Any] = {"urls": turn.get("urls", [])}
        if turn.get("username"):
            entry["username"] = turn.get("username", "")
        if turn.get("credential"):
            entry["credential"] = turn.get("credential", "")
        servers.append(entry)
    return servers


def create_app(config: dict[str, Any], room_manager: RoomManager | None = None) -> FastAPI:
    rooms = room_manager or RoomManager(
        capacity=int(config.get("room", {}).get("capacity", 6)),
        require_token=bool(config.get("room", {}).get("requireInvitationToken", True)),
    )
    rooms.ensure_room(config.get("room", {}).get("name", "Home"))
    hub = SignalingHub(rooms)
    app = FastAPI(title="FlyVibe Local Voice Server", version=config.get("app", {}).get("version", "0.1.0"))
    app.state.config = config
    app.state.rooms = rooms

    static_dir = web_dir()
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def index() -> Response:
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return HTMLResponse("<h1>FlyVibe web client is missing.</h1>", status_code=500)

    @app.get("/api/status")
    async def status() -> dict[str, Any]:
        room = rooms.ensure_room(config.get("room", {}).get("name", "Home"))
        return {
            "status": "online",
            "port": int(config.get("server", {}).get("port", 4545)),
            "room": room.room_id,
            "participants": rooms.participant_count(room.room_id),
            "capacity": room.capacity,
        }

    @app.get("/api/room")
    async def room() -> dict[str, Any]:
        return rooms.ensure_room(config.get("room", {}).get("name", "Home")).public_dict()

    @app.get("/api/participants")
    async def participants() -> dict[str, Any]:
        room = rooms.ensure_room(config.get("room", {}).get("name", "Home"))
        return {
            "participants": [participant.public_dict() for participant in rooms.participants(room.room_id)],
        }

    @app.get("/api/webrtc-config")
    async def webrtc_config() -> dict[str, Any]:
        return {"iceServers": public_ice_servers(config)}

    @app.get("/api/validate-invite")
    async def validate_invite(room: str = Query(...), token: str | None = Query(default=None)) -> dict[str, Any]:
        if not rooms.validate_invite(room, token):
            raise HTTPException(status_code=403, detail="Invalid or expired invitation")
        return {"ok": True}

    @app.websocket("/ws")
    async def websocket_endpoint(
        websocket: WebSocket,
        room: str = Query(...),
        token: str | None = Query(default=None),
        name: str = Query(default="Guest"),
    ) -> None:
        await hub.connect(websocket, room, token, name)

    return app
