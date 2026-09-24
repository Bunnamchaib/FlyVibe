# FlyVibe Local Voice Server Design

## Goal
Build `FlyVibe`, a Windows desktop host control panel that starts one local FastAPI server on port `4545`, exposes the same app through Cloudflare Quick Tunnel, generates a QR invitation, and serves a browser-based WebRTC audio room.

## Architecture
- `main.py` starts the PySide6 desktop app.
- `server/` owns FastAPI routes, static web files, WebSocket signaling, room/token validation, and participant state.
- `services/` owns config, path lookup, LAN IP detection, port checks, QR generation, and cloudflared process control.
- `gui/` owns the modern dark host UI and uses Qt signals so server/tunnel logs never block the UI.
- `web/` is external static HTML/CSS/JavaScript using native WebRTC and WebSocket signaling.

## Rules
- Default app port is exactly `4545`.
- HTTP, static files, REST API, and WebSocket signaling use one app port.
- Cloudflare Tunnel is for HTTPS/web/API/WebSocket signaling. It is not TURN.
- WebRTC media uses browser ICE with STUN and optional TURN from `config/config.json`.
- Invitation links include room and secure token.
- No React, Vue, Node.js, npm, or Tkinter.
- Normal host flow requires no CMD.

## Implementation Strategy
Build in a single coherent version 1 while keeping modules small. Tests cover config, room/token lifecycle, cloudflared URL parsing, LAN/port helpers, and FastAPI API behavior. Manual/device testing remains required for real cross-network WebRTC media because STUN/TURN outcomes depend on network conditions.

