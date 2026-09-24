@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
python -m PyInstaller --noconsole --name VoiceServer --add-data "web;web" --add-data "config;config" main.py
if exist "cloudflared.exe" copy /Y "cloudflared.exe" "dist\VoiceServer\cloudflared.exe"
