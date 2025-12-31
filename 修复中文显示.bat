@echo off
chcp 65001 >nul 2>&1
title 修复中文显示问题

echo.
echo ================================================================
echo  修复Windows终端中文显示问题
echo ================================================================
echo.
echo 正在应用修复...
echo.

REM 设置控制台代码页为UTF-8
echo [1/4] 设置UTF-8编码...
REG ADD "HKCU\Console" /v CodePage /t REG_DWORD /d 65001 /f >nul 2>&1

REM 设置控制台字体（支持中文的等宽字体）
echo [2/4] 设置终端字体为Consolas...
REG ADD "HKCU\Console" /v FaceName /t REG_SZ /d "Consolas" /f >nul 2>&1
REG ADD "HKCU\Console" /v FontFamily /t REG_DWORD /d 54 /f >nul 2>&1
REG ADD "HKCU\Console" /v FontSize /t REG_DWORD /d 1048576 /f >nul 2>&1
REG ADD "HKCU\Console" /v FontWeight /t REG_DWORD /d 400 /f >nul 2>&1

REM 设置窗口大小
echo [3/4] 调整窗口尺寸...
REG ADD "HKCU\Console" /v WindowSize /t REG_DWORD /d 1966200 /f >nul 2>&1
REG ADD "HKCU\Console" /v ScreenBufferSize /t REG_DWORD /d 589824120 /f >nul 2>&1

REM 启用快速编辑模式
echo [4/4] 启用快速编辑...
REG ADD "HKCU\Console" /v QuickEdit /t REG_DWORD /d 1 /f >nul 2>&1

echo.
echo ================================================================
echo.
echo ✓ 修复完成！
echo.
echo 建议操作：
echo 1. 关闭所有命令行窗口
echo 2. 重新打开即可看到改善
echo.
echo 如果仍有问题，可以：
echo - 右键窗口标题栏 → 属性 → 字体 → 选择"新宋体"或"Consolas"
echo - 安装 Windows Terminal（微软商店）以获得更好体验
echo.
echo ================================================================
echo.
pause
