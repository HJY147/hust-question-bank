@echo off
chcp 65001 >nul 2>&1
REG ADD "HKCU\Console" /v FaceName /t REG_SZ /d "Consolas" /f >nul 2>&1
title 配置防火墙 - HUST搜题系统
color 0E
mode con cols=80 lines=30

echo.
echo ══════════════════════════════════════════════════════════════
echo  正在配置防火墙，允许局域网访问...
echo ══════════════════════════════════════════════════════════════
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% NEQ 0 (
    echo ❌ 需要管理员权限！
    echo.
    echo 请右键点击此文件，选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

REM 添加防火墙规则
echo 正在添加防火墙规则...
netsh advfirewall firewall add rule name="HUST搜题系统" dir=in action=allow protocol=TCP localport=5000

if %errorlevel% EQU 0 (
    echo.
    echo ✅ 防火墙配置成功！
    echo.
    echo ══════════════════════════════════════════════════════════════
    echo  局域网访问地址：http://10.19.120.229:5000
    echo ══════════════════════════════════════════════════════════════
    echo.
    echo 现在别人可以通过上述地址访问你的搜题系统了！
    echo.
) else (
    echo.
    echo ❌ 配置失败，请检查错误信息
    echo.
)

pause
