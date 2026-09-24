from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Participant:
    client_id: str
    name: str
    joined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def public_dict(self) -> dict[str, str]:
        return {
            "clientId": self.client_id,
            "name": self.name,
            "joinedAt": self.joined_at.isoformat(),
        }


@dataclass
class Room:
    room_id: str
    name: str
    token: str
    capacity: int
    participants: dict[str, Participant] = field(default_factory=dict)

    def public_dict(self) -> dict[str, object]:
        return {
            "roomId": self.room_id,
            "name": self.name,
            "capacity": self.capacity,
            "participants": len(self.participants),
        }

