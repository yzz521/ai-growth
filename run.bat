@echo off
setlocal
cd /d %~dp0
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env
for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do if not "%%A"=="" set "%%A=%%B"
python -m uvicorn app.main:app --host "%AGW_HOST%" --port "%AGW_PORT%" --reload
endlocal
