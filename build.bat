@echo off
title TianCan V1.0 Core Build Tool

where cl >nul 2>nul
if errorlevel 1 (
    echo [!] ERROR: MSVC compiler cl.exe not found.
    echo [!] Please run this script in "x64 Native Tools Command Prompt".
    pause
    exit /b
)

echo [*] Auto-detecting Python environment...
for /f "tokens=*" %%i in ('python -c "import sys, os; print(os.path.join(sys.base_prefix, 'include'))"') do set "PY_INC=%%i"
for /f "tokens=*" %%i in ('python -c "import sys, os; print(os.path.join(sys.base_prefix, 'libs'))"') do set "PY_LIB=%%i"

if "%PY_INC%"=="" (
    echo [!] ERROR: Python environment not found.
    pause
    exit /b
)

echo [+] Detected Include Path: "%PY_INC%"
echo [+] Detected Libs Path:    "%PY_LIB%"

if exist security.pyd del /f /q security.pyd
if exist security.obj del /f /q security.obj

echo [*] Forging security.pyd...
cl /LD security.c /I "%PY_INC%" /link /LIBPATH:"%PY_LIB%" /INCREMENTAL:NO /OUT:security.pyd >nul

if exist security.pyd (
    echo [OK] Build Successful! security.pyd generated.
) else (
    echo [FAIL] Compilation failed.
)
pause