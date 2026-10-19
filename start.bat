@echo off
chcp 65001 > nul
echo ========================================================
echo        Запуск Интерактивного Тренажёра Python
echo ========================================================
echo.

cd /d "%~dp0"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден! Убедитесь, что Python установлен и добавлен в PATH.
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo [ОШИБКА] Файл requirements.txt не найден!
    pause
    exit /b 1
)

echo [1/2] Проверка зависимостей...
python -m pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo [ПРЕДУПРЕЖДЕНИЕ] Не удалось обновить зависимости, пробуем запуск...
)

echo [2/2] Запуск сервера и интерфейса...
python run.py

pause
