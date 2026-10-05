@echo off
if not exist ".venv\Scripts\python.exe" (
 echo Virtual environment not found. Run setup.bat first.
 pause
 exit /b 1
)
cd backend
"..\.venv\Scripts\python.exe" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
