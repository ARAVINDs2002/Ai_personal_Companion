@echo off
setlocal enabledelayedexpansion

:: ============================================================
:: AI Companion - Ultimate One-Click Launcher (Final)
:: ============================================================

set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"

echo.
echo  [1/6] Checking Prerequisites...
echo.

:: 1. Check Ollama
echo [+] Checking for Ollama...
where ollama >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [!] ERROR: Ollama is not installed.
    echo [!] Download from: https://ollama.com/download
    pause
    exit /b 1
)
echo [+] Ollama found.

:: 2. Check Conda
echo [+] Checking for Conda...
set "CONDA_PATH="
for /f "tokens=*" %%i in ('where conda 2^>nul') do (set "CONDA_PATH=%%i" & goto :found_c)
if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" set "CONDA_PATH=%USERPROFILE%\miniconda3\Scripts\conda.exe"
if exist "%USERPROFILE%\anaconda3\Scripts\conda.exe" set "CONDA_PATH=%USERPROFILE%\anaconda3\Scripts\conda.exe"
:found_c

if not defined CONDA_PATH (
    echo [!] ERROR: Miniconda/Anaconda not found.
    echo [!] Download from: https://docs.anaconda.com/miniconda/
    pause
    exit /b 1
)
echo [+] Conda found at: "%CONDA_PATH%"

:: Find activation script
for %%A in ("%CONDA_PATH%") do set "CONDA_BASE=%%~dpA.."
set "CONDA_BAT=%CONDA_BASE%\condabin\conda.bat"
if not exist "%CONDA_BAT%" set "CONDA_BAT=%CONDA_BASE%\Scripts\conda.bat"

if not exist "%CONDA_BAT%" (
    echo [!] ERROR: Could not find conda.bat.
    pause
    exit /b 1
)

echo.
echo  [2/6] Preparing Python Environment...
echo.

echo [+] Checking for 'ai_companion' environment...
set "ENV_EXISTS=n"
for /f "tokens=*" %%i in ('"%CONDA_PATH%" env list') do (
    echo %%i | findstr /c:"ai_companion" >nul
    if !ERRORLEVEL! equ 0 set "ENV_EXISTS=y"
)

if "%ENV_EXISTS%"=="n" (
    echo [+] Environment 'ai_companion' not found. Creating it...
    "%CONDA_PATH%" create -n ai_companion python=3.10 -y
    if !ERRORLEVEL! neq 0 (
        echo [!] Failed to create environment.
        pause
        exit /b 1
    )
)

echo [+] Updating dependencies...
call "%CONDA_BAT%" activate ai_companion && pip install -r backend/requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo [!] ERROR: Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo  [3/6] Initializing Ollama...
echo.

echo [+] Ensuring Ollama service is running...
start /min "" ollama serve
timeout /t 3 >nul

echo [+] Pulling model 'dolphin-mistral'...
ollama pull dolphin-mistral

echo.
echo  [4/6] Starting Backend...
echo.

start "AI Companion Backend" cmd /k "call "%CONDA_BAT%" activate ai_companion && cd /d "%PROJECT_ROOT%backend" && python -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo [+] Waiting for backend...
:wait_backend
curl -s http://127.0.0.1:8000/profile >nul 2>nul
if %ERRORLEVEL% neq 0 (
    timeout /t 1 >nul
    goto :wait_backend
)
echo [+] Backend up!

echo.
echo  [5/6] Starting Frontend Server...
echo.
start "AI Companion Frontend" /min cmd /k "cd /d "%PROJECT_ROOT%" && python -m http.server 3000"

echo.
echo  [6/6] Launching App...
echo.
timeout /t 2 >nul
:: Open the root URL; the new index.html will redirect to the correct folder automatically
start "" "http://localhost:3000"

echo.
echo ==========================================
echo    DONE! AI Companion is now running.
echo ==========================================
pause