@echo off
chcp 65001 >nul 2>&1
REG ADD "HKCU\Console" /v FaceName /t REG_SZ /d "Consolas" /f >nul 2>&1
title 修复虚拟环境 - HUST搜题系统
color 0C
mode con cols=80 lines=30

echo.
echo ==============================================================
echo           Fix Virtual Environment
echo ==============================================================
echo.
echo This tool will remove damaged venv and recreate it
echo.

REM 检查Python
echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python！请先安装Python
    pause
    exit /b 1
)
echo ✓ Python已安装

REM 删除旧环境
echo.
echo [2/3] 删除旧的虚拟环境...
if exist ".venv" (
    echo 正在删除 .venv 文件夹...
    rmdir /s /q .venv
    if exist ".venv" (
        echo ❌ 无法删除，请手动删除 .venv 文件夹后重试
        pause
        exit /b 1
    )
    echo ✓ 旧环境已删除
) else (
    echo ✓ 无需删除
)

REM 创建新环境
echo.
echo [3/3] 创建新的虚拟环境...
python -m venv .venv
if errorlevel 1 (
    echo ❌ 创建失败！
    pause
    exit /b 1
)
echo ✓ 虚拟环境创建成功

echo.
echo ==============================================================
echo.
echo [SUCCESS] Fix Complete!
echo.
echo Next: Run "First Install.bat" to install dependencies
echo.
echo ==============================================================
echo.
pause
