"""
Utilitários para processamento de vídeo e manipulação de frames.
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Union
from PyQt5.QtGui import QImage, QPixmap
from config.app_config import VIDEO_CONFIG
from config.logging_config import get_logger

logger = get_logger('video_utils')

def validate_frame(frame: np.ndarray) -> bool:
    """
    Valida se um frame é válido para processamento.
    
    Args:
        frame: Frame para validar
        
    Returns:
        bool indicando se o frame é válido
    """
    if frame is None:
        return False
        
    try:
        if not isinstance(frame, np.ndarray):
            return False
            
        if len(frame.shape) != 3:
            return False
            
        height, width, channels = frame.shape
        if height <= 0 or width <= 0 or channels != 3:
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Erro ao validar frame: {str(e)}")
        return False

def resize_frame(frame: np.ndarray, 
                target_height: Optional[int] = None,
                keep_aspect_ratio: bool = True) -> Optional[np.ndarray]:
    """
    Redimensiona um frame.
    
    Args:
        frame: Frame original
        target_height: Altura desejada (opcional)
        keep_aspect_ratio: Se deve manter a proporção original
        
    Returns:
        Frame redimensionado ou None se inválido
    """
    try:
        if not validate_frame(frame):
            logger.warning("Frame inválido para redimensionamento")
            return None
            
        if target_height is None:
            target_height = VIDEO_CONFIG['height']
            
        height, width = frame.shape[:2]
        
        if keep_aspect_ratio:
            # Manter proporção
            target_width = int(width * (target_height / height))
        else:
            # Usar largura do VIDEO_CONFIG
            target_width = VIDEO_CONFIG['width']
        
        return cv2.resize(frame, 
                         (target_width, target_height), 
                         interpolation=cv2.INTER_AREA)
        
    except Exception as e:
        logger.error(f"Erro ao redimensionar frame: {str(e)}")
        return None

def bgr_to_rgb(frame: np.ndarray) -> Optional[np.ndarray]:
    """
    Converte uma imagem de BGR para RGB.
    
    Args:
        frame: Frame em formato BGR
        
    Returns:
        Frame em formato RGB ou None se inválido
    """
    try:
        if not validate_frame(frame):
            logger.warning("Frame inválido para conversão BGR->RGB")
            return None
            
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
    except Exception as e:
        logger.error(f"Erro na conversão BGR->RGB: {str(e)}")
        return None

def rgb_to_bgr(frame: np.ndarray) -> Optional[np.ndarray]:
    """
    Converte uma imagem de RGB para BGR.
    
    Args:
        frame: Frame em formato RGB
        
    Returns:
        Frame em formato BGR ou None se inválido
    """
    try:
        if not validate_frame(frame):
            logger.warning("Frame inválido para conversão RGB->BGR")
            return None
            
        return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
    except Exception as e:
        logger.error(f"Erro na conversão RGB->BGR: {str(e)}")
        return None

def frame_to_pixmap(frame: np.ndarray, 
                   auto_resize: bool = True) -> Optional[QPixmap]:
    """
    Converte um frame OpenCV para QPixmap.
    
    Args:
        frame: Frame em formato BGR
        auto_resize: Se deve redimensionar automaticamente
        
    Returns:
        QPixmap do frame ou None se inválido
    """
    try:
        if not validate_frame(frame):
            logger.warning("Frame inválido para conversão para QPixmap")
            return None
            
        # Redimensionar frame se necessário
        if auto_resize:
            frame = resize_frame(frame, VIDEO_CONFIG['height'])
            if frame is None:
                return None
        
        # Converter para RGB
        rgb_frame = bgr_to_rgb(frame)
        if rgb_frame is None:
            return None
        
        # Criar QImage com cópia dos dados
        height, width, channel = rgb_frame.shape
        bytes_per_line = channel * width
        
        # Fazer uma cópia contígua dos dados
        rgb_data = rgb_frame.copy()
        q_image = QImage(rgb_data.data,
                        width,
                        height,
                        bytes_per_line,
                        QImage.Format_RGB888).copy()  # Fazer uma cópia do QImage
        
        # Converter para QPixmap
        pixmap = QPixmap.fromImage(q_image)
        return pixmap
        
    except Exception as e:
        logger.error(f"Erro ao converter frame para QPixmap: {str(e)}")
        return None

def get_frame_dimensions(frame: np.ndarray) -> Tuple[int, int]:
    """
    Retorna as dimensões de um frame.
    
    Args:
        frame: Frame para analisar
        
    Returns:
        Tupla (largura, altura)
    """
    try:
        if not validate_frame(frame):
            logger.warning("Frame inválido para obter dimensões")
            return (0, 0)
            
        height, width = frame.shape[:2]
        return width, height
        
    except Exception as e:
        logger.error(f"Erro ao obter dimensões do frame: {str(e)}")
        return (0, 0)

def calculate_frame_size(frame: np.ndarray) -> int:
    """
    Calcula o tamanho em bytes de um frame.
    
    Args:
        frame: Frame para analisar
        
    Returns:
        Tamanho em bytes
    """
    try:
        if not validate_frame(frame):
            return 0
            
        return frame.nbytes
        
    except Exception as e:
        logger.error(f"Erro ao calcular tamanho do frame: {str(e)}")
        return 0

def adjust_brightness_contrast(frame: np.ndarray,
                            brightness: float = 1.0,
                            contrast: float = 1.0) -> Optional[np.ndarray]:
    """
    Ajusta brilho e contraste de um frame.
    
    Args:
        frame: Frame para ajustar
        brightness: Fator de brilho (1.0 = original)
        contrast: Fator de contraste (1.0 = original)
        
    Returns:
        Frame ajustado ou None se inválido
    """
    try:
        if not validate_frame(frame):
            return None
            
        # Limitar valores
        brightness = max(0.0, min(brightness, 3.0))
        contrast = max(0.0, min(contrast, 3.0))
        
        # Aplicar ajustes
        adjusted = cv2.convertScaleAbs(
            frame,
            alpha=contrast,
            beta=int(brightness * 50)
        )
        
        return adjusted
        
    except Exception as e:
        logger.error(f"Erro ao ajustar brilho/contraste: {str(e)}")
        return None

def draw_text(frame: np.ndarray,
             text: str,
             position: Tuple[int, int],
             font_scale: float = 1.0,
             color: Tuple[int, int, int] = (255, 255, 255),
             thickness: int = 2) -> Optional[np.ndarray]:
    """
    Desenha texto em um frame.
    
    Args:
        frame: Frame para desenhar
        text: Texto a ser desenhado
        position: Posição (x, y) do texto
        font_scale: Escala da fonte
        color: Cor do texto (BGR)
        thickness: Espessura do texto
        
    Returns:
        Frame com texto ou None se inválido
    """
    try:
        if not validate_frame(frame):
            return None
            
        # Criar cópia do frame
        result = frame.copy()
        
        # Desenhar texto com borda preta
        cv2.putText(
            result,
            text,
            position,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (0, 0, 0),  # Borda preta
            thickness + 2
        )
        
        # Desenhar texto principal
        cv2.putText(
            result,
            text,
            position,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao desenhar texto: {str(e)}")
        return None