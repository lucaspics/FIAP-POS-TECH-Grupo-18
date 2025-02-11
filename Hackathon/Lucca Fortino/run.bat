@echo off
setlocal EnableDelayedExpansion

rem Obter o diretório do script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

cls
echo +====================================+
echo ^|          VisionGuard System        ^|
echo +====================================+
echo.
echo Deseja instalar/atualizar as dependencias?
echo.
echo Pressione:
echo [S] - Para instalar/atualizar dependencias
echo [N] - Para pular instalacao e iniciar o sistema
echo.
echo.

set /p opcao="Digite S ou N: "

if /i "%opcao%"=="S" (
    cls
    echo +====================================+
    echo ^|          VisionGuard System        ^|
    echo +====================================+
    echo.
    echo Iniciando instalacao de dependencias...
    echo.
    call install.bat
    if errorlevel 1 (
        echo.
        echo Erro ao instalar dependencias!
        pause
        exit /b 1
    )
) else (
    cls
    echo +====================================+
    echo ^|          VisionGuard System        ^|
    echo +====================================+
    echo.
    echo Instalacao ignorada.
    echo.
    goto :START_SYSTEM
)

:START_SYSTEM
echo Iniciando VisionGuard System...
echo.
python "%SCRIPT_DIR%src/main.py"
pause