@echo off
chcp 65001 >nul
title Система учета КРС PRO

echo =====================================================
echo   ЗАПУСК СИСТЕМЫ УЧЕТА КРС PRO
echo =====================================================
echo.

REM Проверка наличия Python в PATH
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден в PATH!
    echo.
    echo Пожалуйста, установите официальный Python 3.12:
    echo https://www.python.org/downloads/release/python-3129/
    echo.
    echo ВАЖНО: При установке отметьте галочку "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo ✅ Python найден
python --version
echo.

REM Попытка запуска с переменной окружения для Qt
echo 🚀 Запуск программы...
set QT_QPA_PLATFORM_PLUGIN_PATH=%LOCALAPPDATA%\Programs\Python\Python312\Lib\site-packages\PyQt5\Qt5\plugins\platforms
python main.py

if errorlevel 1 (
    echo.
    echo ❌ Ошибка запуска программы!
    echo.
    echo Попробуйте выполнить установку:
    echo 1. Запустите файл "Установка_КРС.bat"
    echo 2. Или следуйте инструкции в файле "ИНСТРУКЦИЯ_ПО_ЗАПУСКУ.md"
    echo.
    pause
)
