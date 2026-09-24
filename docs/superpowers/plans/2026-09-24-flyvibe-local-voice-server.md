# FlyVibe Local Voice Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a runnable Windows/Python local voice server with PySide6 UI, FastAPI single-port backend, Cloudflare tunnel integration, QR invite links, and WebRTC audio web client.

**Architecture:** The backend and browser client are decoupled by a small WebSocket protocol. The desktop app controls server and tunnel processes while reading shared room status through in-process service objects and lightweight HTTP APIs. Config and path helpers keep development and PyInstaller layouts aligned.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, PySide6, qrcode, Pillow, Vanilla JavaScript WebRTC/WebSocket, PyInstaller.

## Global Constraints
- Project folder is `C:\Users\dekso\OneDrive\เดสก์ท็อป\FlyVibe`.
- Repo remote is `https://github.com/Bunnamchaib/FlyVibe`.
- Run `python .\backup.py` before edits.
- Append to `note.md` every work round.
- Default port is `4545`.
- Do not use Tkinter for the product UI.
- Do not claim Cloudflare Tunnel replaces TURN.

---

### Task 1: Project Foundation and Tests

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `tests/test_config_and_rooms.py`
- Create: `tests/test_services.py`
- Create: `tests/test_api.py`

**Interfaces:**
- Produces tests for `load_config`, `RoomManager`, `extract_trycloudflare_url`, `is_port_available`, and `create_app`.

- [x] **Step 1: Write failing tests**
- [x] **Step 2: Run tests and confirm missing modules fail**
- [ ] **Step 3: Implement modules**
- [ ] **Step 4: Run tests and confirm pass**

### Task 2: Backend and Signaling

**Files:**
- Create: `server/app.py`
- Create: `server/rooms.py`
- Create: `server/signaling.py`
- Create: `server/models.py`
- Create: `server/__init__.py`

**Interfaces:**
- Produces `create_app(config, room_manager) -> FastAPI`.
- Produces `RoomManager` with secure invite validation and participant tracking.

### Task 3: Services

**Files:**
- Create: `services/config.py`
- Create: `services/paths.py`
- Create: `services/network.py`
- Create: `services/cloudflare.py`
- Create: `services/qr_service.py`
- Create: `services/server_runner.py`
- Create: `services/__init__.py`

**Interfaces:**
- Produces config loading, QR PNG bytes, cloudflared process manager, LAN IP/port helpers, and Uvicorn background runner.

### Task 4: Desktop UI

**Files:**
- Create: `gui/main_window.py`
- Create: `gui/__init__.py`
- Create: `main.py`

**Interfaces:**
- Produces PySide6 control panel with start/stop, public invite, QR, settings, participants, and logs.

### Task 5: Web Client

**Files:**
- Create: `web/index.html`
- Create: `web/style.css`
- Create: `web/app.js`

**Interfaces:**
- Produces responsive audio-only mesh WebRTC client using `/api/webrtc-config` and `/ws`.

### Task 6: Packaging and Docs

**Files:**
- Create: `README.md`
- Create: `runserver.bat`
- Create: `build.bat`
- Create: `build-debug.bat`
- Create: `config/config.json`

**Interfaces:**
- Produces runnable dev and PyInstaller packaging commands.

