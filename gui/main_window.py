from __future__ import annotations

import time
import webbrowser
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from server.app import create_app
from server.rooms import RoomManager
from services.cloudflare import CloudflareTunnel
from services.config import load_config, save_config
from services.network import is_port_available, preferred_lan_ip
from services.paths import cloudflared_path
from services.qr_service import qr_png_bytes, save_qr_png
from services.server_runner import UvicornServerRunner


def app_stylesheet() -> str:
    return """
    QWidget { background:#0d1117; color:#e6edf3; font-family:'Segoe UI'; font-size:14px; }
    QMainWindow { background:#0d1117; }
    QFrame#card { background:#161b22; border:1px solid #30363d; border-radius:8px; }
    QLabel#title { font-size:28px; font-weight:700; letter-spacing:0; color:#f0f6fc; }
    QLabel#subtitle { color:#8b949e; font-size:14px; }
    QLabel#sectionTitle { color:#f0f6fc; font-size:16px; font-weight:700; }
    QLabel#statusPill { padding:7px 12px; border-radius:14px; font-weight:700; }
    QPushButton { background:#21262d; border:1px solid #30363d; border-radius:6px; padding:10px 14px; color:#f0f6fc; font-weight:600; }
    QPushButton:hover { background:#30363d; }
    QPushButton:disabled { color:#6e7681; background:#161b22; }
    QPushButton#primary { background:#238636; border-color:#2ea043; color:white; font-size:18px; padding:16px 18px; }
    QPushButton#danger { background:#da3633; border-color:#f85149; color:white; font-size:18px; padding:16px 18px; }
    QPushButton#accent { background:#1f6feb; border-color:#388bfd; color:white; }
    QLineEdit, QSpinBox { background:#0d1117; border:1px solid #30363d; border-radius:6px; padding:8px; color:#f0f6fc; }
    QTextEdit { background:#010409; border:1px solid #30363d; border-radius:8px; padding:8px; color:#c9d1d9; font-family:'Consolas'; font-size:12px; }
    QScrollArea { border:0; }
    """


class UiBridge(QObject):
    log = Signal(str)
    public_url = Signal(str)
    tunnel_exit = Signal(object)


class SettingsDialog(QDialog):
    def __init__(self, config: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.config = config
        layout = QFormLayout(self)
        self.port = QSpinBox()
        self.port.setRange(1024, 65535)
        self.port.setValue(int(config["server"]["port"]))
        self.room_name = QLineEdit(str(config["room"]["name"]))
        self.capacity = QSpinBox()
        self.capacity.setRange(2, 12)
        self.capacity.setValue(int(config["room"]["capacity"]))
        self.require_token = QCheckBox("Require invitation token")
        self.require_token.setChecked(bool(config["room"]["requireInvitationToken"]))
        self.auto_copy = QCheckBox("Auto copy public URL")
        self.auto_copy.setChecked(bool(config["ui"]["autoCopyPublicUrl"]))
        self.auto_open = QCheckBox("Automatically open browser")
        self.auto_open.setChecked(bool(config["ui"]["autoOpenBrowser"]))
        self.cloudflared = QLineEdit(str(config["cloudflare"].get("path", "")))
        self.debug = QCheckBox("Debug logs")
        self.debug.setChecked(bool(config.get("debug", False)))
        layout.addRow("Port", self.port)
        layout.addRow("Room name", self.room_name)
        layout.addRow("Capacity", self.capacity)
        layout.addRow("", self.require_token)
        layout.addRow("", self.auto_copy)
        layout.addRow("", self.auto_open)
        layout.addRow("Cloudflared path", self.cloudflared)
        layout.addRow("", self.debug)
        buttons = QHBoxLayout()
        save = QPushButton("SAVE")
        cancel = QPushButton("CANCEL")
        save.setObjectName("accent")
        save.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addRow(buttons)

    def updated_config(self) -> dict[str, Any]:
        self.config["server"]["port"] = int(self.port.value())
        self.config["room"]["name"] = self.room_name.text().strip() or "Home"
        self.config["room"]["capacity"] = int(self.capacity.value())
        self.config["room"]["requireInvitationToken"] = self.require_token.isChecked()
        self.config["ui"]["autoCopyPublicUrl"] = self.auto_copy.isChecked()
        self.config["ui"]["autoOpenBrowser"] = self.auto_open.isChecked()
        self.config["cloudflare"]["path"] = self.cloudflared.text().strip()
        self.config["debug"] = self.debug.isChecked()
        return self.config


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LOCAL VOICE - Private WebRTC Voice Server")
        self.resize(900, 650)
        self.setMinimumSize(760, 560)
        self.setStyleSheet(app_stylesheet())
        self.config = load_config()
        self.room_manager = RoomManager(
            capacity=int(self.config["room"]["capacity"]),
            require_token=bool(self.config["room"]["requireInvitationToken"]),
        )
        self.room_manager.create_room(str(self.config["room"]["name"]))
        self.server_runner: UvicornServerRunner | None = None
        self.tunnel: CloudflareTunnel | None = None
        self.public_root_url: str | None = None
        self.invitation_url: str | None = None
        self.bridge = UiBridge()
        self.bridge.log.connect(self.log)
        self.bridge.public_url.connect(self.on_public_url)
        self.bridge.tunnel_exit.connect(self.on_tunnel_exit)
        self._build_ui()
        self.refresh_static_info()
        self.participant_timer = QTimer(self)
        self.participant_timer.timeout.connect(self.refresh_participants)
        self.participant_timer.start(1500)

    def _build_ui(self) -> None:
        root = QWidget()
        main = QVBoxLayout(root)
        main.setContentsMargins(22, 18, 22, 18)
        main.setSpacing(14)
        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("LOCAL VOICE")
        title.setObjectName("title")
        subtitle = QLabel("Private WebRTC Voice Server")
        subtitle.setObjectName("subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        self.status = QLabel("OFFLINE")
        self.status.setObjectName("statusPill")
        header.addLayout(title_box, 1)
        header.addWidget(self.status)
        main.addLayout(header)
        grid = QGridLayout()
        grid.setSpacing(14)
        self.server_card = self._card("Server")
        self.port_label = QLabel()
        self.lan_label = QLabel()
        self.localhost_label = QLabel()
        self.room_label = QLabel()
        self.users_label = QLabel("Users Online: 0")
        self._add_rows(self.server_card.layout(), [
            ("Application Port", self.port_label),
            ("Local Address", self.lan_label),
            ("Localhost", self.localhost_label),
            ("Room ID", self.room_label),
            ("Participants", self.users_label),
        ])
        self.cloudflare_card = self._card("Cloudflare Tunnel")
        self.tunnel_status = QLabel("OFFLINE")
        self.public_url_label = QLabel("No public URL")
        self.invite_label = QLabel("No invitation link")
        self.public_url_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.invite_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._add_rows(self.cloudflare_card.layout(), [
            ("Tunnel", self.tunnel_status),
            ("Public URL", self.public_url_label),
            ("Invite", self.invite_label),
        ])
        self.qr_card = self._card("QR Invite")
        self.qr_label = QLabel("QR appears after Cloudflare URL is ready")
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumSize(240, 240)
        self.qr_card.layout().addWidget(self.qr_label)
        self.people_card = self._card("Users")
        self.participant_list = QLabel("No users online")
        self.participant_list.setAlignment(Qt.AlignTop)
        self.people_card.layout().addWidget(self.participant_list)
        grid.addWidget(self.server_card, 0, 0)
        grid.addWidget(self.cloudflare_card, 0, 1)
        grid.addWidget(self.qr_card, 1, 0)
        grid.addWidget(self.people_card, 1, 1)
        main.addLayout(grid, 1)
        buttons = QHBoxLayout()
        self.start_btn = QPushButton("START SERVER")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(self.toggle_server)
        self.copy_btn = QPushButton("COPY LINK")
        self.copy_btn.clicked.connect(self.copy_link)
        self.open_btn = QPushButton("OPEN ROOM")
        self.open_btn.clicked.connect(self.open_room)
        self.save_qr_btn = QPushButton("SAVE QR")
        self.save_qr_btn.clicked.connect(self.save_qr)
        self.regen_btn = QPushButton("REGENERATE INVITE")
        self.regen_btn.clicked.connect(self.regenerate_invite)
        self.settings_btn = QPushButton("SETTINGS")
        self.settings_btn.clicked.connect(self.open_settings)
        for button in (self.copy_btn, self.open_btn, self.save_qr_btn, self.regen_btn):
            button.setEnabled(False)
        buttons.addWidget(self.start_btn)
        buttons.addWidget(self.copy_btn)
        buttons.addWidget(self.open_btn)
        buttons.addWidget(self.save_qr_btn)
        buttons.addWidget(self.regen_btn)
        buttons.addWidget(self.settings_btn)
        main.addLayout(buttons)
        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setMinimumHeight(120)
        main.addWidget(self.logs)
        self.toast = QLabel("")
        self.toast.setAlignment(Qt.AlignCenter)
        self.toast.hide()
        main.addWidget(self.toast)
        self.setCentralWidget(root)
        self.set_status("OFFLINE")

    def _card(self, title: str) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
        return frame

    def _add_rows(self, layout: QVBoxLayout, rows: list[tuple[str, QLabel]]) -> None:
        for name, value in rows:
            row = QHBoxLayout()
            key = QLabel(name)
            key.setStyleSheet("color:#8b949e;")
            value.setWordWrap(True)
            row.addWidget(key)
            row.addStretch(1)
            row.addWidget(value)
            layout.addLayout(row)

    def refresh_static_info(self) -> None:
        port = int(self.config["server"]["port"])
        room = self.room_manager.ensure_room(str(self.config["room"]["name"]))
        lan_ip = preferred_lan_ip()
        self.port_label.setText(str(port))
        self.lan_label.setText(f"http://{lan_ip}:{port}")
        self.localhost_label.setText(f"http://127.0.0.1:{port}")
        self.room_label.setText(room.room_id)
        self.refresh_participants()

    def refresh_participants(self) -> None:
        room = self.room_manager.current_room
        participants = self.room_manager.participants(room.room_id if room else None)
        self.users_label.setText(f"Users Online: {len(participants)}")
        if participants:
            self.participant_list.setText("\n".join(f"● {p.name}" for p in participants))
        else:
            self.participant_list.setText("No users online")

    def set_status(self, text: str) -> None:
        colors = {
            "OFFLINE": "#6e7681",
            "STARTING": "#d29922",
            "ONLINE": "#238636",
            "ERROR": "#da3633",
        }
        self.status.setText(f"● {text}")
        self.status.setStyleSheet(f"background:{colors.get(text, '#6e7681')}; color:white; padding:7px 12px; border-radius:14px;")

    def log(self, message: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{stamp}] {message}")

    def toggle_server(self) -> None:
        if self.server_runner:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self) -> None:
        port = int(self.config["server"]["port"])
        if not is_port_available(port):
            self.set_status("ERROR")
            QMessageBox.warning(self, "Port in use", f"Port {port} is already in use.")
            return
        self.set_status("STARTING")
        self.start_btn.setEnabled(False)
        self.log("Starting server...")
        self.room_manager = RoomManager(
            capacity=int(self.config["room"]["capacity"]),
            require_token=bool(self.config["room"]["requireInvitationToken"]),
        )
        self.room_manager.create_room(str(self.config["room"]["name"]))
        app = create_app(self.config, self.room_manager)
        self.server_runner = UvicornServerRunner(app, "0.0.0.0", port, self.bridge.log.emit)
        self.server_runner.start()
        self.refresh_static_info()
        self.log(f"Listening on 127.0.0.1:{port}")
        try:
            exe = cloudflared_path(self.config)
            self.tunnel = CloudflareTunnel(
                exe,
                f"http://127.0.0.1:{port}",
                self.bridge.log.emit,
                self.bridge.public_url.emit,
                self.bridge.tunnel_exit.emit,
            )
            self.tunnel_status.setText("STARTING")
            self.tunnel.start()
            self.log("Starting Cloudflare Tunnel...")
        except Exception as exc:
            self.log(f"ERROR: {exc}")
            self.tunnel_status.setText("ERROR")
        self.start_btn.setText("STOP SERVER")
        self.start_btn.setObjectName("danger")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.start_btn.setEnabled(True)
        self.regen_btn.setEnabled(True)

    def stop_server(self) -> None:
        self.log("Stopping services...")
        if self.tunnel:
            self.tunnel.stop()
            self.tunnel = None
        if self.server_runner:
            self.server_runner.stop()
            self.server_runner = None
        self.public_root_url = None
        self.invitation_url = None
        self.tunnel_status.setText("OFFLINE")
        self.public_url_label.setText("No public URL")
        self.invite_label.setText("No invitation link")
        self.qr_label.setText("QR appears after Cloudflare URL is ready")
        self.qr_label.setPixmap(QPixmap())
        self.set_status("OFFLINE")
        self.start_btn.setText("START SERVER")
        self.start_btn.setObjectName("primary")
        self.start_btn.style().unpolish(self.start_btn)
        self.start_btn.style().polish(self.start_btn)
        self.copy_btn.setEnabled(False)
        self.open_btn.setEnabled(False)
        self.save_qr_btn.setEnabled(False)
        self.regen_btn.setEnabled(False)
        self.log("Stopped")

    def on_public_url(self, url: str) -> None:
        self.public_root_url = url
        self.tunnel_status.setText("ONLINE")
        self.public_url_label.setText(url)
        self.invitation_url = self.room_manager.invitation_url(url)
        self.invite_label.setText(self.invitation_url)
        self.update_qr()
        self.set_status("ONLINE")
        self.copy_btn.setEnabled(True)
        self.open_btn.setEnabled(True)
        self.save_qr_btn.setEnabled(True)
        if self.config["ui"]["autoCopyPublicUrl"]:
            self.copy_link()
        if self.config["ui"]["autoOpenBrowser"]:
            self.open_room()
        self.log("Public URL received")

    def on_tunnel_exit(self, code: object) -> None:
        if self.server_runner:
            self.tunnel_status.setText("OFFLINE")
            self.log(f"Cloudflare Tunnel exited: {code}")

    def update_qr(self) -> None:
        if not self.invitation_url:
            return
        pixmap = QPixmap()
        pixmap.loadFromData(qr_png_bytes(self.invitation_url, box_size=10), "PNG")
        self.qr_label.setPixmap(pixmap.scaled(230, 230, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def copy_link(self) -> None:
        if self.invitation_url:
            QApplication.clipboard().setText(self.invitation_url)
            self.show_toast("Invitation link copied")

    def open_room(self) -> None:
        if self.invitation_url:
            webbrowser.open(self.invitation_url)

    def save_qr(self) -> None:
        if not self.invitation_url:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save QR", "voice-room-qr.png", "PNG Files (*.png)")
        if path:
            save_qr_png(self.invitation_url, Path(path))
            self.show_toast("QR saved")

    def regenerate_invite(self) -> None:
        if not self.public_root_url:
            self.room_manager.regenerate_invite()
            self.show_toast("Invite regenerated")
            return
        self.room_manager.regenerate_invite()
        self.invitation_url = self.room_manager.invitation_url(self.public_root_url)
        self.invite_label.setText(self.invitation_url)
        self.update_qr()
        self.show_toast("Invite regenerated")

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.Accepted:
            self.config = dialog.updated_config()
            save_config(self.config)
            self.room_manager.capacity = int(self.config["room"]["capacity"])
            self.room_manager.require_token = bool(self.config["room"]["requireInvitationToken"])
            self.refresh_static_info()
            self.show_toast("Settings saved")

    def show_toast(self, text: str) -> None:
        self.toast.setText(text)
        self.toast.setStyleSheet("background:#238636; color:white; border-radius:6px; padding:8px;")
        self.toast.show()
        QTimer.singleShot(2200, self.toast.hide)

    def closeEvent(self, event) -> None:
        self.stop_server()
        event.accept()
