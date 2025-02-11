@echo off
setlocal EnableDelayedExpansion

rem Obter o diretório do script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

cls
echo +====================================+
echo ^|     VisionGuard - Instalacao       ^|
echo +====================================+
echo.

rem Verificar se Python está instalado
python --version > nul 2>&1
if errorlevel 1 (
    echo Erro: Python nao encontrado!
    echo Por favor, instale Python 3.8 ou superior.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

rem Verificar versão do Python
python -c "import sys; exit(0) if sys.version_info >= (3,8) else exit(1)"
if errorlevel 1 (
    echo Erro: Python 3.8 ou superior eh necessario!
    echo Versao atual:
    python --version
    pause
    exit /b 1
)

rem Verificar se pip está instalado
python -m pip --version > nul 2>&1
if errorlevel 1 (
    echo Erro: pip nao encontrado!
    echo Tentando instalar pip...
    python -m ensurepip --default-pip
    if errorlevel 1 (
        echo Falha ao instalar pip
        pause
        exit /b 1
    )
)

echo Atualizando pip...
python -m pip install --upgrade pip

rem Criar e ativar ambiente virtual
if not exist "venv" (
    echo Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo Erro ao criar ambiente virtual!
        pause
        exit /b 1
    )
)

echo Ativando ambiente virtual...
call venv\Scripts\activate
if errorlevel 1 (
    echo Erro ao ativar ambiente virtual!
    pause
    exit /b 1
)

echo Instalando dependencias...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Erro ao instalar dependencias!
    pause
    exit /b 1
)

rem Criar diretórios necessários
echo Criando diretorios...
if not exist "logs" mkdir logs
if not exist "logs\alerts" mkdir logs\alerts
if not exist "logs\frames" mkdir logs\frames
if not exist "logs\metrics" mkdir logs\metrics
if not exist "logs\results" mkdir logs\results
if not exist "models" mkdir models

rem Verificar modelo
if not exist "models\best.pt" (
    echo AVISO: Modelo nao encontrado em models\best.pt
    echo Por favor, coloque seu modelo treinado neste local.
)

echo.
echo +====================================+
echo ^|      Instalacao Concluida!         ^|
echo +====================================+
echo.
echo Execute run.bat para iniciar o sistema
echo.

pause