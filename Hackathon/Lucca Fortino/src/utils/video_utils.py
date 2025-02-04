import cv2
from datetime import datetime
import os
from PyQt5.QtGui import QImage, QPixmap
from config.app_config import VIDEO_WIDTH, VIDEO_HEIGHT
from config.logging_config import logger

def resize_frame(frame, width=VIDEO_WIDTH, height=VIDEO_HEIGHT):
    """Redimensiona o frame para o tamanho especificado."""
    return cv2.resize(frame, (width, height))

def bgr_to_rgb(frame):
    """Converte o frame de BGR para RGB."""
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

def frame_to_qimage(frame):
    """Converte um frame OpenCV para QImage."""
    height, width, channel = frame.shape
    step = channel * width
    return QImage(frame.data, width, height, step, QImage.Format_RGB888)

def frame_to_pixmap(frame):
    """Converte um frame OpenCV para QPixmap."""
    rgb_frame = bgr_to_rgb(frame)
    return QPixmap.fromImage(frame_to_qimage(rgb_frame))

def save_frame(frame, directory, prefix="frame"):
    """
    Salva um frame em um diretório específico.
    
    Args:
        frame: Frame OpenCV para salvar
        directory: Diretório onde salvar o frame
        prefix: Prefixo para o nome do arquivo
        
    Returns:
        str: Caminho do arquivo salvo
    """
    os.makedirs(directory, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    file_path = os.path.join(directory, f"{prefix}_{timestamp}.jpg")
    
    # Converter para BGR se necessário
    if len(frame.shape) == 3 and frame.shape[2] == 3:
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    else:
        frame_bgr = frame
        
    cv2.imwrite(file_path, frame_bgr)
    logger.info(f"Frame salvo em: {file_path}")
    return file_path

def get_video_info(cap):
    """
    Obtém informações básicas do vídeo.
    
    Args:
        cap: Objeto VideoCapture do OpenCV
        
    Returns:
        dict: Dicionário com informações do vídeo
    """
    return {
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "duration": int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS))
    }

def ms_to_timestamp(ms):
    """Converte milissegundos em timestamp legível."""
    seconds = ms // 1000
    minutes = seconds // 60
    hours = minutes // 60
    
    return f"{int(hours):02d}:{int(minutes%60):02d}:{int(seconds%60):02d}"