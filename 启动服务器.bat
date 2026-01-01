@echo off
chcp 65001 >nul 2>&1
REG ADD "HKCU\Console" /v FaceName /t REG_SZ /d "Consolas" /f >nul 2>&1
title HUST搜题系统 v3.0 - 服务器
color 0B
mode con cols=80 lines=35

echo.
echo ==============================================================
echo          HUST Question Bank System v3.0
echo ==============================================================
echo.

REM 获取当前目录
cd /d "%~dp0"

REM 检查端口占用
echo [Check] Checking port 5000...
netstat -ano | findstr ":5000" >nul
if %errorlevel%==0 (
    echo [Warning] Port 5000 is in use
    echo [Action] Killing existing process...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 1 /nobreak >nul
)
echo [OK] Port 5000 is available

REM 检查虚拟环境是否存在
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    echo [OK] Virtual environment found
) else (
    echo.
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run "首次安装.bat" first
    echo.
    pause
    exit /b 1
)

REM 检查后端文件
if not exist "backend\app_simple.py" (
    echo [ERROR] Backend file not found: backend\app_simple.py
    pause
    exit /b 1
)
echo [OK] Backend files verified

REM 统计题库
set /a QUESTION_COUNT=0
set /a ANSWER_COUNT=0
if exist "data\question_images" (
    for %%f in (data\question_images\*.jpg data\question_images\*.png) do set /a QUESTION_COUNT+=1
)
if exist "data\answers" (
    for %%f in (data\answers\*.txt) do set /a ANSWER_COUNT+=1
)
echo [Info] Questions: %QUESTION_COUNT%, Answers: %ANSWER_COUNT%

REM 启动服务器
echo.
echo ==============================================================
echo  Starting Server...
echo ==============================================================
echo  Local:   http://localhost:5000
echo  Network: http://0.0.0.0:5000
echo ==============================================================
echo  Press Ctrl+C to stop
echo ==============================================================
echo.

REM 延迟2秒后打开浏览器
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

REM 启动Flask服务
cd backend
"%~dp0.venv\Scripts\python.exe" app_simple.py

echo.
echo 服务器已停止
pause
