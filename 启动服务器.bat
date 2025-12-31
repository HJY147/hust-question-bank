@echo off
chcp 65001 >nul
title HUST搜题系统 - 服务器
color 0B

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              HUST搜题系统 - 启动服务器                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM 获取当前目录
cd /d "%~dp0"

REM 检查虚拟环境是否存在
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    echo ✓ 使用本地虚拟环境
) else (
    echo.
    echo ❌ 未找到虚拟环境！
    echo.
    echo 请先运行 "首次安装.bat" 安装环境
    echo.
    pause
    exit /b 1
)

REM 检查后端文件
if not exist "backend\app_simple.py" (
    echo ❌ 未找到后端文件 backend\app_simple.py
    pause
    exit /b 1
)

REM 启动服务器
echo.
echo 正在启动服务器...
echo.
echo ══════════════════════════════════════════════════════════════
echo  访问地址: http://localhost:5000
echo  按 Ctrl+C 停止服务器
echo ══════════════════════════════════════════════════════════════
echo.

REM 延迟2秒后打开浏览器
start /b cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

REM 启动Flask服务
cd backend
"%~dp0.venv\Scripts\python.exe" app_simple.py

echo.
echo 服务器已停止
pause
