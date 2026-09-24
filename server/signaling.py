from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket

from .models import Participant
from .rooms import RoomManager


class SignalingHub:
    def __init__(self, rooms: RoomManager) -> None:
        self.rooms = rooms
        self._connections: dict[str, WebSocket] = {}
        self._client_rooms: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, room_id: str, token: str | None, name: str) -> None:
        if not self.rooms.validate_invite(room_id, token):
            await websocket.accept()
            await websocket.send_json({"type": "error", "message": "Invalid or expired invitation"})
            await websocket.close(code=4403)
            return
        await websocket.accept()
        try:
            participant = self.rooms.add_participant(room_id, name)
        except ValueError as exc:
            await websocket.send_json({"type": "error", "message": str(exc)})
            await websocket.close(code=4409)
            return
        async with self._lock:
            existing = [p.public_dict() for p in self.rooms.participants(room_id) if p.client_id != participant.client_id]
            self._connections[participant.client_id] = websocket
            self._client_rooms[participant.client_id] = room_id
        await websocket.send_json(
            {
                "type": "joined",
                "clientId": participant.client_id,
                "room": room_id,
                "peers": existing,
            }
        )
        await self.broadcast(
            room_id,
            {
                "type": "peer-joined",
                "peer": participant.public_dict(),
            },
            exclude=participant.client_id,
        )
        try:
            while True:
                message = await websocket.receive_json()
                await self.handle_message(participant, room_id, message)
        except Exception:
            pass
        finally:
            await self.disconnect(room_id, participant.client_id)

    async def handle_message(self, participant: Participant, room_id: str, message: dict[str, Any]) -> None:
        msg_type = message.get("type")
        if msg_type in {"offer", "answer", "ice"}:
            target = str(message.get("target", ""))
            payload = dict(message)
            payload["from"] = participant.client_id
            payload["name"] = participant.name
            await self.send_to(target, payload)
        elif msg_type == "leave":
            await self.disconnect(room_id, participant.client_id)
        elif msg_type == "speaking":
            await self.broadcast(
                room_id,
                {"type": "speaking", "clientId": participant.client_id, "speaking": bool(message.get("speaking"))},
                exclude=participant.client_id,
            )

    async def disconnect(self, room_id: str, client_id: str) -> None:
        async with self._lock:
            websocket = self._connections.pop(client_id, None)
            self._client_rooms.pop(client_id, None)
        self.rooms.remove_participant(room_id, client_id)
        if websocket is not None:
            try:
                await websocket.close()
            except Exception:
                pass
        await self.broadcast(room_id, {"type": "peer-left", "clientId": client_id})

    async def send_to(self, client_id: str, message: dict[str, Any]) -> None:
        websocket = self._connections.get(client_id)
        if websocket is None:
            return
        try:
            await websocket.send_json(message)
        except Exception:
            room_id = self._client_rooms.get(client_id, "")
            if room_id:
                await self.disconnect(room_id, client_id)

    async def broadcast(self, room_id: str, message: dict[str, Any], exclude: str | None = None) -> None:
        targets = [
            client_id
            for client_id, active_room in self._client_rooms.items()
            if active_room == room_id and client_id != exclude
        ]
        for client_id in targets:
            await self.send_to(client_id, message)

