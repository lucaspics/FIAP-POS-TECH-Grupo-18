"""
Configuração centralizada do sistema de logging.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Dict
from .app_config import LOG_DIRS

# Configurações de rotação de logs
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

# Formatos de log
DETAILED_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
SIMPLE_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

def create_rotating_handler(log_path: Path, level: int, formatter: logging.Formatter) -> RotatingFileHandler:
    """
    Cria um handler de log com rotação.
    
    Args:
        log_path: Caminho do arquivo de log
        level: Nível de logging
        formatter: Formatador para as mensagens
        
    Returns:
        RotatingFileHandler configurado
    """
    handler = RotatingFileHandler(
        str(log_path),
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler

def get_handlers() -> Dict[str, logging.Handler]:
    """
    Cria e configura os handlers de log.
    
    Returns:
        Dict com os handlers configurados
    """
    # Criar formatadores
    detailed_formatter = logging.Formatter(DETAILED_FORMAT)
    simple_formatter = logging.Formatter(SIMPLE_FORMAT)
    
    # Handler de console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Handlers de arquivo
    handlers = {
        'console': console_handler,
        'app': create_rotating_handler(
            Path(LOG_DIRS['base']) / 'app.log',
            logging.INFO,
            detailed_formatter
        ),
        'error': create_rotating_handler(
            Path(LOG_DIRS['errors']) / 'error.log',
            logging.ERROR,
            detailed_formatter
        ),
        'alert': create_rotating_handler(
            Path(LOG_DIRS['alerts']) / 'alerts.log',
            logging.INFO,
            detailed_formatter
        ),
        'metrics': create_rotating_handler(
            Path(LOG_DIRS['metrics']) / 'metrics.log',
            logging.INFO,
            simple_formatter
        )
    }
    
    return handlers

def setup_logging() -> logging.Logger:
    """
    Configura o sistema de logging da aplicação.
    
    Returns:
        Logger configurado
    """
    try:
        # Garantir que os diretórios existam
        for dir_path in LOG_DIRS.values():
            os.makedirs(dir_path, exist_ok=True)
        
        # Configurar logger raiz
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Remover handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Adicionar novos handlers
        handlers = get_handlers()
        for handler in handlers.values():
            root_logger.addHandler(handler)
        
        # Criar logger específico da aplicação
        logger = logging.getLogger('visionguard')
        logger.setLevel(logging.INFO)
        
        return logger
        
    except Exception as e:
        # Fallback para configuração básica em caso de erro
        logging.basicConfig(
            level=logging.INFO,
            format=SIMPLE_FORMAT,
            handlers=[logging.StreamHandler()]
        )
        logging.error(f"Erro ao configurar logging: {str(e)}")
        return logging.getLogger('visionguard')

def get_logger(name: str) -> logging.Logger:
    """
    Obtém um logger configurado para um módulo específico.
    
    Args:
        name: Nome do módulo/componente
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(f'visionguard.{name}')

# Criar logger global
logger = setup_logging()

# Exemplo de uso em outros módulos:
# from config.logging_config import get_logger
# logger = get_logger(__name__)