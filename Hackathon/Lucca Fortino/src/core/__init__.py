"""
Core do sistema VisionGuard - Módulo otimizado para processamento local
"""

import cv2
import numpy as np
from typing import Tuple, Optional
from pathlib import Path

from .detector import (
    ObjectDetector,
    Detection,
    DetectionResult
)

from .alert_manager import AlertManager
from .email_sender import EmailSender

# Constantes de processamento de imagem
DEFAULT_TARGET_HEIGHT = 320
DEFAULT_CONFIDENCE_THRESHOLD = 0.25
DEFAULT_ALERT_THRESHOLD = 0.5

def resize_frame(frame: np.ndarray, target_height: int = DEFAULT_TARGET_HEIGHT) -> np.ndarray:
    """
    Redimensiona um frame mantendo a proporção.
    
    Args:
        frame: Frame original
        target_height: Altura desejada
        
    Returns:
        Frame redimensionado
    """
    height, width = frame.shape[:2]
    target_width = int(width * (target_height / height))
    return cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)

def bgr_to_rgb(frame: np.ndarray) -> np.ndarray:
    """
    Converte uma imagem de BGR para RGB.
    
    Args:
        frame: Frame em formato BGR
        
    Returns:
        Frame em formato RGB
    """
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

def rgb_to_bgr(frame: np.ndarray) -> np.ndarray:
    """
    Converte uma imagem de RGB para BGR.
    
    Args:
        frame: Frame em formato RGB
        
    Returns:
        Frame em formato BGR
    """
    return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

def encode_frame_jpg(frame: np.ndarray, quality: int = 95) -> bytes:
    """
    Codifica um frame em JPEG.
    
    Args:
        frame: Frame para codificar
        quality: Qualidade da compressão (1-100)
        
    Returns:
        Bytes do JPEG
    """
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, buffer = cv2.imencode('.jpg', frame, encode_param)
    return buffer.tobytes()

def decode_frame_jpg(buffer: bytes) -> Optional[np.ndarray]:
    """
    Decodifica um buffer JPEG em frame.
    
    Args:
        buffer: Bytes do JPEG
        
    Returns:
        Frame decodificado ou None se falhar
    """
    try:
        nparr = np.frombuffer(buffer, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        return None

def get_frame_dimensions(frame: np.ndarray) -> Tuple[int, int]:
    """
    Retorna as dimensões de um frame.
    
    Args:
        frame: Frame para analisar
        
    Returns:
        Tupla (largura, altura)
    """
    height, width = frame.shape[:2]
    return width, height

__all__ = [
    'ObjectDetector',
    'Detection',
    'DetectionResult',
    'AlertManager',
    'EmailSender',
    'resize_frame',
    'bgr_to_rgb',
    'rgb_to_bgr',
    'encode_frame_jpg',
    'decode_frame_jpg',
    'get_frame_dimensions',
    'DEFAULT_TARGET_HEIGHT',
    'DEFAULT_CONFIDENCE_THRESHOLD',
    'DEFAULT_ALERT_THRESHOLD'
]