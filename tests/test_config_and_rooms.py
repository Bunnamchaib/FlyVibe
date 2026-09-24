from pathlib import Path

from services.config import load_config
from server.rooms import RoomManager


def test_load_config_creates_default_file(tmp_path: Path):
    config_path = tmp_path / "config.json"

    config = load_config(config_path)

    assert config_path.exists()
    assert config["server"]["port"] == 4545
    assert config["room"]["capacity"] == 6
    assert config["webrtc"]["iceServers"][0]["urls"] == ["stun:stun.l.google.com:19302"]


def test_room_manager_generates_secure_invite_and_invalidates_old_token():
    rooms = RoomManager(capacity=6, require_token=True)
    room = rooms.create_room("Test Room")
    old_token = room.token

    assert len(room.room_id) == 6
    assert len(old_token) >= 20
    assert rooms.validate_invite(room.room_id, old_token)

    new_token = rooms.regenerate_invite()

    assert new_token != old_token
    assert not rooms.validate_invite(room.room_id, old_token)
    assert rooms.validate_invite(room.room_id, new_token)


def test_room_manager_capacity_and_participant_lifecycle():
    rooms = RoomManager(capacity=2, require_token=False)
    room = rooms.create_room("Home")

    first = rooms.add_participant(room.room_id, "OHM")
    second = rooms.add_participant(room.room_id, "JUN")

    assert first.client_id != second.client_id
    assert rooms.participant_count(room.room_id) == 2

    try:
        rooms.add_participant(room.room_id, "MAX")
    except ValueError as exc:
        assert "full" in str(exc).lower()
    else:
        raise AssertionError("room capacity was not enforced")

    rooms.remove_participant(room.room_id, first.client_id)
    assert rooms.participant_count(room.room_id) == 1

