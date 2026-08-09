@echo off
title Password Manager - Secure Portable Launcher
echo ==================================================
echo   Starting Password Manager...
echo ==================================================

:: Try python executable first
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python PasswordManager.py
    goto end
)

:: Try py launcher
py --version >nul 2>&1
if %errorlevel% equ 0 (
    py PasswordManager.py
    goto end
)

:: If python is not installed, fallback to standalone binary
if exist "dist\PasswordManagerApp\PasswordManager.exe" (
    start "" "dist\PasswordManagerApp\PasswordManager.exe"
    goto end
)

if exist "PasswordManagerSetup.exe" (
    start "" "PasswordManagerSetup.exe"
    goto end
)

echo [ERROR] Python environment or executable not found.
echo Please install Python 3.10+ or run dist\PasswordManagerApp\PasswordManager.exe.
pause

:end
