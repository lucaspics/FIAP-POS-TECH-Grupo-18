import cv2
import numpy as np
from PyQt5.QtGui import QImage, QPixmap
from config.app_config import VIDEO_CONFIG

def resize_frame(frame, target_height=None):
    """
    Redimensiona um frame mantendo a proporção.
    
    Args:
        frame: Frame original
        target_height: Altura desejada (opcional)
        
    Returns:
        Frame redimensionado
    """
    if frame is None:
        return None
        
    if target_height is None:
        target_height = VIDEO_CONFIG['height']
        
    height, width = frame.shape[:2]
    target_width = int(width * (target_height / height))
    return cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_AREA)

def bgr_to_rgb(frame):
    """
    Converte uma imagem de BGR para RGB.
    
    Args:
        frame: Frame em formato BGR
        
    Returns:
        Frame em formato RGB
    """
    if frame is None:
        return None
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

def frame_to_pixmap(frame):
    """
    Converte um frame OpenCV para QPixmap.
    
    Args:
        frame: Frame em formato BGR
        
    Returns:
        QPixmap do frame
    """
    if frame is None:
        return None
        
    # Redimensionar frame
    frame = resize_frame(frame, VIDEO_CONFIG['height'])
    
    # Converter para RGB
    rgb_frame = bgr_to_rgb(frame)
    
    # Criar QImage
    height, width, channel = rgb_frame.shape
    bytes_per_line = channel * width
    q_image = QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
    
    # Converter para QPixmap
    return QPixmap.fromImage(q_image)

def get_frame_dimensions(frame):
    """
    Retorna as dimensões de um frame.
    
    Args:
        frame: Frame para analisar
        
    Returns:
        Tupla (largura, altura)
    """
    if frame is None:
        return (0, 0)
    height, width = frame.shape[:2]
    return width, height