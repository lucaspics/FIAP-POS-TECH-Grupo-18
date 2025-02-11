"""
Script para remover diretórios vazios.
"""

import os
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def remove_empty_dirs():
    """Remove diretórios vazios do projeto."""
    try:
        # Obter diretório base
        base_dir = Path(__file__).resolve().parent.parent
        src_dir = base_dir / 'src'
        
        # Lista de diretórios para verificar
        dirs_to_check = [
            'utils',
            'processing'
        ]
        
        for dir_name in dirs_to_check:
            dir_path = src_dir / dir_name
            if dir_path.exists() and not any(dir_path.iterdir()):
                dir_path.rmdir()
                logger.info(f'Removido diretório vazio: src/{dir_name}/')
        
        logger.info('Remoção de diretórios vazios concluída')
        
    except Exception as e:
        logger.error(f'Erro ao remover diretórios vazios: {str(e)}')
        raise

def main():
    """Função principal."""
    try:
        logger.info('Iniciando remoção de diretórios vazios...')
        remove_empty_dirs()
        logger.info('Remoção concluída com sucesso!')
        return 0
    except Exception as e:
        logger.error(f'Erro durante remoção: {str(e)}')
        return 1

if __name__ == '__main__':
    exit(main())