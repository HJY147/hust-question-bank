@echo off
chcp 65001 >nul 2>&1
REG ADD "HKCU\Console" /v FaceName /t REG_SZ /d "Consolas" /f >nul 2>&1
title 上传题目助手 - HUST搜题系统
color 0B
mode con cols=90 lines=35

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║              HUST搜题系统 - 上传题目助手                     ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo 本工具帮助你快速上传题目到系统
echo.

:MENU
echo ══════════════════════════════════════════════════════════════
echo  请选择操作：
echo ══════════════════════════════════════════════════════════════
echo  1. 上传图片题目（手动）
echo  2. PDF转图片
echo  3. 批量重命名文件
echo  4. 查看题库统计
echo  5. 退出
echo ══════════════════════════════════════════════════════════════
echo.

set /p choice="请输入选项 (1-5): "

if "%choice%"=="1" goto UPLOAD_IMAGE
if "%choice%"=="2" goto PDF_CONVERT
if "%choice%"=="3" goto RENAME
if "%choice%"=="4" goto STATS
if "%choice%"=="5" exit /b 0

echo 无效选项，请重试
timeout /t 2 >nul
cls
goto MENU

:UPLOAD_IMAGE
cls
echo.
echo ══════════════════════════════════════════════════════════════
echo  上传图片题目
echo ══════════════════════════════════════════════════════════════
echo.
echo 步骤：
echo 1. 将题目图片复制到 photo\ 目录
echo 2. 创建对应的答案文件到 data\answers\ 目录
echo.
echo 文件命名规则：
echo   calc_001.jpg  → data\answers\calc_001.txt
echo   phys_002.png  → data\answers\phys_002.txt
echo.
echo 学科缩写：
echo   calc    - 高等数学
echo   phys    - 大学物理
echo   circuit - 电路分析
echo   linear  - 线性代数
echo   prob    - 概率论
echo.
echo 按任意键打开文件夹...
pause >nul
explorer photo
explorer data\answers
echo.
echo 完成后按任意键返回主菜单...
pause >nul
cls
goto MENU

:PDF_CONVERT
cls
echo.
echo ══════════════════════════════════════════════════════════════
echo  PDF转图片
echo ══════════════════════════════════════════════════════════════
echo.
echo 正在检查依赖...
.venv\Scripts\python.exe -c "import fitz" 2>nul
if errorlevel 1 (
    echo.
    echo ❌ 缺少依赖包！正在安装...
    .venv\Scripts\pip.exe install PyMuPDF Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
    echo ✓ 依赖安装完成
)
echo.
set /p pdf_path="请输入PDF文件路径（或拖拽文件到此处）: "
REM 去除引号
set pdf_path=%pdf_path:"=%
if not exist "%pdf_path%" (
    echo ❌ 文件不存在
    pause
    cls
    goto MENU
)
echo.
echo 正在转换...
.venv\Scripts\python.exe scripts\pdf转图片.py "%pdf_path%"
echo.
echo 按任意键返回主菜单...
pause >nul
cls
goto MENU

:RENAME
cls
echo.
echo ══════════════════════════════════════════════════════════════
echo  批量重命名文件
echo ══════════════════════════════════════════════════════════════
echo.
echo 示例：将文件批量重命名为 calc_001, calc_002...
echo.
set /p folder="请输入要重命名的文件夹路径: "
set folder=%folder:"=%
if not exist "%folder%" (
    echo ❌ 文件夹不存在
    pause
    cls
    goto MENU
)
echo.
set /p prefix="请输入文件名前缀（如 calc, phys）: "
set /p start_num="请输入起始序号（默认1）: "
if "%start_num%"=="" set start_num=1
echo.
echo 将要重命名 %folder% 中的文件为 %prefix%_001, %prefix%_002...
set /p confirm="确认吗？(y/n): "
if /i not "%confirm%"=="y" (
    cls
    goto MENU
)
echo.
echo 正在重命名...
powershell -Command "$i=%start_num%; Get-ChildItem '%folder%' -File | ForEach-Object { $ext=$_.Extension; $newName='%prefix%_{0:D3}{1}' -f $i,$ext; Rename-Item $_.FullName $newName; Write-Host \"✓ $($_.Name) → $newName\"; $i++ }"
echo.
echo ✓ 重命名完成！
pause
cls
goto MENU

:STATS
cls
echo.
echo ══════════════════════════════════════════════════════════════
echo  题库统计
echo ══════════════════════════════════════════════════════════════
echo.
echo 📊 题目图片数量:
powershell -Command "(Get-ChildItem photo -File -Exclude '*.md','*.txt').Count"
echo.
echo 📝 答案文件数量:
powershell -Command "(Get-ChildItem data\answers -File -Exclude '.gitkeep').Count"
echo.
echo 📂 文件列表:
echo.
echo --- 题目图片 ---
dir /b photo | findstr /v ".md .txt"
echo.
echo --- 答案文件 ---
dir /b data\answers | findstr /v ".gitkeep"
echo.
pause
cls
goto MENU
