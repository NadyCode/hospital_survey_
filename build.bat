@echo off
REM ====================================================
REM 病院アンケートシステム - Windows EXE ビルドスクリプト
REM
REM 使い方:
REM   build.bat             バージョン番号なし（config.py の現在値を使う）
REM   build.bat 1.2.0       バージョンを 1.2.0 に更新してからビルド
REM
REM 必要環境: Python 3.8 以上（インストール時に "Add Python to PATH" にチェック）
REM ====================================================
chcp 65001 > nul
setlocal enableextensions

REM --- BAT ファイルと同じフォルダに移動（どこから実行しても正しく動く） ---
cd /d "%~dp0"

echo ============================================================
echo  EXE Build
echo ============================================================

REM ============================================================
REM  Python の検出
REM  注意: Windows 10/11 の "python" はストアスタブの場合がある。
REM        -c "import sys" で本物かどうか確認する。
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
echo [ERROR] Python が見つかりません。
echo.
echo  以下の手順でインストールしてください:
echo    1. https://www.python.org/downloads/ を開く
echo    2. "Download Python 3.x.x" をクリック
echo    3. インストーラーを起動し、最初の画面で
echo       "Add Python to PATH" に必ずチェックを入れる
echo    4. "Install Now" をクリック
echo    5. インストール完了後、このバッチを再実行する
echo.
echo  ※ Windows ストアの Python スタブは使用できません。
echo    上記 URL から直接インストールしてください。
echo.
pause
exit /b 1

:py_found
for /f "delims=" %%V in ('%PY% --version 2^>^&1') do echo [PY] %%V

REM ============================================================
REM  バージョン番号の処理
REM ============================================================
if "%~1"=="" (
    for /f "delims=" %%V in ('%PY% _update_version.py --read') do set BUILD_VERSION=%%V
    if not defined BUILD_VERSION (
        echo [ERROR] config.py からバージョンを読み取れませんでした。
        pause
        exit /b 1
    )
    echo [VER] Current version: %BUILD_VERSION%
) else (
    set BUILD_VERSION=%~1
    echo [VER] Setting version to: %BUILD_VERSION%
    %PY% _update_version.py %BUILD_VERSION%
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] config.py version update failed.
        pause
        exit /b 1
    )
)

REM ============================================================
REM  [1/3] 依存パッケージのインストール
REM ============================================================
echo.
echo [1/3] Installing packages...
%PY% -m pip install --upgrade pip
if %ERRORLEVEL% neq 0 goto :pip_error
%PY% -m pip install -r requirements.txt
if %ERRORLEVEL% neq 0 goto :pip_error
%PY% -m pip install "pyinstaller>=5.0"
if %ERRORLEVEL% neq 0 goto :pip_error
goto :pip_ok
:pip_error
echo.
echo [ERROR] pip install failed.
pause
exit /b 1
:pip_ok

REM ============================================================
REM  [2/3] キャッシュ削除
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
REM  [3/3] EXE ビルド
REM ============================================================
echo.
echo [3/3] Building EXE (this may take a few minutes)...

%PY% -m PyInstaller --noconfirm --onedir --windowed --name "HospitalSurvey" %ICON_OPT% %CFG_OPT% --hidden-import "matplotlib.backends.backend_tkagg" --hidden-import "matplotlib.backends.backend_agg" --collect-submodules matplotlib --hidden-import "PIL._tkinter_finder" --hidden-import "tkinter" --hidden-import "tkinter.ttk" --hidden-import "tkinter.messagebox" --hidden-import "tkinter.filedialog" --hidden-import "tkinter.simpledialog" --hidden-import "views.main_window" --hidden-import "views.styles" --hidden-import "views.respondent.survey_form" --hidden-import "views.respondent.completion_view" --hidden-import "views.respondent.result_view" --hidden-import "views.admin.login_dialog" --hidden-import "views.admin.dashboard" --hidden-import "views.admin.survey_manager" --hidden-import "views.admin.survey_editor" --hidden-import "views.admin.aggregator" --hidden-import "views.admin.user_manager" --hidden-import "views.admin.access_log_tab" --hidden-import "views.admin.settings_tab" --hidden-import "models.survey" --hidden-import "models.user" --hidden-import "utils.data_manager" --hidden-import "utils.file_lock" --hidden-import "utils.logger" --hidden-import "utils.updater" main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Build failed. Check the messages above.
    pause
    exit /b 1
)

REM --- version.txt を出力 ---
if not exist "dist\HospitalSurvey" mkdir "dist\HospitalSurvey"
(echo %BUILD_VERSION%)>"dist\HospitalSurvey\version.txt"
echo [VER] Wrote dist\HospitalSurvey\version.txt : %BUILD_VERSION%

echo.
echo ============================================================
echo  Build complete!  Version: %BUILD_VERSION%
echo.
echo  Distribution:
echo    1. Copy the dist\HospitalSurvey\ folder to each PC
echo       (first-time install / manual update)
echo.
echo    2. For auto-update distribution, run deploy_update.bat
echo       (copies EXE + version.txt to shared folder\_app_update\)
echo ============================================================
pause
endlocal
