@echo off
REM ====================================================
REM 病院アンケートシステム - 自動更新配布スクリプト
REM
REM ビルド後に実行すると、共有フォルダの _app_update\ に
REM 最新 EXE と version.txt を配置します。
REM 次回各端末の起動時に自動更新が適用されます。
REM
REM 使い方:
REM   deploy_update.bat
REM     -> app_config.json の shared_folder を自動検出
REM
REM   deploy_update.bat "\\server\share\HospitalData"
REM     -> 共有フォルダのパスを直接指定
REM ====================================================
chcp 65001 > nul

REM --- BAT ファイルと同じフォルダに移動 ---
cd /d "%~dp0"

echo ============================================================
echo  病院アンケートシステム  自動更新配布
echo ============================================================

REM ============================================================
REM  Python コマンドの自動検出
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
echo [ERROR] Python が見つかりません。build.bat を先に実行し、Python をインストールしてください。
pause
exit /b 1
:py_found

REM ============================================================
REM  ビルド成果物の確認
REM ============================================================
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

REM ============================================================
REM  共有フォルダの特定
REM ============================================================
if not "%~1"=="" (
    set SHARED=%~1
    echo [DIR] 共有フォルダ（引数指定）: %SHARED%
) else (
    for /f "delims=" %%S in ('%PY% _update_version.py --shared-folder') do set SHARED=%%S
    echo [DIR] 共有フォルダ: %SHARED%
)

REM ============================================================
REM  _app_update フォルダへ配置
REM ============================================================
set UPDATE_DIR=%SHARED%\_app_update
if not exist "%UPDATE_DIR%" (
    mkdir "%UPDATE_DIR%"
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] %UPDATE_DIR% を作成できませんでした。
        echo         フォルダのパスとアクセス権を確認してください。
        pause
        exit /b 1
    )
    echo [DIR] %UPDATE_DIR% を作成しました。
)

echo [COPY] HospitalSurvey.exe をコピー中...
copy /Y "dist\HospitalSurvey\HospitalSurvey.exe" "%UPDATE_DIR%\HospitalSurvey.exe"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] EXE のコピーに失敗しました。
    echo         共有フォルダへの書き込み権限を確認してください。
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
