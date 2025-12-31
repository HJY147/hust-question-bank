@echo off
chcp 65001 >nul 2>&1
REG ADD "HKCU\Console" /v FaceName /t REG_SZ /d "Consolas" /f >nul 2>&1
title 上传题目助手 - HUST搜题系统
color 0B
mode con cols=90 lines=35

echo.
echo ==============================================================
echo           Upload Question Helper
echo ==============================================================
echo.
echo This tool helps you upload questions quickly
echo.

:MENU
echo ==============================================================
echo  Select Option:
echo ==============================================================
echo  1. Upload Images (Manual)
echo  2. Convert PDF to Images
echo  3. Batch Rename Files
echo  4. View Statistics
echo  5. Exit
echo ==============================================================
echo.

set /p choice="请输入选项 (1-5): "

if "%choice%"=="1" goto UPLOAD_IMAGE
if "%choice%"=="2" goto PDF_CONVERT
if "%choice%"=="3" goto RENAME
if "%choice%"=="4" goto STATS
if "%choice%"=="5" exit /b 0

echo Invalid option, please try again
timeout /t 2 >nul
cls
goto MENU

:UPLOAD_IMAGE
cls
echo.
echo ==============================================================
echo  Upload Image Questions
echo ==============================================================
echo.
echo Steps:
echo 1. Copy question images to photo\ folder
echo 2. Create answer files in data\answers\ folder
echo.
echo File naming rules:
echo   calc_001.jpg  -> data\answers\calc_001.txt
echo   phys_002.png  -> data\answers\phys_002.txt
echo.
echo Subject codes:
echo   calc    - Calculus
echo   phys    - Physics
echo   circuit - Circuit
echo   linear  - Linear Algebra
echo   prob    - Probability
echo.
echo Press any key to open folders...
pause >nul
explorer photo
explorer data\answers
echo.
echo Press any key to return to menu...
pause >nul
cls
goto MENU

:PDF_CONVERT
cls
echo.
echo ==============================================================
echo  Convert PDF to Images
echo ==============================================================
echo.
echo Checking dependencies...
.venv\Scripts\python.exe -c "import fitz" 2>nul
if errorlevel 1 (
    echo.
    echo [X] Missing dependencies! Installing...
    .venv\Scripts\pip.exe install PyMuPDF Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet
    echo [OK] Dependencies installed
)
echo.
set /p pdf_path="Enter PDF file path (or drag file here): "
REM Remove quotes
set pdf_path=%pdf_path:"=%
if not exist "%pdf_path%" (
    echo [X] File not found
    pause
    cls
    goto MENU
)
echo.
echo Converting...
.venv\Scripts\python.exe scripts\pdf转图片.py "%pdf_path%"
echo.
echo Press any key to return to menu...
pause >nul
cls
goto MENU

:RENAME
cls
echo.
echo ==============================================================
echo  Batch Rename Files
echo ==============================================================
echo.
echo Example: Rename files to calc_001, calc_002...
echo.
set /p folder="Enter folder path: "
set folder=%folder:"=%
if not exist "%folder%" (
    echo [X] Folder not found
    pause
    cls
    goto MENU
)
echo.
set /p prefix="Enter file prefix (e.g. calc, phys): "
set /p start_num="Enter start number (default 1): "
if "%start_num%"=="" set start_num=1
echo.
echo Will rename files in %folder% to %prefix%_001, %prefix%_002...
set /p confirm="Confirm? (y/n): "
if /i not "%confirm%"=="y" (
    cls
    goto MENU
)
echo.
echo Renaming...
powershell -Command "$i=%start_num%; Get-ChildItem '%folder%' -File | ForEach-Object { $ext=$_.Extension; $newName='%prefix%_{0:D3}{1}' -f $i,$ext; Rename-Item $_.FullName $newName; Write-Host \"[OK] $($_.Name) -> $newName\"; $i++ }"
echo.
echo [OK] Rename complete!
pause
cls
goto MENU

:STATS
cls
echo.
echo ==============================================================
echo  Question Bank Statistics
echo ==============================================================
echo.
echo [Stats] Question images:
powershell -Command "(Get-ChildItem photo -File -Exclude '*.md','*.txt').Count"
echo.
echo [Stats] Answer files:
powershell -Command "(Get-ChildItem data\answers -File -Exclude '.gitkeep').Count"
echo.
echo [List] Files:
echo.
echo --- Question Images ---
dir /b photo | findstr /v ".md .txt"
echo.
echo --- Answer Files ---
dir /b data\answers | findstr /v ".gitkeep"
echo.
pause
cls
goto MENU
