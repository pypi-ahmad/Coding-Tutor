@echo off
setlocal EnableDelayedExpansion

echo ============================================================
echo  Coding Tutor — Local Launcher
echo ============================================================
echo.

:: ── 1. Verify uv is installed ────────────────────────────────
where uv >nul 2>&1
if errorlevel 1 (
    echo  ERROR: uv is not installed or not on PATH.
    echo.
    echo  Install uv from the official installer:
    echo    https://docs.astral.sh/uv/getting-started/installation/
    echo.
    echo  On Windows you can run:
    echo    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    echo  After installing, open a new terminal and run this launcher again.
    echo.
    pause
    exit /b 1
)

echo  uv found:
uv --version
echo.

:: ── 2. Move into the script directory ────────────────────────
cd /d "%~dp0"

:: ── 3. Sync / install dependencies ───────────────────────────
echo  Installing / synchronising dependencies...
uv sync --frozen 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Dependency installation failed.
    echo  Check the error above and ensure pyproject.toml is present.
    echo.
    pause
    exit /b 1
)
echo.

:: ── 4. Check for .env ─────────────────────────────────────────
if not exist ".env" (
    echo  NOTE: .env file not found.
    echo  Copy .env.example to .env and add your API key(s) before
    echo  using AI features. The app will still start without keys.
    echo.
)

:: ── 5. Launch Streamlit ───────────────────────────────────────
echo  Starting Coding Tutor at http://127.0.0.1:8551 ...
echo  Press Ctrl+C to stop the server.
echo.
uv run streamlit run app.py --server.address 127.0.0.1 --server.port 8551
if errorlevel 1 (
    echo.
    echo  ERROR: Streamlit failed to start.
    echo  Check the output above for details.
    echo.
    pause
    exit /b 1
)

endlocal
