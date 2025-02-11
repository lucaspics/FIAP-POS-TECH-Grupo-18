"""
Script para finalizar a limpeza do projeto.
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

def move_files():
    """Move arquivos para suas pastas corretas."""
    try:
        # Obter diretório base
        base_dir = Path(__file__).resolve().parent.parent
        
        # Mover arquivos de utils para tools
        utils_dir = base_dir / 'utils'
        tools_dir = base_dir / 'tools'
        
        if utils_dir.exists():
            for file in utils_dir.glob('*'):
                dest_file = tools_dir / file.name
                if not dest_file.exists():  # Evitar sobrescrever
                    shutil.move(str(file), str(dest_file))
                    logger.info(f'Movido: {file.name} -> tools/')
            
            # Remover pasta utils se vazia
            if not any(utils_dir.iterdir()):
                utils_dir.rmdir()
                logger.info('Pasta utils/ removida')
        
        # Mover arquivos de doc para docs/user
        doc_dir = base_dir / 'doc'
        docs_user_dir = base_dir / 'docs' / 'user'
        
        if doc_dir.exists():
            for file in doc_dir.glob('*'):
                dest_file = docs_user_dir / file.name
                if not dest_file.exists():  # Evitar sobrescrever
                    shutil.move(str(file), str(dest_file))
                    logger.info(f'Movido: {file.name} -> docs/user/')
            
            # Remover pasta doc se vazia
            if not any(doc_dir.iterdir()):
                doc_dir.rmdir()
                logger.info('Pasta doc/ removida')
        
        logger.info('Movimentação de arquivos concluída')
        
    except Exception as e:
        logger.error(f'Erro ao mover arquivos: {str(e)}')
        raise

def remove_empty_dirs():
    """Remove diretórios vazios."""
    try:
        base_dir = Path(__file__).resolve().parent.parent
        
        # Lista de diretórios para verificar
        dirs_to_check = [
            'src/api',
            'src/assets',
            'src/data',
            'src/logs',
            'src/models'
        ]
        
        for dir_path in dirs_to_check:
            full_path = base_dir / dir_path
            if full_path.exists() and not any(full_path.iterdir()):
                full_path.rmdir()
                logger.info(f'Removido diretório vazio: {dir_path}')
        
        logger.info('Remoção de diretórios vazios concluída')
        
    except Exception as e:
        logger.error(f'Erro ao remover diretórios vazios: {str(e)}')
        raise

def main():
    """Função principal."""
    try:
        logger.info('Iniciando limpeza final...')
        move_files()
        remove_empty_dirs()
        logger.info('Limpeza final concluída com sucesso!')
        return 0
    except Exception as e:
        logger.error(f'Erro durante limpeza final: {str(e)}')
        return 1

if __name__ == '__main__':
    exit(main())