import logging
import os

def setup_logging():
    """Configura o sistema de logging da aplicação."""
    # Garantir que os diretórios de log existam
    os.makedirs("logs", exist_ok=True)
    
    # Configuração básica do logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/frontend.log"),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

# Criar logger global
logger = setup_logging()