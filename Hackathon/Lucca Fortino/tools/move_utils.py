"""
Script para mover utilitários para o core.
"""

import os
import shutil
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def move_utils_to_core():
    """Move os arquivos de utils para core."""
    try:
        # Obter diretório base
        base_dir = Path(__file__).resolve().parent.parent
        utils_dir = base_dir / 'src' / 'utils'
        core_dir = base_dir / 'src' / 'core'
        
        if utils_dir.exists():
            # Mover cada arquivo
            for file in utils_dir.glob('*.py'):
                dest_file = core_dir / file.name
                if not dest_file.exists():  # Evitar sobrescrever
                    shutil.move(str(file), str(dest_file))
                    logger.info(f'Movido: {file.name} -> core/')
            
            # Remover pasta utils se vazia
            if not any(utils_dir.iterdir()):
                utils_dir.rmdir()
                logger.info('Pasta src/utils/ removida')
        
        logger.info('Movimentação de utilitários concluída')
        
    except Exception as e:
        logger.error(f'Erro ao mover utilitários: {str(e)}')
        raise

def main():
    """Função principal."""
    try:
        logger.info('Iniciando movimentação de utilitários...')
        move_utils_to_core()
        logger.info('Movimentação concluída com sucesso!')
        return 0
    except Exception as e:
        logger.error(f'Erro durante movimentação: {str(e)}')
        return 1

if __name__ == '__main__':
    exit(main())