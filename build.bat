@echo off
REM ============================================================
REM Hospital Survey System - EXE Build Script
REM
REM Usage:
REM   build.bat             (uses current version in config.py)
REM   build.bat 1.2.0       (sets version to 1.2.0 then builds)
REM
REM Requires: Python 3.8+ installed with "Add Python to PATH" checked
REM ============================================================
chcp 65001 > nul
setlocal enableextensions

REM Move to the folder where this bat file lives
cd /d "%~dp0"

echo ============================================================
echo  Hospital Survey System - EXE Build
echo ============================================================

REM ============================================================
REM  Detect Python
REM  Use -c "import sys" to reject Windows Store stub
REM  (the stub returns ERRORLEVEL 0 for --version but does nothing)
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

echo.
echo [ERROR] Python not found.
echo.
echo  Install Python 3.8 or later:
echo    1. Go to https://www.python.org/downloads/
echo    2. Click "Download Python 3.x.x"
echo    3. Run the installer
echo    4. CHECK "Add Python to PATH" on the first screen
echo    5. Click "Install Now"
echo    6. Re-run this bat after installation
echo.
echo  NOTE: The Windows Store Python stub cannot be used.
echo        Please install directly from python.org.
echo.
pause
exit /b 1

:py_found
for /f "delims=" %%V in ('%PY% --version 2^>^&1') do echo [PY] %%V

REM ============================================================
REM  Version handling
REM ============================================================
if "%~1"=="" (
    for /f "delims=" %%V in ('%PY% _update_version.py --read') do set BUILD_VERSION=%%V
    if not defined BUILD_VERSION (
        echo [ERROR] Could not read version from config.py
        pause
        exit /b 1
    )
    echo [VER] Using current version: %BUILD_VERSION%
) else (
    set BUILD_VERSION=%~1
    echo [VER] Setting version to: %BUILD_VERSION%
    %PY% _update_version.py %BUILD_VERSION%
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to update version in config.py
        pause
        exit /b 1
    )
)

REM ============================================================
REM  [1/3] Install dependencies
REM ============================================================
echo.
echo [1/3] Installing dependencies...
%PY% -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 goto :pip_error
%PY% -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 goto :pip_error
%PY% -m pip install "pyinstaller>=5.0"
if %ERRORLEVEL% neq 0 goto :pip_error
goto :pip_ok
:pip_error
echo [ERROR] pip install failed. Check network/proxy settings.
pause
exit /b 1
:pip_ok

REM ============================================================
REM  [2/3] Clean old cache
REM ============================================================
echo.
echo [2/3] Cleaning old build cache...
if exist build   rmdir /s /q build
if exist dist    rmdir /s /q dist

set ICON_OPT=
if exist icon.ico set ICON_OPT=--icon "icon.ico"

set CFG_OPT=
if exist app_config.json set CFG_OPT=--add-data "app_config.json;."

REM ============================================================
REM  [3/3] Build EXE
REM ============================================================
echo.
echo [3/3] Building EXE (this may take a few minutes)...

%PY% -m PyInstaller --noconfirm --onedir --windowed --name "HospitalSurvey" %ICON_OPT% %CFG_OPT% --hidden-import "matplotlib.backends.backend_tkagg" --hidden-import "matplotlib.backends.backend_agg" --collect-submodules matplotlib --hidden-import "PIL._tkinter_finder" --hidden-import "tkinter" --hidden-import "tkinter.ttk" --hidden-import "tkinter.messagebox" --hidden-import "tkinter.filedialog" --hidden-import "tkinter.simpledialog" --hidden-import "views.main_window" --hidden-import "views.styles" --hidden-import "views.respondent.survey_form" --hidden-import "views.respondent.completion_view" --hidden-import "views.respondent.result_view" --hidden-import "views.admin.login_dialog" --hidden-import "views.admin.dashboard" --hidden-import "views.admin.survey_manager" --hidden-import "views.admin.survey_editor" --hidden-import "views.admin.aggregator" --hidden-import "views.admin.user_manager" --hidden-import "views.admin.access_log_tab" --hidden-import "views.admin.settings_tab" --hidden-import "models.survey" --hidden-import "models.user" --hidden-import "utils.data_manager" --hidden-import "utils.file_lock" --hidden-import "utils.logger" --hidden-import "utils.updater" main.py

if %ERRORLEVEL% neq 0 (
    echo [ERROR] Build failed. See messages above.
    pause
    exit /b 1
)

REM Write version.txt
if not exist "dist\HospitalSurvey" mkdir "dist\HospitalSurvey"
(echo %BUILD_VERSION%)>"dist\HospitalSurvey\version.txt"
echo [VER] Wrote version.txt: %BUILD_VERSION%

echo.
echo ============================================================
echo  Build complete!  Version: %BUILD_VERSION%
echo.
echo  Distribution:
echo    1. Copy dist\HospitalSurvey\ folder to each PC
echo       (first install / manual update)
echo.
echo    2. For auto-update: run deploy_update.bat
echo       (copies EXE + version.txt to shared folder\_app_update\)
echo ============================================================
pause
endlocal
