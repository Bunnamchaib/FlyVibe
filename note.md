# FlyVibe Work Note

## 2026-09-24 15:19 (+07:00) - รอบแรก: ตั้งต้นโปรเจกต์และอ่านความต้องการ

### ทำอะไรไปแล้ว
- ใช้โฟลเดอร์หลัก: `C:\Users\dekso\OneDrive\เดสก์ท็อป\FlyVibe`
- คัดลอก `backup.py` จาก `D:\NAMCHAI\cost v3\backup.py` มาไว้ในโฟลเดอร์หลักแล้ว
- รัน `backup.py` ก่อนแก้ไฟล์ และสร้างแบคอัพแล้วที่ `backup\backup FlyVibe 24092026 15 19.zip`
- อ่านกฎจาก `D:\NAMCHAI\cost v3\DevRoule.md` แล้ว
- อ่านไฟล์ความต้องการที่แนบมาแล้ว: ต้องสร้างแอป Windows ชื่อโครงการ `FlyVibe` สำหรับ Local Voice Server

### เข้าใจความต้องการหลัก
- ต้องสร้างแอป Windows/Python ที่ host เปิด EXE แล้วเริ่ม FastAPI server, WebSocket signaling, Cloudflare Tunnel, QR invite และห้องเสียง WebRTC ได้จริง
- ใช้พอร์ตแอปเดียวเป็นค่าเริ่มต้นคือ `4545`
- Frontend ใช้ HTML/CSS/Vanilla JS ไม่ใช้ React/Vue/Node/npm ถ้าไม่จำเป็น
- Desktop GUI ใช้ PySide6 หน้าตา dark professional มีสถานะ server/tunnel, public URL, QR, participants, logs และ settings
- WebRTC เป็น audio-only mesh สำหรับผู้ใช้ประมาณ 2-6 คน มี STUN และเตรียม config TURN ไว้
- Invitation ต้องมี room id และ secure token; regenerate invite ต้องทำให้ token เก่าใช้ไม่ได้
- Cloudflare Tunnel ใช้สำหรับ HTTPS/web/API/WebSocket signaling เท่านั้น ไม่ใช่ TURN relay

### ปัญหา/ข้อควรระวัง
- โปรเจกต์ตอนนี้ยังว่างเกือบทั้งหมด มีแค่ `backup.py`, โฟลเดอร์ `backup`, และ `note.md`
- งานใหญ่และมีหลายเฟส ต้องทำทีละเฟสตามลำดับ ไม่ควรเขียนทุกอย่างรวดเดียวแบบเสี่ยงพัง
- ต้องตรวจจริงทุกครั้งหลังแก้โค้ด เช่น syntax, route, WebSocket, GUI launch, process cleanup
- ต้องไม่อ้างว่า Cloudflare Tunnel แก้ปัญหา WebRTC media/NAT ได้ทั้งหมด เพราะบางเครือข่ายต้องใช้ TURN

### จะทำอะไรต่อ
- ก่อนแก้โค้ดครั้งถัดไป ต้องรัน `python .\backup.py` จากโฟลเดอร์หลักก่อนเสมอ
- ออกแบบแผนพัฒนาแบบ phase ตาม requirement ก่อนเริ่มเขียนโค้ด
- เริ่มจากโครงสร้างโปรเจกต์และ Phase 1: FastAPI static server พอร์ต `4545`
- บันทึก `note.md` ต่อท้ายทุกครั้ง ไม่ทับของเก่า

## 2026-09-24 15:22 (+07:00) - รอบสอง: รับกติกา Repo และ Push

### ทำอะไรไปแล้ว
- รัน `python .\backup.py` ก่อนแก้ `note.md` ตามกฎ
- รับข้อมูล repo หลักของโปรเจกต์: `https://github.com/Bunnamchaib/FlyVibe`
- รับกติกา push: เมื่อมีการเปลี่ยนแปลงใหญ่ หรือแก้ประมาณ 5 ครั้ง ให้ push 1 ครั้ง
- ตรวจ git แล้วพบว่า `FlyVibe` ตอนนี้ยังไม่ได้เป็น git repo แยกของตัวเอง

### ปัญหา/ข้อควรระวัง
- `git rev-parse --show-toplevel` คืนค่าเป็น `C:\Users\dekso` ไม่ใช่ `C:\Users\dekso\OneDrive\เดสก์ท็อป\FlyVibe`
- remote ปัจจุบันเป็น `https://github.com/Thaicubic/APM-MEETING.git` ซึ่งไม่ใช่ repo ของ `FlyVibe`
- ห้าม push จากสถานะนี้ เพราะเสี่ยง push ผิด repo

### จะทำอะไรต่อ
- ก่อนเริ่มพัฒนาโค้ดจริง ต้องจัด git repo ให้ถูกต้องในโฟลเดอร์ `FlyVibe`
- remote ที่ถูกต้องต้องเป็น `https://github.com/Bunnamchaib/FlyVibe`
- backup ทุกรอบก่อนแก้ไฟล์ยังต้องทำเหมือนเดิม

## 2026-09-24 15:38 (+07:00) - รอบสาม: สร้าง FlyVibe Local Voice Server v0.1.0

### ทำอะไรไปแล้ว
- รัน `backup.py` ก่อนเริ่มแก้ไฟล์ และรัน backup อีกครั้งก่อนอัปเดต note รอบสรุป
- Init git repo แยกในโฟลเดอร์ `FlyVibe` แล้ว และตั้ง remote เป็น `https://github.com/Bunnamchaib/FlyVibe.git`
- สร้างโครงสร้างโปรเจกต์ครบ: `server`, `services`, `gui`, `web`, `config`, `tests`, `docs`
- สร้าง PySide6 Host Control Panel ไม่ใช้ Tkinter
- สร้าง FastAPI server ใช้พอร์ตเดียว `4545` สำหรับ `/`, static web, REST API และ WebSocket `/ws`
- สร้าง room/token system: room id 6 ตัว, secure token, regenerate invite, capacity default 6
- สร้าง WebSocket signaling สำหรับ join, offer, answer, ice, leave, peer-left
- สร้าง web client HTML/CSS/Vanilla JS สำหรับ WebRTC audio-only mesh, mute, remote audio mute, leave, reconnect
- เพิ่ม Cloudflare Tunnel integration: run `cloudflared.exe tunnel --url http://127.0.0.1:4545`, อ่าน log, parse `https://*.trycloudflare.com`
- เพิ่ม QR generation, copy link, save QR, open room, settings dialog
- เพิ่ม `README.md`, `requirements.txt`, `runserver.bat`, `build.bat`, `build-debug.bat`
- Build EXE สำเร็จที่ `dist\VoiceServer\VoiceServer.exe` และ copy `cloudflared.exe` ไปไว้ข้าง EXE แล้ว

### ตรวจสอบแล้ว
- `python -m pytest -q`: ผ่าน 9 tests
- `python -m compileall main.py server services gui`: ผ่าน
- Smoke server จริงบน `127.0.0.1:4545`: `/`, `/api/status`, `/api/webrtc-config` และ WebSocket join ผ่าน
- GUI smoke ด้วย PySide6 offscreen: เปิด/ปิดได้ exit code 0
- `cloudflared.exe --version`: ผ่าน เป็น version 2026.3.0
- Quick Tunnel smoke: สร้าง public URL ได้จริง และ parse URL ได้
- `build.bat`: PyInstaller build ผ่าน
- Smoke `dist\VoiceServer\VoiceServer.exe`: process เปิดอยู่หลัง 4 วินาที แล้วสั่งหยุดได้

### ปัญหา/ข้อควรระวัง
- เครื่องนี้ใช้ Python 3.14 ทำให้ `PySide6==6.9.1` ลงไม่ได้ จึงปรับ `requirements.txt` เป็น `PySide6>=6.10.1,<6.12`
- ยังไม่ได้ทดสอบเสียง WebRTC จริงด้วยมือถือ 2 เครื่องข้ามเครือข่าย ต้องทดสอบจริงภายหลัง
- STUN อย่างเดียวอาจไม่ผ่านบาง NAT/firewall ต้องตั้ง TURN ใน `config/config.json` ถ้า peer connection fail
- Cloudflare Tunnel ใช้สำหรับ HTTPS/web/API/WebSocket signaling เท่านั้น ไม่ใช่ TURN relay
- โฟลเดอร์ `dist` และ `build` ถูก ignore ใน git แต่มีไฟล์ build อยู่ในเครื่องแล้ว

### จะทำอะไรต่อ
- ทดสอบจริงด้วยมือถือ 2 เครื่องหรือมือถือ+PC ผ่าน public QR
- ถ้า WebRTC media fail ให้เพิ่ม TURN server ใน config
- ก่อนแก้ครั้งต่อไปให้รัน `python .\backup.py` ก่อนเสมอ
- เมื่อพร้อม push ให้ commit เฉพาะ source/docs/tests ไม่รวม `backup`, `build`, `dist`, `cloudflared.exe`

## 2026-09-24 15:40 (+07:00) - รอบสี่: Commit และ Push

### ทำอะไรไปแล้ว
- รัน `backup.py` ก่อนแก้ note
- Commit งานหลักแล้ว: `2f68490 feat: build local voice server`
- Push เข้า repo `https://github.com/Bunnamchaib/FlyVibe.git` branch `main` สำเร็จ

### ปัญหา/ข้อควรระวัง
- ไฟล์ release ใน `dist` อยู่ในเครื่อง แต่ไม่ได้ push เพราะถูก ignore
- `cloudflared.exe` อยู่ในเครื่องและใน `dist\VoiceServer` แต่ไม่ได้ push เพราะไฟล์ใหญ่และถูก ignore

### จะทำอะไรต่อ
- ทดสอบจริงจาก `dist\VoiceServer\VoiceServer.exe` กับมือถือ 2 เครื่อง
- ถ้าทดสอบผ่านจริง ค่อย tag/release หรือแนบ zip release ภายหลัง
