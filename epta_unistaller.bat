@echo off
setlocal

set "LAUNCHER_DIR=%cd%"
set "APPDATA_DIR=%APPDATA%\EPTAData"

echo Вы уверены, что хотите удалить лаунчер и данные? (y/n)
set /p confirm=Выберите y или n: 
if /i "%confirm%" neq "y" (
    echo Отмена.
    pause
    exit /b
)

echo Удаление папки лаунчера: %LAUNCHER_DIR%
rmdir /s /q "%LAUNCHER_DIR%"

echo Удаление папки данных: %APPDATA_DIR%
rmdir /s /q "%APPDATA_DIR%"

echo Удаление завершено.
pause
