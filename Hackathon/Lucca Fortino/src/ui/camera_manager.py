"""
Gerenciador de recursos da câmera.
"""

import cv2
import time
import platform
from typing import Tuple, Optional, Any
from config.logging_config import get_logger
from config.app_config import VIDEO_CONFIG
from .source_dialog import CameraBackend

logger = get_logger('camera_manager')

class CameraManager:
    """Gerenciador de recursos da câmera."""
    
    def __init__(self):
        """Inicializa o gerenciador de câmera."""
        self.cap: Optional[cv2.VideoCapture] = None
        self.camera_id: Optional[int] = None
        self.last_frame_time: Optional[float] = None
        self.reconnect_attempts: int = 0
        self.max_reconnect_attempts: int = 3
        self.frame_timeout: float = VIDEO_CONFIG['frame_timeout']
        self.is_camera: bool = False
        self.video_path: Optional[str] = None
        
    def is_connection_stale(self) -> bool:
        """
        Verifica se a conexão está estagnada.
        
        Returns:
            bool indicando se a conexão está estagnada
        """
        if self.last_frame_time is None:
            return False
            
        elapsed = time.time() - self.last_frame_time
        is_stale = elapsed > self.frame_timeout
        
        if is_stale:
            logger.warning(f"Conexão estagnada - {elapsed:.1f}s sem frames (timeout: {self.frame_timeout}s)")
        
        return is_stale
    
    def try_reconnect(self) -> bool:
        """
        Tenta reconectar à câmera.
        
        Returns:
            bool indicando sucesso da reconexão
        """
        if self.camera_id is None:
            logger.error("Tentativa de reconexão sem ID de câmera válido")
            return False
            
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.warning("Número máximo de tentativas de reconexão atingido")
            return False
            
        logger.info(f"Tentativa de reconexão {self.reconnect_attempts + 1}/{self.max_reconnect_attempts}")
        
        # Libera a câmera atual mas mantém o camera_id
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Tenta cada backend disponível
        backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, None] if platform.system() == 'Windows' else [None]
        
        for backend in backends:
            cap, error = CameraBackend.try_backend(self.camera_id, backend)
            if cap:
                self.cap = cap
                self.last_frame_time = time.time()
                logger.info(f"Reconexão bem sucedida usando backend {backend if backend else 'padrão'}")
                return True
        
        self.reconnect_attempts += 1
        return False
    
    def read_frame(self) -> Tuple[bool, Optional[Any]]:
        """
        Lê um frame da câmera com verificações de estado.
        
        Returns:
            Tupla (sucesso, frame)
        """
        if not self.cap or not self.cap.isOpened():
            logger.warning("Tentativa de leitura com câmera fechada")
            return False, None
            
        try:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.last_frame_time = time.time()
                if self.reconnect_attempts > 0:
                    logger.info("Leitura normalizada após falhas")
                self.reconnect_attempts = 0  # Reset contador de tentativas após sucesso
                return True, frame
                
            # Falha na leitura
            logger.warning(f"Falha ao ler frame: ret={ret}, frame={'vazio' if frame is None else 'ok'}")
            
            # Verifica se é uma falha temporária ou permanente
            if self.is_connection_stale():
                if not self.try_reconnect():
                    return False, None
                # Tenta ler novamente após reconexão
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.last_frame_time = time.time()
                    logger.info("Frame recuperado após reconexão")
                    return True, frame
            
            return False, None
            
        except Exception as e:
            logger.error(f"Erro ao ler frame: {str(e)}")
            return False, None
    
    def get_video_info(self) -> dict:
        """
        Obtém informações do vídeo atual.
        
        Returns:
            Dict com informações do vídeo
        """
        info = {
            'is_camera': self.is_camera,
            'is_open': bool(self.cap and self.cap.isOpened()),
            'fps': 0,
            'frame_count': 0,
            'duration': 0,
            'current_pos': 0,
            'width': 0,
            'height': 0
        }
        
        if self.cap and self.cap.isOpened():
            info.update({
                'fps': self.cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'current_pos': self.cap.get(cv2.CAP_PROP_POS_FRAMES),
                'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            })
            
            if not self.is_camera:
                info['duration'] = info['frame_count'] / info['fps']
        
        return info
    
    def set_video_pos(self, pos_ms: int) -> bool:
        """
        Define a posição do vídeo em milissegundos.
        
        Args:
            pos_ms: Posição em milissegundos
            
        Returns:
            bool indicando sucesso da operação
        """
        if not self.cap or not self.cap.isOpened() or self.is_camera:
            return False
            
        try:
            self.cap.set(cv2.CAP_PROP_POS_MSEC, pos_ms)
            return True
        except Exception as e:
            logger.error(f"Erro ao definir posição do vídeo: {str(e)}")
            return False
    
    def get_current_time(self) -> int:
        """
        Obtém o tempo atual do vídeo em milissegundos.
        
        Returns:
            Tempo em milissegundos
        """
        if not self.cap or not self.cap.isOpened() or self.is_camera:
            return 0
            
        try:
            return int(self.cap.get(cv2.CAP_PROP_POS_MSEC))
        except Exception as e:
            logger.error(f"Erro ao obter tempo do vídeo: {str(e)}")
            return 0
    
    def release(self):
        """Libera os recursos da câmera."""
        try:
            if self.cap:
                self.cap.release()
                self.cap = None
            self.last_frame_time = None
            self.video_path = None
            self.is_camera = False
            logger.info("Recursos da câmera liberados")
        except Exception as e:
            logger.error(f"Erro ao liberar recursos: {str(e)}")