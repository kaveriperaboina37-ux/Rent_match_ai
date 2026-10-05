@echo off
if not exist "frontend\node_modules" (
 echo Frontend dependencies not found. Run setup.bat first.
 pause
 exit /b 1
)
cd frontend
call npm run dev -- --host 127.0.0.1
