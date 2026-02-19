@echo off
REM ====================================================
REM 病院アンケートシステム - Windows EXE ビルドスクリプト
REM PyInstaller を使用してポータブル exe を生成します
REM ====================================================

echo [INFO] 依存パッケージをインストール中...
pip install -r requirements.txt
pip install pyinstaller

echo [INFO] EXE をビルド中...
pyinstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "HospitalSurvey" ^
    --add-data "data;data" ^
    --hidden-import matplotlib.backends.backend_tkagg ^
    --hidden-import tkinter ^
    --hidden-import tkinter.ttk ^
    main.py

echo [INFO] ビルド完了！
echo [INFO] dist\HospitalSurvey\ フォルダに生成されました。
echo [INFO] HospitalSurvey.exe を実行してください。
pause
