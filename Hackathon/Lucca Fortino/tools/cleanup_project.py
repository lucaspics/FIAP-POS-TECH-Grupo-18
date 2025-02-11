"""
Script para remover arquivos e pastas obsoletos do projeto VisionGuard.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict

def setup_logging():
    """Configura o sistema de logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('cleanup_log.txt')
        ]
    )

def get_items_to_remove() -> Dict[str, List[str]]:
    """
    Define os itens que devem ser removidos.
    
    Returns:
        Dict com listas de diretórios e arquivos a serem removidos
    """
    return {
        'directories': [
            'src/logs',
            'src/data',
            'src/models',
            'src/assets',
            'src/api'
        ],
        'files': [
            'src/run.py',
            'src/api/main.py',
            'src/api/config.py',
            'src/api/detector.py',
            'src/api/alert_manager.py'
        ]
    }

def remove_items(base_dir: Path, items: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Remove os itens especificados de forma segura.
    
    Args:
        base_dir: Diretório base do projeto
        items: Dicionário com listas de itens a remover
    
    Returns:
        Dict com listas de itens removidos com sucesso
    """
    removed_items = {
        'directories': [],
        'files': []
    }
    
    # Remover diretórios
    for dir_path in items['directories']:
        full_path = base_dir / dir_path
        if full_path.exists() and full_path.is_dir():
            try:
                shutil.rmtree(full_path)
                removed_items['directories'].append(dir_path)
                logging.info(f'Removido diretório: {dir_path}')
            except Exception as e:
                logging.error(f'Erro ao remover diretório {dir_path}: {str(e)}')
    
    # Remover arquivos
    for file_path in items['files']:
        full_path = base_dir / file_path
        if full_path.exists() and full_path.is_file():
            try:
                full_path.unlink()
                removed_items['files'].append(file_path)
                logging.info(f'Removido arquivo: {file_path}')
            except Exception as e:
                logging.error(f'Erro ao remover arquivo {file_path}: {str(e)}')
    
    return removed_items

def verify_removal(base_dir: Path, removed_items: Dict[str, List[str]]) -> bool:
    """
    Verifica se os itens foram removidos corretamente.
    
    Args:
        base_dir: Diretório base do projeto
        removed_items: Dicionário com listas de itens que deveriam ter sido removidos
    
    Returns:
        bool indicando se todos os itens foram removidos
    """
    all_removed = True
    
    # Verificar diretórios
    for dir_path in removed_items['directories']:
        full_path = base_dir / dir_path
        if full_path.exists():
            logging.error(f'Diretório ainda existe: {dir_path}')
            all_removed = False
    
    # Verificar arquivos
    for file_path in removed_items['files']:
        full_path = base_dir / file_path
        if full_path.exists():
            logging.error(f'Arquivo ainda existe: {file_path}')
            all_removed = False
    
    if all_removed:
        logging.info('Todos os itens foram removidos com sucesso!')
    else:
        logging.warning('Alguns itens não foram removidos corretamente')
    
    return all_removed

def main():
    """Função principal."""
    setup_logging()
    logging.info('Iniciando processo de limpeza...')
    
    try:
        # Obter diretório base do projeto
        base_dir = Path(__file__).resolve().parent.parent
        
        # Definir itens a serem removidos
        items_to_remove = get_items_to_remove()
        
        # Remover itens
        removed_items = remove_items(base_dir, items_to_remove)
        
        # Verificar remoção
        if verify_removal(base_dir, removed_items):
            logging.info('Processo de limpeza concluído com sucesso!')
            return 0
        else:
            logging.error('Falha no processo de limpeza')
            return 1
            
    except Exception as e:
        logging.error(f'Erro durante o processo de limpeza: {str(e)}')
        return 1

if __name__ == '__main__':
    exit(main())