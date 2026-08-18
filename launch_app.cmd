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
    set "UV_EXE=%USERPROFILE%\.local\bin\uv.exe"
    if not exist "%UV_EXE%" (
        echo  uv was not found. Installing it for the current user...
        powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference = 'Stop'; $env:UV_INSTALL_DIR = Join-Path $env:USERPROFILE '.local\bin'; Invoke-RestMethod 'https://astral.sh/uv/install.ps1' | Invoke-Expression"
        if errorlevel 1 goto :uv_install_failed
    )
)

echo  Using:
call "%UV_EXE%" --version
if errorlevel 1 goto :uv_not_found
echo.

set "UV_PROJECT_ENVIRONMENT=%CD%\.venv"
echo  Creating or updating %UV_PROJECT_ENVIRONMENT% ...
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

:uv_install_failed
echo.
echo  ERROR: uv installation failed.
echo  Check your internet connection, then run this launcher again.
goto :failed

:uv_not_found
echo.
echo  ERROR: uv could not be found after setup.
echo  See https://docs.astral.sh/uv/getting-started/installation/
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
