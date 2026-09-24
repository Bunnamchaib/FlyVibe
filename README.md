# FlyVibe Local Voice Server

FlyVibe is a Windows host application for small private WebRTC voice rooms. The host opens `VoiceServer.exe`, starts one local FastAPI server on port `4545`, starts Cloudflare Quick Tunnel, receives a public HTTPS URL, generates a QR invitation, and lets phones or computers join an audio-only voice room in the browser.

## Requirements
- Windows 10 or Windows 11 64-bit
- Python 3.11+
- `cloudflared.exe` beside `main.py` during development or beside `VoiceServer.exe` in release
- Microphone-capable browser: Chrome, Edge, Android Chrome, iPhone Safari where WebRTC is supported

## Setup
```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Run Development Version
```bat
runserver.bat
```

The app opens a PySide6 host control panel. Click `START SERVER`. The app checks port `4545`, starts FastAPI/Uvicorn, starts `cloudflared.exe tunnel --url http://127.0.0.1:4545`, detects the `https://xxxxx.trycloudflare.com` URL, and generates a QR code.

## Build EXE
```bat
build.bat
```

Debug console build:
```bat
build-debug.bat
```

Final files should include:
```text
dist\VoiceServer\VoiceServer.exe
dist\VoiceServer\cloudflared.exe
dist\VoiceServer\web\
```

## cloudflared.exe
Place `cloudflared.exe` in the project root for development:
```text
C:\Users\dekso\OneDrive\เดสก์ท็อป\FlyVibe\cloudflared.exe
```

For release, place it beside `VoiceServer.exe`.

## One-Port Architecture
FlyVibe uses one application port, default `4545`, for:
- HTML/CSS/JS
- REST API
- WebSocket signaling
- room status
- host dashboard status

WebRTC media is not forced through port `4545`. Audio media uses browser ICE.

## WebRTC, STUN, TURN
Cloudflare Tunnel gives a public HTTPS page and WebSocket signaling endpoint. It does not replace TURN and does not relay WebRTC media.

The default config includes Google STUN:
```json
{
  "urls": ["stun:stun.l.google.com:19302"]
}
```

Some networks cannot connect peer-to-peer with STUN only. In that case, add a real TURN server in `config/config.json`:
```json
{
  "turn": {
    "enabled": true,
    "urls": ["turn:turn.example.com:3478"],
    "username": "user",
    "credential": "pass"
  }
}
```

## Testing With Two Devices
1. On PC A, run `VoiceServer.exe` or `runserver.bat`.
2. Click `START SERVER`.
3. Wait for `ONLINE`, public URL, and QR.
4. On Phone B, scan QR, enter a name, allow microphone, join.
5. On Phone C or PC C, open the same invitation, enter another name, allow microphone, join.
6. Confirm both clients can hear each other, mute works, leaving removes the participant, and the host dashboard count updates.

Test across different networks. Localhost-only testing is not enough.

## Microphone Notes
Browsers usually require a secure context for microphone access. Cloudflare public URLs are HTTPS. `localhost` is also treated as secure. LAN HTTP URLs such as `http://192.168.x.x:4545` may not allow microphone access in all browsers.

## Windows Firewall
Windows may ask whether Python or `VoiceServer.exe` can accept private network connections. Allow private networks if you want LAN access. Do not disable firewall protection. Cloudflare Tunnel itself uses outbound connections.

## Troubleshooting
- `Port 4545 is already in use`: change the port in Settings or stop the other program.
- `cloudflared.exe not found`: put `cloudflared.exe` beside the app or set the path in Settings.
- `Invalid or expired invitation`: use the latest QR/link after regenerating invite or restarting tunnel.
- `Unable to establish peer connection`: the network may require TURN. Configure TURN in `config/config.json`.
- Microphone denied: refresh the page and allow microphone permission.

