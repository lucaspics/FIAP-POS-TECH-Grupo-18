"""
Worker thread para processar análises de frames de forma assíncrona.
"""

import cv2
import time
from datetime import datetime
import asyncio
from typing import Optional, Dict, Any
from PyQt5.QtCore import QThread, pyqtSignal
from config.logging_config import get_logger
from config.app_config import MODEL_CONFIG, VIDEO_CONFIG
from core.detector import ObjectDetector
from core.alert_manager import AlertManager

class AnalysisWorker(QThread):
    """Worker thread para processar análises de frames."""
    
    # Sinais
    analysis_complete = pyqtSignal(dict)  # Sinal emitido quando a análise é concluída
    analysis_error = pyqtSignal(str)      # Sinal emitido em caso de erro
    metrics_update = pyqtSignal(dict)     # Sinal emitido com métricas de performance
    
    # Compartilhar instâncias entre workers
    _detector: Optional[ObjectDetector] = None
    _alert_manager: Optional[AlertManager] = None
    _event_loop: Optional[asyncio.AbstractEventLoop] = None
    
    @classmethod
    def initialize(cls, model_path: str, alert_dir: str):
        """
        Inicializa as instâncias compartilhadas do detector e gerenciador de alertas.
        
        Args:
            model_path: Caminho para o modelo YOLO
            alert_dir: Diretório para salvar alertas
        """
        logger = get_logger('analysis_worker')
        
        if cls._detector is None:
            try:
                cls._detector = ObjectDetector(model_path)
                logger.info("Detector inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar detector: {str(e)}")
                raise
                
        if cls._alert_manager is None:
            try:
                cls._alert_manager = AlertManager(
                    min_confidence=MODEL_CONFIG['confidence_threshold'],
                    max_alerts=1000
                )
                logger.info("AlertManager inicializado com sucesso")
            except Exception as e:
                logger.error(f"Erro ao inicializar AlertManager: {str(e)}")
                raise
    
    def __init__(self, frame_rgb, frame_number: Optional[int] = None, video_time: int = 0):
        """
        Inicializa o worker.
        
        Args:
            frame_rgb: Frame em formato RGB
            frame_number: Número do frame (opcional)
            video_time: Tempo do vídeo em ms
        """
        super().__init__()
        self.logger = get_logger('analysis_worker')
        self.frame_rgb = frame_rgb.copy()
        self.frame_number = frame_number
        self.video_time = video_time
        self.start_time = time.time()
        
        # Verificar se as instâncias compartilhadas foram inicializadas
        if self._detector is None or self._alert_manager is None:
            raise RuntimeError("Worker não inicializado. Chame AnalysisWorker.initialize() primeiro")
    
    def _emit_metrics(self, analysis_time: float, detection_count: int):
        """
        Emite métricas de performance.
        
        Args:
            analysis_time: Tempo de análise em segundos
            detection_count: Número de detecções
        """
        metrics = {
            'frame_number': self.frame_number,
            'analysis_time': analysis_time,
            'fps': 1.0 / analysis_time if analysis_time > 0 else 0,
            'detection_count': detection_count,
            'video_time': self.video_time,
            'timestamp': datetime.now().isoformat()
        }
        self.metrics_update.emit(metrics)
    
    async def analyze(self) -> Optional[Dict[str, Any]]:
        """
        Realiza a análise do frame de forma assíncrona.
        
        Returns:
            Dict com resultados da análise ou None em caso de erro
        """
        try:
            # Converter frame para BGR para o detector
            frame_bgr = cv2.cvtColor(self.frame_rgb, cv2.COLOR_RGB2BGR)
            
            # Redimensionar frame se necessário
            if frame_bgr.shape[0] != MODEL_CONFIG['target_height']:
                scale = MODEL_CONFIG['target_height'] / frame_bgr.shape[0]
                new_width = int(frame_bgr.shape[1] * scale)
                frame_bgr = cv2.resize(frame_bgr, (new_width, MODEL_CONFIG['target_height']))
            
            # Realizar detecção
            result = await self._detector.detect(
                frame_bgr,
                conf_threshold=MODEL_CONFIG['confidence_threshold']
            )
            
            # Processar alerta se necessário
            alert_id = None
            alert_triggered = await self._alert_manager.process_detection(
                result,
                frame_bgr,
                self.video_time
            )
            
            # Se um alerta foi gerado, buscar o ID do último alerta
            if alert_triggered:
                # Pegar o ID do último alerta gerado
                alerts = await asyncio.to_thread(self._alert_manager.get_recent_alerts, 1)
                if alerts:
                    alert_id = alerts[0].get('alert_id')
            
            # Calcular métricas
            analysis_time = time.time() - self.start_time
            self._emit_metrics(analysis_time, len(result.detections))
            
            # Converter resultado para formato compatível com a interface
            return {
                "timestamp": result.timestamp.isoformat(),
                "detections": [det.to_dict() for det in result.detections],
                "alert_triggered": int(alert_triggered),
                "analysis_time": analysis_time,
                "frame_number": self.frame_number,
                "video_time": self.video_time,
                "alert_id": alert_id  # Incluir o ID do alerta se foi gerado
            }
            
        except Exception as e:
            self._handle_error(e)
            return None
    
    def _handle_error(self, error: Exception):
        """
        Trata erros ocorridos durante a análise.
        
        Args:
            error: Exceção ocorrida
        """
        error_msg = str(error) if str(error).strip() else "Erro desconhecido"
        frame_info = f"frame {self.frame_number}" if self.frame_number is not None else "frame desconhecido"
        full_error = f"Erro na análise do {frame_info}: {error_msg}"
        
        self.logger.error(full_error, exc_info=True)
        self.analysis_error.emit(full_error)
    
    def run(self):
        """Executa a análise em uma thread separada."""
        try:
            # Criar novo event loop para a thread se necessário
            if self._event_loop is None or self._event_loop.is_closed():
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
            
            # Executar análise
            result = self._event_loop.run_until_complete(self.analyze())
            
            if result:
                self.analysis_complete.emit(result)
            else:
                self.analysis_error.emit("Análise não retornou resultados")
                
        except Exception as e:
            error_msg = f"Erro durante análise do frame {self.frame_number}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            self.analysis_error.emit(error_msg)
            
        finally:
            # Limpar recursos
            try:
                if self._event_loop and not self._event_loop.is_closed():
                    pending = asyncio.all_tasks(self._event_loop)
                    self._event_loop.run_until_complete(asyncio.gather(*pending))
                    self._event_loop.close()
            except Exception as e:
                self.logger.error(f"Erro ao limpar recursos: {str(e)}")
    
    @classmethod
    def cleanup(cls):
        """Limpa recursos compartilhados."""
        try:
            if cls._event_loop and not cls._event_loop.is_closed():
                cls._event_loop.close()
            cls._event_loop = None
        except Exception as e:
            logger = get_logger('analysis_worker')
            logger.error(f"Erro ao limpar recursos compartilhados: {str(e)}")