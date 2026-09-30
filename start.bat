@echo off
echo.
echo  ╔═══════════════════════════════════════╗
echo  ║   MENTORA  -  Well-Being Tracker      ║
echo  ╚═══════════════════════════════════════╝
echo.

:: Check prerequisites
where python >nul 2>nul || (echo Python not found. Install from python.org & pause & exit /b 1)
where node   >nul 2>nul || (echo Node.js not found. Install from nodejs.org & pause & exit /b 1)
where npm    >nul 2>nul || (echo npm not found. & pause & exit /b 1)

:: Backend env
if not exist "backend\.env" (
    echo Copying backend .env.example...
    copy "backend\.env.example" "backend\.env"
    echo Edit backend\.env with your Supabase + OpenAI credentials.
)

:: Frontend env
if not exist "frontend\.env" (
    echo Copying frontend .env.example...
    copy "frontend\.env.example" "frontend\.env"
    echo Edit frontend\.env with your Supabase web configuration.
)

:: Backend
echo.
echo [Backend] Setting up Python environment...
cd backend
if not exist "venv" python -m venv venv
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
echo [Backend] Starting FastAPI on http://localhost:8000
start "Mentora Backend" cmd /k "venv\Scripts\activate && uvicorn main:app --reload --port 8000"
cd ..

:: Frontend
echo.
echo [Frontend] Installing Node dependencies...
cd frontend
if not exist "node_modules" npm install --legacy-peer-deps
echo [Frontend] Starting React on http://localhost:3000
echo.
echo ====================================================
echo   Frontend:  http://localhost:3000
echo   API:       http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo ====================================================
echo.
npm start
cd ..

