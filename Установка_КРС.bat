@echo off
chcp 65001 >nul
title Установка для КРС учета

color 0A
echo.
echo =====================================================
echo    🐄 УСТАНОВКА СИСТЕМЫ УЧЕТА КРС PRO
echo =====================================================
echo.

REM Шаг 1: Проверка текущего Python
echo [1/5] Проверка текущей версии Python...
python --version 2>nul
if errorlevel 1 (
    color 0C
    echo.
    echo ⚠️  ВНИМАНИЕ: Python не найден в PATH!
    echo.
)
echo.

REM Шаг 2: Удаление проблемных версий
echo [2/5] Удаление старых версий PyQt5...
pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip -y 2>nul
if errorlevel 1 (
    echo Пропущено (возможно, не установлены)
)
echo.

REM Шаг 3: Информация об официальном Python
color 0B
echo [3/5] ═══════════════════════════════════════════
echo        ВАЖНО: Требуется официальный Python 3.12!
echo ═══════════════════════════════════════════
echo.
echo Ваша версия Python (pythoncore 3.14) несовместима
echo с PyQt5 и PyInstaller.
echo.
echo Скачайте официальный Python 3.12:
echo 🔗 https://www.python.org/downloads/release/python-3129/
echo.
echo При установке ОБЯЗАТЕЛЬНО отметьте:
echo ☑️  Add Python to PATH
echo.
pause

REM Шаг 4: После установки официального Python
echo.
echo [4/5] Проверка установки Python...
python --version 2>nul
if errorlevel 1 (
    color 0C
    echo.
    echo ❌ Python всё ещё не найден!
    echo Пожалуйста, установите Python и перезапустите этот скрипт.
    echo.
    pause
    exit /b 1
)
color 0A
echo ✅ Python найден!
echo.

REM Шаг 5: Установка зависимостей
echo [5/5] Установка необходимых библиотек...
pip install PyQt5==5.15.9 pyinstaller --force-reinstall
if errorlevel 1 (
    color 0C
    echo.
    echo ❌ Ошибка установки библиотек!
    echo Проверьте подключение к интернету.
    pause
    exit /b 1
)

echo.
color 0A
echo =====================================================
echo   ✅ ГОТОВО! Система установлена успешно!
echo =====================================================
echo.
echo Теперь запустите файл "Запустить_КРС.bat"
echo.
echo Если программа не запускается, прочитайте:
echo "ИНСТРУКЦИЯ_ПО_ЗАПУСКУ.md"
echo.
pause
