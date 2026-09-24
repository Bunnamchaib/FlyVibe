from fastapi.testclient import TestClient

from server.app import create_app
from server.rooms import RoomManager
from services.config import default_config


def test_api_status_and_room_hide_invitation_token():
    config = default_config()
    rooms = RoomManager(capacity=6, require_token=True)
    room = rooms.create_room("Home")
    app = create_app(config, rooms)
    client = TestClient(app)

    status = client.get("/api/status").json()
    room_data = client.get("/api/room").json()

    assert status["status"] == "online"
    assert status["port"] == 4545
    assert status["room"] == room.room_id
    assert "token" not in status
    assert room_data["roomId"] == room.room_id
    assert "token" not in room_data


def test_api_webrtc_config_includes_stun_and_optional_turn():
    config = default_config()
    config["turn"]["enabled"] = True
    config["turn"]["urls"] = ["turn:turn.example.com:3478"]
    config["turn"]["username"] = "user"
    config["turn"]["credential"] = "pass"
    rooms = RoomManager(capacity=6, require_token=True)
    rooms.create_room("Home")
    app = create_app(config, rooms)
    client = TestClient(app)

    data = client.get("/api/webrtc-config").json()

    assert {"urls": ["stun:stun.l.google.com:19302"]} in data["iceServers"]
    assert {
        "urls": ["turn:turn.example.com:3478"],
        "username": "user",
        "credential": "pass",
    } in data["iceServers"]

