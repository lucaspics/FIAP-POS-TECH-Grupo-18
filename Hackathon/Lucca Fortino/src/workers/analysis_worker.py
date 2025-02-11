import cv2
import time
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from config.logging_config import logger
from config.app_config import MODEL_CONFIG
from core import (
    ObjectDetector,
    AlertManager,
    Detection,
    DetectionResult,
    resize_frame,
    bgr_to_rgb,
    rgb_to_bgr
)

class AnalysisWorker(QThread):
    """Worker thread para processar análises de frames."""
    analysis_complete = pyqtSignal(dict)  # Sinal emitido quando a análise é concluída
    analysis_error = pyqtSignal(str)      # Sinal emitido em caso de erro
    
    # Compartilhar instâncias entre workers
    _detector = None
    _alert_manager = None
    
    @classmethod
    def initialize(cls, model_path: str, alert_dir: str):
        """
        Inicializa as instâncias compartilhadas do detector e gerenciador de alertas.
        
        Args:
            model_path: Caminho para o modelo YOLO
            alert_dir: Diretório para salvar alertas
        """
        if cls._detector is None:
            try:
                cls._detector = ObjectDetector(model_path)
                logger.info("Detector inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar detector: {str(e)}")
                raise
                
        if cls._alert_manager is None:
            try:
                cls._alert_manager = AlertManager(alert_dir)
                logger.info("AlertManager inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar AlertManager: {str(e)}")
                raise
    
    def __init__(self, frame_rgb, frame_number=None, video_time=0):
        """
        Inicializa o worker.
        
        Args:
            frame_rgb: Frame em formato RGB
            frame_number: Número do frame (opcional)
            video_time: Tempo do vídeo em ms
        """
        super().__init__()
        self.frame_rgb = frame_rgb.copy()
        self.frame_number = frame_number
        self.video_time = video_time
        
        # Verificar se as instâncias compartilhadas foram inicializadas
        if self._detector is None or self._alert_manager is None:
            raise RuntimeError("Worker não inicializado. Chame AnalysisWorker.initialize() primeiro")
    
    async def analyze(self):
        """Realiza a análise do frame."""
        try:
            # Converter frame para BGR para o detector
            frame_bgr = rgb_to_bgr(self.frame_rgb)
            
            # Realizar detecção
            result = await self._detector.detect(
                frame_bgr,
                conf_threshold=MODEL_CONFIG['confidence_threshold']
            )
            
            # Processar alerta se necessário
            alert_triggered = await self._alert_manager.process_detection(
                result,
                frame_bgr,
                self.video_time
            )
            
            # Converter resultado para formato compatível com a interface atual
            return {
                "timestamp": result.timestamp.isoformat(),
                "detections": [det.to_dict() for det in result.detections],
                "alert_triggered": int(alert_triggered)
            }
            
        except Exception as e:
            self._handle_error(e)
            return None
    
    def _handle_error(self, error):
        """Trata erros ocorridos durante a análise."""
        error_msg = str(error) if str(error).strip() else "Erro desconhecido"
        frame_info = f"frame {self.frame_number}" if self.frame_number is not None else "frame desconhecido"
        full_error = f"Erro na análise do {frame_info}: {error_msg}"
        logger.error(full_error)
        self.analysis_error.emit(full_error)
    
    def run(self):
        """Executa a análise em uma thread separada."""
        try:
            import asyncio
            # Criar novo event loop para a thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Executar análise
            result = loop.run_until_complete(self.analyze())
            
            # Fechar loop
            loop.close()
            
            if result:
                self.analysis_complete.emit(result)
            else:
                self.analysis_error.emit("Análise não retornou resultados")
                
        except Exception as e:
            error_msg = f"Erro durante análise do frame {self.frame_number}: {str(e)}"
            logger.error(error_msg)
            self.analysis_error.emit(error_msg)
            
        finally:
            # Garantir que o loop seja fechado
            try:
                loop.close()
            except Exception:
                pass