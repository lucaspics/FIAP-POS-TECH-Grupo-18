from pathlib import Path
import shutil
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_folders():
    """Cria a estrutura de pastas necessária para o dataset."""
    try:
        # Estrutura base
        folders = [
            "data/images/train",
            "data/images/val",
            "data/labels/train",
            "data/labels/val",
            "models",
            "logs"
        ]
        
        # Criar pastas
        for folder in folders:
            Path(folder).mkdir(parents=True, exist_ok=True)
            logger.info(f"Pasta criada: {folder}")
        
        logger.info("""
Estrutura de pastas criada com sucesso!

Próximos passos:
1. Baixe um dataset do Roboflow Universe:
   https://universe.roboflow.com/
   Procure por "knife detection" ou "weapon detection"

2. Organize os arquivos:
   - data/images/train/  (80% das imagens)
   - data/images/val/    (20% das imagens)
   - data/labels/train/  (anotações de treino)
   - data/labels/val/    (anotações de validação)

3. Execute o treinamento:
   .\train.bat

Cada pasta contém um arquivo README.md com instruções detalhadas.
Para dúvidas, consulte os arquivos README.md em cada pasta.
""")
        
    except Exception as e:
        logger.error(f"Erro ao criar pastas: {str(e)}")
        raise

if __name__ == "__main__":
    setup_folders()