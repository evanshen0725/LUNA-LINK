@echo off
setlocal
cd /d "%~dp0backend"
if not exist .venv py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
start "LUNA-LINK Frontend" cmd /c "cd /d %~dp0frontend && py -m http.server 5500"
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
