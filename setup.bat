@echo off
chcp 65001 > nul
echo ========================================================
echo        Установка Интерактивного Тренажёра Python
echo ========================================================
echo.

cd /d "%~dp0"

echo Проверка наличия Python...
python --version
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не обнаружен в системе.
    pause
    exit /b 1
)

echo.
echo Установка зависимостей проекта из requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo ========================================================
echo Установка успешно завершена!
echo Запустить тренажёр можно с помощью start.bat или команды:
echo    python run.py
echo ========================================================
pause
