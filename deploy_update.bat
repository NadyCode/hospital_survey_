@echo off
REM ============================================================
REM Hospital Survey System - Auto-Update Deploy Script
REM
REM Copies the built EXE and version.txt to the shared folder's
REM _app_update\ subfolder so clients auto-update on next launch.
REM
REM Usage:
REM   deploy_update.bat
REM     (reads shared_folder path from app_config.json)
REM
REM   deploy_update.bat "\\server\share\HospitalData"
REM     (specify shared folder path directly)
REM ============================================================
chcp 65001 > nul
setlocal enableextensions

REM Move to the folder where this bat file lives
cd /d "%~dp0"

echo ============================================================
echo  Hospital Survey System - Deploy Update
echo ============================================================

REM ============================================================
REM  Detect Python
REM ============================================================
set PY=

python -c "import sys" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY=python
    goto :py_found
)

py -c "import sys" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY=py
    goto :py_found
)

echo [ERROR] Python not found. Run build.bat first and install Python.
pause
exit /b 1
:py_found

REM ============================================================
REM  Check build artifacts
REM ============================================================
if not exist "dist\HospitalSurvey\HospitalSurvey.exe" (
    echo [ERROR] dist\HospitalSurvey\HospitalSurvey.exe not found.
    echo         Run build.bat first.
    pause
    exit /b 1
)
if not exist "dist\HospitalSurvey\version.txt" (
    echo [ERROR] dist\HospitalSurvey\version.txt not found.
    echo         Run build.bat first.
    pause
    exit /b 1
)

set /p NEW_VERSION=<"dist\HospitalSurvey\version.txt"
echo [VER] Deploying version: %NEW_VERSION%

REM ============================================================
REM  Resolve shared folder path
REM ============================================================
if not "%~1"=="" (
    set SHARED=%~1
    echo [DIR] Shared folder (argument): %SHARED%
) else (
    for /f "delims=" %%S in ('%PY% _update_version.py --shared-folder') do set SHARED=%%S
    echo [DIR] Shared folder (app_config.json): %SHARED%
)

REM ============================================================
REM  Copy files to _app_update\
REM ============================================================
set UPDATE_DIR=%SHARED%\_app_update
if not exist "%UPDATE_DIR%" (
    mkdir "%UPDATE_DIR%"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Cannot create %UPDATE_DIR%
        echo         Check the path and write permissions.
        pause
        exit /b 1
    )
    echo [DIR] Created %UPDATE_DIR%
)

echo [COPY] Copying HospitalSurvey.exe...
copy /Y "dist\HospitalSurvey\HospitalSurvey.exe" "%UPDATE_DIR%\HospitalSurvey.exe"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to copy EXE. Check write permissions.
    pause
    exit /b 1
)

echo [COPY] Copying version.txt...
copy /Y "dist\HospitalSurvey\version.txt" "%UPDATE_DIR%\version.txt"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to copy version.txt.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Deploy complete!  Version: %NEW_VERSION%
echo.
echo  Destination: %UPDATE_DIR%
echo.
echo  Clients will see an update dialog on next launch.
echo ============================================================
pause
endlocal
