"""
Script para reorganizar a estrutura de diretórios do projeto VisionGuard.
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Tuple

def setup_logging():
    """Configura o sistema de logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('reorganize_log.txt')
        ]
    )

def get_directory_structure() -> Dict[str, List[str]]:
    """
    Define a nova estrutura de diretórios.
    
    Returns:
        Dict com a estrutura de diretórios a ser criada
    """
    return {
        'docs': [
            'technical',
            'user'
        ],
        'tests': [],
        'tools': [],
        'logs': [
            'alerts',
            'errors',
            'frames',
            'metrics',
            'results'
        ]
    }

def get_file_moves() -> List[Tuple[str, str]]:
    """
    Define os arquivos que devem ser movidos.
    
    Returns:
        Lista de tuplas (origem, destino) dos arquivos
    """
    return [
        # Documentação
        ('how_works.md', 'docs/technical/how_works.md'),
        ('docs/refactor_plan.md', 'docs/technical/refactor_plan.md'),
        ('docs/async_migration_plan.md', 'docs/technical/async_migration_plan.md'),
        ('docs/cleanup_plan.md', 'docs/technical/cleanup_plan.md'),
        ('docs/implementation_steps.md', 'docs/technical/implementation_steps.md'),
        ('doc/visionguard.docx', 'docs/user/visionguard.docx'),
        ('doc/Hack 1 IADT.docx.pdf', 'docs/user/Hack_1_IADT.pdf'),
        
        # Scripts de utilidade
        ('utils/copy_model.bat', 'tools/copy_model.bat'),
        ('utils/copy_model.py', 'tools/copy_model.py'),
        ('utils/setup_folders.py', 'tools/setup_folders.py'),
        ('utils/setup.bat', 'tools/setup.bat'),
        ('utils/train.bat', 'tools/train.bat'),
        ('utils/train.py', 'tools/train.py')
    ]

def create_directory_structure(base_dir: Path, structure: Dict[str, List[str]]) -> bool:
    """
    Cria a nova estrutura de diretórios.
    
    Args:
        base_dir: Diretório base do projeto
        structure: Dicionário com a estrutura de diretórios
    
    Returns:
        bool indicando sucesso da operação
    """
    try:
        for dir_name, subdirs in structure.items():
            # Criar diretório principal
            dir_path = base_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            logging.info(f'Criado/verificado diretório: {dir_name}')
            
            # Criar subdiretórios
            for subdir in subdirs:
                subdir_path = dir_path / subdir
                subdir_path.mkdir(exist_ok=True)
                logging.info(f'Criado/verificado subdiretório: {dir_name}/{subdir}')
        
        return True
        
    except Exception as e:
        logging.error(f'Erro ao criar estrutura de diretórios: {str(e)}')
        return False

def move_files(base_dir: Path, moves: List[Tuple[str, str]]) -> bool:
    """
    Move os arquivos para suas novas localizações.
    
    Args:
        base_dir: Diretório base do projeto
        moves: Lista de tuplas (origem, destino) dos arquivos
    
    Returns:
        bool indicando sucesso da operação
    """
    try:
        for src, dst in moves:
            src_path = base_dir / src
            dst_path = base_dir / dst
            
            if src_path.exists():
                # Criar diretório de destino se não existir
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Mover arquivo
                shutil.move(str(src_path), str(dst_path))
                logging.info(f'Movido: {src} -> {dst}')
            else:
                logging.warning(f'Arquivo de origem não encontrado: {src}')
        
        return True
        
    except Exception as e:
        logging.error(f'Erro ao mover arquivos: {str(e)}')
        return False

def verify_structure(base_dir: Path, structure: Dict[str, List[str]], moves: List[Tuple[str, str]]) -> bool:
    """
    Verifica se a reorganização foi bem-sucedida.
    
    Args:
        base_dir: Diretório base do projeto
        structure: Dicionário com a estrutura de diretórios
        moves: Lista de tuplas (origem, destino) dos arquivos
    
    Returns:
        bool indicando se tudo está correto
    """
    all_correct = True
    
    # Verificar diretórios
    for dir_name, subdirs in structure.items():
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            logging.error(f'Diretório não encontrado: {dir_name}')
            all_correct = False
        
        for subdir in subdirs:
            subdir_path = dir_path / subdir
            if not subdir_path.exists():
                logging.error(f'Subdiretório não encontrado: {dir_name}/{subdir}')
                all_correct = False
    
    # Verificar arquivos movidos
    for _, dst in moves:
        dst_path = base_dir / dst
        if not dst_path.exists():
            logging.error(f'Arquivo não encontrado no destino: {dst}')
            all_correct = False
    
    if all_correct:
        logging.info('Verificação da estrutura concluída com sucesso!')
    else:
        logging.warning('Alguns itens não estão na estrutura esperada')
    
    return all_correct

def main():
    """Função principal."""
    setup_logging()
    logging.info('Iniciando reorganização do projeto...')
    
    try:
        # Obter diretório base do projeto
        base_dir = Path(__file__).resolve().parent.parent
        
        # Criar nova estrutura de diretórios
        structure = get_directory_structure()
        if not create_directory_structure(base_dir, structure):
            return 1
        
        # Mover arquivos
        moves = get_file_moves()
        if not move_files(base_dir, moves):
            return 1
        
        # Verificar resultado
        if verify_structure(base_dir, structure, moves):
            logging.info('Reorganização concluída com sucesso!')
            return 0
        else:
            logging.error('Falha na reorganização')
            return 1
            
    except Exception as e:
        logging.error(f'Erro durante a reorganização: {str(e)}')
        return 1

if __name__ == '__main__':
    exit(main())