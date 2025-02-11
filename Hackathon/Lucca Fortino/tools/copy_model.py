import os
from pathlib import Path
import shutil
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def copy_latest_model():
    """
    Copia o modelo mais recente da pasta de treinamento para models/best.pt
    """
    try:
        # Encontrar a pasta de treinamento mais recente
        models_dir = Path("models")
        if not models_dir.exists():
            logger.error("Pasta 'models' não encontrada!")
            return False

        train_folders = [f for f in models_dir.iterdir() if f.is_dir() and f.name.startswith("train_")]
        if not train_folders:
            logger.error("Nenhuma pasta de treinamento encontrada!")
            return False

        # Ordenar por data de modificação (mais recente primeiro)
        latest_train = max(train_folders, key=lambda x: x.stat().st_mtime)
        
        # Caminho para o melhor modelo
        best_model = latest_train / "weights" / "best.pt"
        if not best_model.exists():
            logger.error(f"Modelo não encontrado em {best_model}")
            return False

        # Copiar para models/best.pt
        target_path = models_dir / "best.pt"
        shutil.copy2(best_model, target_path)
        logger.info(f"Modelo copiado com sucesso para {target_path}")
        
        return True

    except Exception as e:
        logger.error(f"Erro ao copiar modelo: {str(e)}")
        return False

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════╗
║     VisionGuard - Copiar Modelo      ║
╚══════════════════════════════════════╝
    """)
    
    if copy_latest_model():
        print("\nModelo copiado com sucesso! O sistema está pronto para uso.")
        print("Execute: .\\run.bat")
    else:
        print("\nErro ao copiar modelo. Verifique os logs para mais detalhes.")