@echo off
setlocal
title Coding Tutor

cd /d "%~dp0"

echo ============================================================
echo  Coding Tutor - local setup and launcher
echo ============================================================
echo.

set "UV_EXE=uv"
where uv >nul 2>&1
if errorlevel 1 (
    echo  ERROR: uv is not installed or is not available on PATH.
    echo  Install uv, then run this launcher again:
    echo  https://docs.astral.sh/uv/getting-started/installation/
    echo  Official Windows installer: https://astral.sh/uv/install.ps1
    goto :failed
)

echo  Using:
call "%UV_EXE%" --version
if errorlevel 1 goto :uv_not_found
echo.

set "UV_PROJECT_ENVIRONMENT=%CD%\.venv"
if not exist "%UV_PROJECT_ENVIRONMENT%\Scripts\python.exe" (
    echo  Creating %UV_PROJECT_ENVIRONMENT% ...
    call "%UV_EXE%" venv "%UV_PROJECT_ENVIRONMENT%"
    if errorlevel 1 goto :venv_failed
    echo.
)

echo  Synchronizing dependencies in %UV_PROJECT_ENVIRONMENT% ...
call "%UV_EXE%" sync --locked
if errorlevel 1 goto :sync_failed
echo.

echo  Starting Coding Tutor at http://127.0.0.1:8551 ...
echo  Press Ctrl+C to stop the server.
echo.
call "%UV_EXE%" run --locked streamlit run app.py --server.address 127.0.0.1 --server.port 8551
if errorlevel 1 goto :launch_failed

endlocal
exit /b 0

:uv_not_found
echo.
echo  ERROR: uv could not be found after setup.
echo  See https://docs.astral.sh/uv/getting-started/installation/
goto :failed

:venv_failed
echo.
echo  ERROR: The project virtual environment could not be created.
echo  Check the uv output above and confirm this folder is writable.
goto :failed

:sync_failed
echo.
echo  ERROR: Dependency setup failed.
echo  Check the output above and confirm pyproject.toml and uv.lock are present.
goto :failed

:launch_failed
echo.
echo  ERROR: Streamlit failed to start.
echo  Check the output above for details.

:failed
echo.
pause
endlocal
exit /b 1
