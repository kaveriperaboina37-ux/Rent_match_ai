@echo off
setlocal
echo ==========================================
echo RentMatch AI - Full Project Setup
echo ==========================================
python --version >nul 2>&1
if errorlevel 1 (echo Python is not installed or not on PATH.&pause&exit /b 1)
node --version >nul 2>&1
if errorlevel 1 (echo Node.js is not installed or not on PATH.&pause&exit /b 1)

if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  python -m venv .venv
)
echo Installing Python packages...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo Installing frontend packages...
cd frontend
call npm install
cd ..

if not exist "backend\.env" copy "backend\.env.example" "backend\.env" >nul

echo.
echo SETUP COMPLETE.
echo.
echo Next:
echo 1. .\start_backend.bat
echo 2. Open a SECOND terminal
echo 3. .\start_frontend.bat
echo 4. Open http://localhost:5173
echo.
pause
