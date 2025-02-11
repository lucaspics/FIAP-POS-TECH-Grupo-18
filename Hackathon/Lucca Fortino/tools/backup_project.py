"""
Script para criar backup do projeto VisionGuard antes da limpeza.
"""

import os
import shutil
from datetime import datetime
import logging
from pathlib import Path

def setup_logging():
    """Configura o sistema de logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('backup_log.txt')
        ]
    )

def create_backup():
    """
    Cria um backup completo do projeto em uma pasta com timestamp.
    
    Returns:
        str: Caminho da pasta de backup criada
    """
    # Obter diretório base do projeto (2 níveis acima deste script)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Criar nome da pasta de backup com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = base_dir / f'backup_{timestamp}'
    
    try:
        # Criar diretório de backup
        backup_dir.mkdir(exist_ok=True)
        logging.info(f'Criado diretório de backup: {backup_dir}')
        
        # Lista de diretórios e arquivos a serem copiados
        items_to_backup = [
            'src',
            'data',
            'models',
            'logs',
            'docs',
            'utils',
            'tools',
            '.env',
            '.gitignore',
            'requirements.txt',
            'README.md'
        ]
        
        # Copiar cada item
        for item in items_to_backup:
            src_path = base_dir / item
            if src_path.exists():
                dst_path = backup_dir / item
                
                if src_path.is_dir():
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    logging.info(f'Copiado diretório: {item}')
                else:
                    shutil.copy2(src_path, dst_path)
                    logging.info(f'Copiado arquivo: {item}')
            else:
                logging.warning(f'Item não encontrado: {item}')
        
        # Criar arquivo de metadados do backup
        metadata = {
            'timestamp': timestamp,
            'items_backed_up': items_to_backup,
            'backup_path': str(backup_dir)
        }
        
        with open(backup_dir / 'backup_metadata.txt', 'w') as f:
            for key, value in metadata.items():
                f.write(f'{key}: {value}\n')
        
        logging.info('Backup concluído com sucesso!')
        return str(backup_dir)
        
    except Exception as e:
        logging.error(f'Erro durante o backup: {str(e)}')
        raise

def verify_backup(backup_dir):
    """
    Verifica se o backup foi criado corretamente.
    
    Args:
        backup_dir (str): Caminho do diretório de backup
    
    Returns:
        bool: True se o backup estiver íntegro
    """
    backup_path = Path(backup_dir)
    
    try:
        # Verificar se o diretório existe
        if not backup_path.exists():
            logging.error('Diretório de backup não encontrado')
            return False
            
        # Verificar metadata
        if not (backup_path / 'backup_metadata.txt').exists():
            logging.error('Arquivo de metadata não encontrado')
            return False
            
        # Verificar diretórios principais
        essential_dirs = ['src', 'data', 'models']
        for dir_name in essential_dirs:
            if not (backup_path / dir_name).exists():
                logging.error(f'Diretório essencial não encontrado: {dir_name}')
                return False
        
        logging.info('Verificação do backup concluída com sucesso!')
        return True
        
    except Exception as e:
        logging.error(f'Erro durante verificação do backup: {str(e)}')
        return False

def main():
    """Função principal."""
    setup_logging()
    logging.info('Iniciando processo de backup...')
    
    try:
        backup_dir = create_backup()
        if verify_backup(backup_dir):
            logging.info(f'Backup criado e verificado com sucesso em: {backup_dir}')
            return 0
        else:
            logging.error('Falha na verificação do backup')
            return 1
    except Exception as e:
        logging.error(f'Falha no processo de backup: {str(e)}')
        return 1

if __name__ == '__main__':
    exit(main())