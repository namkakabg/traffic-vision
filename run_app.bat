@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title TrafficVision - Dashboard va Kiem thu

set "REPO_ROOT=%~dp0"
cd /d "%REPO_ROOT%"

echo ==============================================================
echo                TRAFFICVISION - HE THONG KIEM THU
echo ==============================================================
echo.

:: 1. Kiem tra va thiet lap moi truong Python
set "PYTHON_EXE="

if exist "%REPO_ROOT%.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%REPO_ROOT%.venv\Scripts\python.exe"
    echo [*] Su dung moi truong Python ao: .venv
) else if exist "%REPO_ROOT%venv\Scripts\python.exe" (
    set "PYTHON_EXE=%REPO_ROOT%venv\Scripts\python.exe"
    echo [*] Su dung moi truong Python ao: venv
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        set "PYTHON_EXE=python"
        echo [*] Su dung Python he thong
    ) else (
        echo [!] Loi: Khong tim thay Python tren may tinh!
        echo     Vui long cai dat Python 3.11 hoac tao moi truong .venv
        echo.
        pause
        exit /b 1
    )
)

:: 2. Kiem tra baseline model da duoc khoi tao hay chua
if not exist "%REPO_ROOT%artifacts\production\model.onnx" (
    echo.
    echo [*] Phat hien baseline model chua duoc khoi tao!
    echo [*] Dang tu dong chay scripts\bootstrap_baseline.py...
    "%PYTHON_EXE%" scripts\bootstrap_baseline.py
    if %errorlevel% neq 0 (
        echo.
        echo [!] Khoi tao baseline model that bai. Vui long kiem tra ket noi internet hoac thu vien.
        pause
        exit /b 1
    )
    echo [+] Khoi tao baseline model thanh cong!
    echo.
)

:: 3. Xu ly tham so dong lenh neu co (app / test / smoke)
if /i "%~1"=="app" goto RUN_APP
if /i "%~1"=="test" goto RUN_TEST
if /i "%~1"=="smoke" goto RUN_SMOKE

:MENU
echo.
echo ==============================================================
echo                      LUA CHON HOAT DONG
echo ==============================================================
echo  [1] Khoi chay ung dung Web Dashboard (Streamlit)
echo  [2] Chay toan bo test kiem thu tu dong (Pytest)
echo  [3] Chay Smoke Test nhanh (Kiem thu model va pipeline)
echo  [4] Thoat
echo ==============================================================
set "CHOICE=1"
set /p "CHOICE=Nhap lua chon [1/2/3/4] (Mac dinh la 1): "

if "%CHOICE%"=="1" goto RUN_APP
if "%CHOICE%"=="2" goto RUN_TEST
if "%CHOICE%"=="3" goto RUN_SMOKE
if "%CHOICE%"=="4" goto EXIT

echo [!] Lua chon khong hop le, vui long thu lai.
goto MENU

:RUN_APP
echo.
echo [*] Dang khoi chay Streamlit Web Dashboard...
echo [*] Trinh duyet se tu dong mo tai http://localhost:8501
echo [*] Nhan Ctrl+C tai cua so nay de dung ung dung.
echo.
"%PYTHON_EXE%" -m streamlit run app.py
if errorlevel 1 (
    echo.
    echo [!] Dashboard da dung do loi. Cua so nay se giu nguyen de ban doc thong bao loi o tren.
    echo     Kiem tra moi truong Python va cai dat lai thu vien neu Streamlit chua co.
    echo.
    pause
    goto MENU
)
goto EXIT

:RUN_TEST
echo.
echo [*] Dang chay toan bo bo test (pytest)...
echo.
"%PYTHON_EXE%" -m pytest -v
echo.
pause
goto MENU

:RUN_SMOKE
echo.
echo [*] Dang chay Smoke Test voi pipeline noi bo...
echo.
"%PYTHON_EXE%" scripts\smoke_test.py
echo.
pause
goto MENU

:EXIT
echo.
echo [*] Tam biet!
exit /b 0
