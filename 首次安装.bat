@echo off
REM 设置UTF-8编码
chcp 65001 >nul 2>&1
REM 设置控制台字体为Consolas或新宋体（支持中文）
REG ADD "HKCU\Console" /v FaceName /t REG_SZ /d "Consolas" /f >nul 2>&1
title HUST搜题系统 - 首次安装
color 0A
mode con cols=80 lines=30

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║           HUST搜题系统 - 首次安装向导                        ║
echo ║                                                              ║
echo ║  本脚本将自动完成以下操作：                                  ║
echo ║  1. 检查Python环境                                           ║
echo ║  2. 创建虚拟环境                                             ║
echo ║  3. 安装依赖包（使用清华镜像源）                             ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM 检查Python是否安装
echo [1/4] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ 错误：未检测到Python！
    echo.
    echo 请先安装Python 3.8或更高版本：
    echo 下载地址：https://www.python.org/downloads/
    echo.
    echo 安装时请务必勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
echo ✓ Python已安装

REM 显示Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo   版本: %PYVER%

REM 创建虚拟环境
echo.
echo [2/4] 创建虚拟环境...
if exist ".venv" (
    echo ⚠ 检测到已有虚拟环境，验证是否可用...
    REM 测试虚拟环境是否正常
    .venv\Scripts\python.exe --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ 虚拟环境已损坏，正在重新创建...
        rmdir /s /q .venv
        python -m venv .venv
        if errorlevel 1 (
            echo ❌ 创建虚拟环境失败！
            pause
            exit /b 1
        )
        echo ✓ 虚拟环境重建成功
    ) else (
        echo ✓ 虚拟环境正常，跳过创建
    )
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ 创建虚拟环境失败！
        pause
        exit /b 1
    )
    echo ✓ 虚拟环境创建成功
)

REM 升级pip
echo.
echo [3/4] 升级pip（使用清华镜像源）...
.venv\Scripts\python.exe -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
echo ✓ pip升级完成

REM 安装依赖
echo.
echo [4/4] 安装依赖包（使用清华镜像源）...
echo.
echo 正在安装: flask, flask-cors, waitress, Pillow, requests, python-dotenv
echo.

.venv\Scripts\pip.exe install flask==2.3.0 flask-cors==4.0.0 waitress==2.1.2 Pillow requests python-dotenv -i https://pypi.tuna.tsinghua.edu.cn/simple

if errorlevel 1 (
    echo.
    echo ❌ 依赖安装失败！
    echo.
    echo 可能的解决方案：
    echo 1. 检查网络连接
    echo 2. 尝试使用其他镜像源：
    echo    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
    echo.
    pause
    exit /b 1
)

echo.
echo ✓ 所有依赖安装完成！
echo.
echo ══════════════════════════════════════════════════════════════
echo.
echo ✅ 安装成功！
echo.
echo 下一步：双击运行 "启动服务器.bat" 启动系统
echo.
echo ══════════════════════════════════════════════════════════════
echo.
pause
