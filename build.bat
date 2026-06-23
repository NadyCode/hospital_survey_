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

REM --- BAT ファイルと同じフォルダに移動（どこから実行しても正しく動く） ---
cd /d "%~dp0"

echo ============================================================
echo  病院アンケートシステム  EXE ビルド
echo ============================================================

REM ============================================================
REM  Python コマンドの自動検出（python / py の両方に対応）
REM ============================================================
set PY=
python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set PY=python
    goto :py_found
)
py --version >nul 2>&1
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
pause
exit /b 1

:py_found
echo [PY] Python コマンド: %PY%
for /f "delims=" %%V in ('%PY% --version 2^>^&1') do echo [PY] %%V

REM ============================================================
REM  バージョン番号の処理
REM ============================================================
if "%~1"=="" (
    REM 引数なし: config.py から現在のバージョンを読み取る
    for /f "delims=" %%V in ('%PY% _update_version.py --read') do set BUILD_VERSION=%%V
    if not defined BUILD_VERSION (
        echo [ERROR] config.py からバージョンを読み取れませんでした。
        pause
        exit /b 1
    )
    echo [VER] 現在のバージョン %BUILD_VERSION% を使用します。
) else (
    set BUILD_VERSION=%~1
    echo [VER] バージョンを %BUILD_VERSION% に設定します...
    %PY% _update_version.py %BUILD_VERSION%
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] config.py のバージョン更新に失敗しました。
        pause
        exit /b 1
    )
)

REM ============================================================
REM  [1/3] 依存パッケージのインストール
REM ============================================================
echo.
echo [1/3] 依存パッケージをインストール中...
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
%PY% -m pip install "pyinstaller>=5.0"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] pip install に失敗しました。
    echo         ネットワーク接続とプロキシ設定を確認してください。
    pause
    exit /b 1
)

REM ============================================================
REM  [2/3] キャッシュ削除（再ビルド時のゴミを防ぐ）
REM ============================================================
echo.
echo [2/3] 古いビルドキャッシュを削除中...
if exist build   rmdir /s /q build
if exist dist    rmdir /s /q dist

REM --- オプション: icon.ico ---
set ICON_OPT=
if exist icon.ico set ICON_OPT=--icon "icon.ico"

REM --- オプション: app_config.json ---
set CFG_OPT=
if exist app_config.json set CFG_OPT=--add-data "app_config.json;."

REM ============================================================
REM  [3/3] EXE ビルド
REM ============================================================
echo.
echo [3/3] EXE をビルド中（数分かかります）...
%PY% -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "HospitalSurvey" ^
    %ICON_OPT% ^
    %CFG_OPT% ^
    --hidden-import "matplotlib.backends.backend_tkagg" ^
    --hidden-import "matplotlib.backends.backend_agg" ^
    --collect-submodules matplotlib ^
    --hidden-import "PIL._tkinter_finder" ^
    --hidden-import "tkinter" ^
    --hidden-import "tkinter.ttk" ^
    --hidden-import "tkinter.messagebox" ^
    --hidden-import "tkinter.filedialog" ^
    --hidden-import "tkinter.simpledialog" ^
    --hidden-import "views.main_window" ^
    --hidden-import "views.styles" ^
    --hidden-import "views.respondent.survey_form" ^
    --hidden-import "views.respondent.completion_view" ^
    --hidden-import "views.respondent.result_view" ^
    --hidden-import "views.admin.login_dialog" ^
    --hidden-import "views.admin.dashboard" ^
    --hidden-import "views.admin.survey_manager" ^
    --hidden-import "views.admin.survey_editor" ^
    --hidden-import "views.admin.aggregator" ^
    --hidden-import "views.admin.user_manager" ^
    --hidden-import "views.admin.access_log_tab" ^
    --hidden-import "views.admin.settings_tab" ^
    --hidden-import "models.survey" ^
    --hidden-import "models.user" ^
    --hidden-import "utils.data_manager" ^
    --hidden-import "utils.file_lock" ^
    --hidden-import "utils.logger" ^
    --hidden-import "utils.updater" ^
    main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] ビルドに失敗しました。上記のエラーメッセージを確認してください。
    pause
    exit /b 1
)

REM --- version.txt を dist フォルダに書き出す ---
echo %BUILD_VERSION%> "dist\HospitalSurvey\version.txt"
echo [VER] dist\HospitalSurvey\version.txt に %BUILD_VERSION% を書き込みました。

echo.
echo ============================================================
echo  ビルド完了！  バージョン: %BUILD_VERSION%
echo.
echo  配布手順:
echo    1. dist\HospitalSurvey\ フォルダごと各端末にコピー
echo       （初回配布 / 手動アップデート）
echo.
echo    2. 自動アップデートで配布する場合は deploy_update.bat を実行
echo       （共有フォルダの _app_update\ に EXE + version.txt を配置）
echo ============================================================
pause
