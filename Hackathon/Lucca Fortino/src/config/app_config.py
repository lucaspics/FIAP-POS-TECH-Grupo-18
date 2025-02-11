"""
Configurações centralizadas do sistema VisionGuard
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Diretório base do projeto (2 níveis acima de config/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Diretórios do sistema
DIRS = {
    'logs': BASE_DIR / 'logs',
    'tools': BASE_DIR / 'tools',
    'docs': BASE_DIR / 'docs',
    'data': BASE_DIR / 'data',
    'models': BASE_DIR / 'models'
}

# Subdiretórios de logs
LOG_DIRS = {
    'base': DIRS['logs'],
    'alerts': DIRS['logs'] / 'alerts',
    'frames': DIRS['logs'] / 'frames',
    'metrics': DIRS['logs'] / 'metrics',
    'results': DIRS['logs'] / 'results',
    'errors': DIRS['logs'] / 'errors'
}

# Configurações do modelo
MODEL_CONFIG = {
    'path': DIRS['models'] / 'best.pt',
    'confidence_threshold': 0.25,
    'alert_threshold': 0.5,
    'target_height': 320
}

# Configurações de vídeo/câmera
VIDEO_CONFIG = {
    'frame_interval': 30,  # ms entre frames
    'analysis_interval': 5,  # frames entre análises
    'max_concurrent_workers': 2,
    'frame_timeout': 5.0,  # segundos - tempo maior para tolerar atrasos
    'width': 640,  # largura do vídeo
    'height': 480,  # altura do vídeo
    'overlay_path': BASE_DIR / 'art' / 'cam_overlay.psd'
}

# Configurações de alertas
ALERT_CONFIG = {
    'min_time_between_alerts': 1000,  # ms
    'save_frames': True,
    'save_detections': True,
    'notification_email': os.getenv('SMTP_EMAIL', 'fiap.iadev.2023.team18@gmail.com'),
    'enable_email_alerts': True,
    'alert_subject': 'VisionGuard - Alerta de Detecção',
    'alert_template': 'Objeto cortante detectado em {timestamp}'
}

# Configurações de interface
UI_CONFIG = {
    'window_title': 'VisionGuard System',
    'window_size': (1000, 600),
    'update_interval': 1000,  # ms
    'max_log_entries': 100
}

def validate_config() -> bool:
    """
    Valida as configurações do sistema.
    
    Returns:
        bool indicando se a configuração é válida
    """
    try:
        # Verificar diretórios
        for dir_name, dir_path in LOG_DIRS.items():
            os.makedirs(dir_path, exist_ok=True)
        
        # Verificar modelo
        model_path = Path(MODEL_CONFIG['path'])
        if not model_path.exists():
            raise ValueError(f"Modelo não encontrado: {model_path}")
        
        # Validar valores numéricos
        if MODEL_CONFIG['confidence_threshold'] < 0 or MODEL_CONFIG['confidence_threshold'] > 1:
            raise ValueError("confidence_threshold deve estar entre 0 e 1")
            
        if MODEL_CONFIG['alert_threshold'] < 0 or MODEL_CONFIG['alert_threshold'] > 1:
            raise ValueError("alert_threshold deve estar entre 0 e 1")
            
        if MODEL_CONFIG['target_height'] < 100:
            raise ValueError("target_height deve ser pelo menos 100 pixels")
            
        if VIDEO_CONFIG['frame_interval'] < 1:
            raise ValueError("frame_interval deve ser positivo")
            
        if VIDEO_CONFIG['analysis_interval'] < 1:
            raise ValueError("analysis_interval deve ser positivo")
            
        if VIDEO_CONFIG['max_concurrent_workers'] < 1:
            raise ValueError("max_concurrent_workers deve ser positivo")
            
        if ALERT_CONFIG['min_time_between_alerts'] < 0:
            raise ValueError("min_time_between_alerts deve ser não-negativo")
            
        # Validar email
        if '@' not in ALERT_CONFIG['notification_email']:
            raise ValueError("Email de notificação inválido")
            
        return True
        
    except Exception as e:
        import logging
        logging.error(f"Erro na validação de configurações: {str(e)}")
        return False

def get_config() -> Dict[str, Any]:
    """
    Retorna todas as configurações em um único dicionário.
    
    Returns:
        Dict com todas as configurações
    """
    return {
        'dirs': DIRS,
        'log_dirs': LOG_DIRS,
        'model': MODEL_CONFIG,
        'video': VIDEO_CONFIG,
        'alert': ALERT_CONFIG,
        'ui': UI_CONFIG
    }

# Validar configurações ao importar o módulo
if not validate_config():
    raise RuntimeError("Configurações inválidas")