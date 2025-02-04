@echo off
echo Verificando ambiente Python...

python --version >nul 2>&1
if errorlevel 1 (
    echo Python nao encontrado! Por favor, instale o Python e adicione ao PATH.
    pause
    exit /b 1
)

echo Verificando dependencias...
pip show ultralytics >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r ../requirements.txt
    if errorlevel 1 (
        echo Erro ao instalar dependencias!
        pause
        exit /b 1
    )
)

echo Iniciando treinamento do VisionGuard...
python train.py
pause