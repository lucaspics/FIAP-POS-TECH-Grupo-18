@echo off
setlocal

rem Obter o diretório do script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo Verificando ambiente Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python nao encontrado! Por favor, instale o Python e adicione ao PATH.
    pause
    exit /b 1
)

echo Atualizando pip e setuptools...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo Erro ao atualizar pip e setuptools!
    pause
    exit /b 1
)

echo Removendo PyQt5 existente...
pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip
if errorlevel 1 (
    echo Aviso: Erro ao remover PyQt5 existente
)

echo Instalando dependencias basicas...
pip install --user numpy>=1.26.0 PyYAML>=6.0.1 tqdm>=4.66.1 python-dotenv>=1.0.0
if errorlevel 1 (
    echo Erro ao instalar dependencias basicas!
    pause
    exit /b 1
)

echo Instalando PyTorch...
pip install --user torch torchvision --index-url https://download.pytorch.org/whl/cu121
if errorlevel 1 (
    echo Erro ao instalar PyTorch! Tentando versao CPU...
    pip install --user torch torchvision --index-url https://download.pytorch.org/whl/cpu
    if errorlevel 1 (
        echo Erro ao instalar PyTorch!
        pause
        exit /b 1
    )
)

echo Instalando OpenCV...
pip install --user opencv-python>=4.6.0
if errorlevel 1 (
    echo Erro ao instalar OpenCV!
    pause
    exit /b 1
)

echo Instalando Ultralytics...
pip install --user ultralytics>=8.0.196
if errorlevel 1 (
    echo Erro ao instalar Ultralytics!
    pause
    exit /b 1
)

echo Instalando FastAPI e dependencias...
pip install --user "fastapi>=0.104.1" "uvicorn>=0.24.0" "python-multipart>=0.0.6" "pydantic>=2.5.2" "pydantic-settings>=2.1.0" "aiofiles>=23.2.1"
if errorlevel 1 (
    echo Erro ao instalar FastAPI!
    pause
    exit /b 1
)

echo Instalando PyQt5...
pip install --user --no-deps PyQt5-sip==12.13.0
pip install --user --no-deps PyQt5-Qt5==5.15.2
pip install --user --no-deps PyQt5==5.15.10
if errorlevel 1 (
    echo Erro ao instalar PyQt5!
    pause
    exit /b 1
)

echo Instalando dependencias auxiliares...
pip install --user "qasync>=0.24.0" "aiohttp>=3.9.1" "aiosmtplib>=2.0.2"
if errorlevel 1 (
    echo Erro ao instalar dependencias auxiliares!
    pause
    exit /b 1
)

echo Verificando instalacao...
python -c "from PyQt5 import QtCore; import cv2; import torch; import ultralytics; print('OpenCV version:', cv2.__version__); print('PyTorch version:', torch.__version__); print('Ultralytics version:', ultralytics.__version__); print('PyQt5 version:', QtCore.QT_VERSION_STR)"
if errorlevel 1 (
    echo AVISO: Algumas dependencias podem nao ter sido instaladas corretamente.
    pause
    exit /b 1
)

echo Instalacao concluida com sucesso!
pause