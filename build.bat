@echo off
REM ====================================================
REM 病院アンケートシステム - Windows EXE ビルドスクリプト
REM
REM 使い方:
REM   build.bat             <- バージョン番号なし（config.py の現在値を使う）
REM   build.bat 1.2.0       <- バージョンを 1.2.0 に更新してからビルド
REM
REM 実行前に Python 3.8+ と pip が PATH に通っていることを確認してください
REM ====================================================
chcp 65001 > nul

echo ============================================================
echo  病院アンケートシステム  EXE ビルド
echo ============================================================

REM --- バージョン番号の処理 ---
if "%~1"=="" (
    REM 引数なし: config.py から現在のバージョンを読み取る
    for /f "delims=" %%V in ('python -c "from config import APP_VERSION; print(APP_VERSION)"') do set BUILD_VERSION=%%V
    echo [VER] バージョン引数なし。現在のバージョン %BUILD_VERSION% を使用します。
) else (
    set BUILD_VERSION=%~1
    echo [VER] バージョンを %BUILD_VERSION% に設定します...
    python -c "import re, sys; path='config.py'; txt=open(path,encoding='utf-8').read(); out=re.sub(r'APP_VERSION\s*=\s*\"[^\"]+\"','APP_VERSION = \"%BUILD_VERSION%\"',txt); open(path,'w',encoding='utf-8').write(out)"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] config.py のバージョン更新に失敗しました。
        pause
        exit /b 1
    )
    echo [VER] config.py を APP_VERSION = "%BUILD_VERSION%" に更新しました。
)

REM --- 依存パッケージのインストール ---
echo [1/3] 依存パッケージをインストール中...
pip install --upgrade pip
pip install -r requirements.txt
pip install "pyinstaller>=5.0"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] pip install に失敗しました。
    pause
    exit /b 1
)

REM --- キャッシュ削除（再ビルド時のゴミを防ぐ） ---
echo [2/3] 古いビルドキャッシュを削除中...
if exist build   rmdir /s /q build
if exist dist    rmdir /s /q dist

REM --- icon.ico が存在する場合だけ --icon を付与 ---
set ICON_OPT=
if exist icon.ico set ICON_OPT=--icon "icon.ico"

REM --- app_config.json が存在する場合は同梱 ---
set CFG_OPT=
if exist app_config.json set CFG_OPT=--add-data "app_config.json;."

REM --- EXE ビルド ---
echo [3/3] EXE をビルド中（数分かかります）...
pyinstaller ^
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
echo       （共有フォルダの _app_update\ に EXE+version.txt を配置）
echo ============================================================
pause
