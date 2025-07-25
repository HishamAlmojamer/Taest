@echo off
title نظام إدارة المخازن المتطور - المهندس هشام المجمر
color 0B

echo.
echo ================================================================
echo           نظام إدارة المخازن المتطور v3.0
echo ================================================================
echo.
echo تصميم وتطوير: المهندس هشام المجمر
echo رقم الهاتف: 773988932
echo جميع الحقوق محفوظة 2024
echo.
echo ================================================================
echo.

echo [1/5] فحص Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python غير مثبت أو غير موجود في PATH
    echo يرجى تثبيت Python 3.7 أو أحدث من: https://python.org
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo ✅ Python %%i متوفر
)

echo.
echo [2/5] فحص المتطلبات الأساسية...
python -c "import tkinter, sqlite3, hashlib" >nul 2>&1
if errorlevel 1 (
    echo ❌ بعض المكتبات الأساسية مفقودة
    echo يرجى التأكد من تثبيت Python بشكل صحيح
    echo.
    pause
    exit /b 1
) else (
    echo ✅ المكتبات الأساسية متوفرة
)

echo.
echo [3/5] فحص المكتبات الإضافية...
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  matplotlib غير مثبتة (للرسوم البيانية)
    echo يمكن تثبيتها بالأمر: pip install matplotlib
) else (
    echo ✅ matplotlib متوفرة
)

python -c "import openpyxl" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  openpyxl غير مثبتة (لملفات Excel)
    echo يمكن تثبيتها بالأمر: pip install openpyxl
) else (
    echo ✅ openpyxl متوفرة
)

echo.
echo [4/5] تحضير النظام...
if exist start_system.py (
    echo ✅ ملف التشغيل المحسن موجود
    set MAIN_FILE=start_system.py
) else if exist run_enhanced.py (
    echo ✅ ملف التشغيل البديل موجود
    set MAIN_FILE=run_enhanced.py
) else (
    echo ⚠️  استخدام ملف التشغيل الأساسي
    set MAIN_FILE=main.py
)

echo.
echo [5/5] بدء النظام...
echo ================================================================
echo.

python %MAIN_FILE%

echo.
echo ================================================================
echo           شكراً لاستخدام نظام إدارة المخازن المتطور
echo.
echo للدعم الفني: المهندس هشام المجمر - 773988932
echo ================================================================
pause