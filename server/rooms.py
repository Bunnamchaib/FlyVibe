from __future__ import annotations

import secrets
import string
import threading
import uuid

from .models import Participant, Room


ROOM_ALPHABET = string.ascii_uppercase + string.digits


class RoomManager:
    def __init__(self, capacity: int = 6, require_token: bool = True) -> None:
        self.capacity = int(capacity)
        self.require_token = bool(require_token)
        self._room: Room | None = None
        self._lock = threading.RLock()

    @property
    def current_room(self) -> Room | None:
        return self._room

    def create_room(self, name: str = "Home") -> Room:
        with self._lock:
            room_id = self._generate_room_id()
            token = secrets.token_urlsafe(32)
            self._room = Room(room_id=room_id, name=name or "Home", token=token, capacity=self.capacity)
            return self._room

    def ensure_room(self, name: str = "Home") -> Room:
        with self._lock:
            if self._room is None:
                return self.create_room(name)
            return self._room

    def regenerate_invite(self) -> str:
        with self._lock:
            room = self.ensure_room()
            room.token = secrets.token_urlsafe(32)
            return room.token

    def validate_invite(self, room_id: str, token: str | None) -> bool:
        with self._lock:
            room = self._room
            if room is None or room.room_id != room_id:
                return False
            if not self.require_token:
                return True
            return bool(token) and secrets.compare_digest(room.token, token)

    def invitation_url(self, base_url: str) -> str:
        with self._lock:
            room = self.ensure_room()
            separator = "&" if "?" in base_url else "?"
            if self.require_token:
                return f"{base_url}{separator}room={room.room_id}&token={room.token}"
            return f"{base_url}{separator}room={room.room_id}"

    def add_participant(self, room_id: str, name: str) -> Participant:
        with self._lock:
            room = self._require_room(room_id)
            if len(room.participants) >= room.capacity:
                raise ValueError("Room is full")
            participant = Participant(client_id=str(uuid.uuid4()), name=(name or "Guest").strip()[:40] or "Guest")
            room.participants[participant.client_id] = participant
            return participant

    def remove_participant(self, room_id: str, client_id: str) -> None:
        with self._lock:
            room = self._room
            if room and room.room_id == room_id:
                room.participants.pop(client_id, None)

    def participants(self, room_id: str | None = None) -> list[Participant]:
        with self._lock:
            room = self._room
            if room is None:
                return []
            if room_id is not None and room.room_id != room_id:
                return []
            return list(room.participants.values())

    def participant_count(self, room_id: str | None = None) -> int:
        return len(self.participants(room_id))

    def _require_room(self, room_id: str) -> Room:
        if self._room is None or self._room.room_id != room_id:
            raise ValueError("Invalid or expired invitation")
        return self._room

    def _generate_room_id(self) -> str:
        return "".join(secrets.choice(ROOM_ALPHABET) for _ in range(6))

