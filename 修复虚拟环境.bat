@echo off
chcp 65001 >nul
title 修复虚拟环境 - HUST搜题系统
color 0C

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║           HUST搜题系统 - 虚拟环境修复工具                   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 本工具将删除损坏的虚拟环境并重新创建
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
echo ══════════════════════════════════════════════════════════════
echo.
echo ✅ 修复完成！
echo.
echo 下一步：双击运行 "首次安装.bat" 安装依赖
echo.
echo ══════════════════════════════════════════════════════════════
echo.
pause
