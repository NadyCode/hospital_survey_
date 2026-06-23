@echo off
REM ====================================================
REM 病院アンケートシステム - 自動更新配布スクリプト
REM
REM ビルド後に実行することで、共有フォルダの _app_update\ に
REM 最新 EXE と version.txt を配置します。
REM 次回各端末起動時に自動更新が適用されます。
REM
REM 使い方:
REM   deploy_update.bat
REM     -> app_config.json の shared_folder を読んで配置先を自動検出
REM
REM   deploy_update.bat "\\server\share\HospitalData"
REM     -> 共有フォルダのパスを直接指定
REM ====================================================
chcp 65001 > nul

echo ============================================================
echo  病院アンケートシステム  自動更新配布
echo ============================================================

REM --- ビルド成果物の確認 ---
if not exist "dist\HospitalSurvey\HospitalSurvey.exe" (
    echo [ERROR] dist\HospitalSurvey\HospitalSurvey.exe が見つかりません。
    echo         先に build.bat を実行してください。
    pause
    exit /b 1
)
if not exist "dist\HospitalSurvey\version.txt" (
    echo [ERROR] dist\HospitalSurvey\version.txt が見つかりません。
    echo         先に build.bat を実行してください。
    pause
    exit /b 1
)

REM --- バージョン確認 ---
set /p NEW_VERSION=<"dist\HospitalSurvey\version.txt"
echo [VER] 配布するバージョン: %NEW_VERSION%

REM --- 共有フォルダの特定 ---
if not "%~1"=="" (
    set SHARED=%~1
    echo [DIR] 共有フォルダ（引数指定）: %SHARED%
) else (
    REM app_config.json から shared_folder を読み取る
    if not exist app_config.json (
        echo [WARN] app_config.json が見つかりません。デフォルト "data" フォルダを使用します。
        set SHARED=data
    ) else (
        for /f "usebackq delims=" %%S in (`python -c "import json; d=json.load(open('app_config.json',encoding='utf-8')); print(d.get('shared_folder','data'))"`) do set SHARED=%%S
    )
    echo [DIR] 共有フォルダ（設定ファイル）: %SHARED%
)

REM --- 配置先ディレクトリの作成 ---
set UPDATE_DIR=%SHARED%\_app_update
if not exist "%UPDATE_DIR%" (
    mkdir "%UPDATE_DIR%"
    echo [DIR] %UPDATE_DIR% を作成しました。
)

REM --- ファイルのコピー ---
echo [COPY] HospitalSurvey.exe をコピー中...
copy /Y "dist\HospitalSurvey\HospitalSurvey.exe" "%UPDATE_DIR%\HospitalSurvey.exe"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] EXE のコピーに失敗しました。共有フォルダへのアクセス権を確認してください。
    pause
    exit /b 1
)

echo [COPY] version.txt をコピー中...
copy /Y "dist\HospitalSurvey\version.txt" "%UPDATE_DIR%\version.txt"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] version.txt のコピーに失敗しました。
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  配布完了！  バージョン: %NEW_VERSION%
echo.
echo  配置先: %UPDATE_DIR%
echo.
echo  各端末が次回起動時に自動更新ダイアログを表示し、
echo  承認後に新しい EXE が適用されます。
echo ============================================================
pause
