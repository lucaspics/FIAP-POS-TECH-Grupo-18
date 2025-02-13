"""
Gerenciador de análise de frames.
"""

import cv2
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
from config.logging_config import get_logger
from config.app_config import MODEL_CONFIG, VIDEO_CONFIG
from workers.analysis_worker import AnalysisWorker
from core.video_utils import resize_frame, bgr_to_rgb

logger = get_logger('analysis_manager')

class AnalysisManager(QObject):
    """Gerenciador de análise de frames."""
    
    # Sinais
    analysis_complete = pyqtSignal(dict)  # Emitido quando uma análise é concluída
    analysis_error = pyqtSignal(str)      # Emitido quando ocorre um erro
    metrics_update = pyqtSignal(dict)     # Emitido com métricas de performance
    
    def __init__(self):
        """Inicializa o gerenciador de análise."""
        super().__init__()
        
        # Contadores e controle
        self.current_frame_count: int = 0
        self.last_analyzed_frame: int = 0
        self.current_video_time: int = 0
        
        # Workers
        self.active_workers: List[AnalysisWorker] = []
        self.max_concurrent_workers: int = VIDEO_CONFIG['max_concurrent_workers']
        self.analysis_interval: int = VIDEO_CONFIG['analysis_interval']
        
        # Cache
        self.last_frame: Optional[np.ndarray] = None
        
        # Métricas
        self.total_analyses: int = 0
        self.total_detections: int = 0
        self.start_time: float = datetime.now().timestamp()
    
    def initialize(self, model_path: str, alert_dir: str) -> bool:
        """
        Inicializa o sistema de análise.
        
        Args:
            model_path: Caminho para o modelo YOLO
            alert_dir: Diretório para salvar alertas
            
        Returns:
            bool indicando sucesso da inicialização
        """
        try:
            AnalysisWorker.initialize(model_path, alert_dir)
            logger.info("Sistema de análise inicializado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar sistema de análise: {str(e)}")
            return False
    
    def process_frame(self, frame: np.ndarray, video_time: int = 0, is_last_frame: bool = False) -> bool:
        """
        Processa um novo frame.
        
        Args:
            frame: Frame para processar
            video_time: Tempo do vídeo em ms
            is_last_frame: Indica se é o último frame do vídeo
            
        Returns:
            bool indicando se o frame foi enviado para análise
        """
        try:
            # Atualizar contadores
            self.current_frame_count += 1
            self.current_video_time = video_time
            
            # Armazenar último frame
            self.last_frame = frame.copy()
            
            # Limpar workers concluídos
            self.active_workers = [w for w in self.active_workers if not w.isFinished()]
            
            # Verificar se devemos analisar este frame
            frames_since_last = self.current_frame_count - self.last_analyzed_frame
            # Sempre analisar o último frame ou seguir o intervalo normal
            if is_last_frame or (frames_since_last >= self.analysis_interval and
                len(self.active_workers) < self.max_concurrent_workers):
                self.analyze_frame(frame, is_last_frame)
                self.last_analyzed_frame = self.current_frame_count
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao processar frame: {str(e)}")
            return False
    
    def analyze_frame(self, frame: np.ndarray, is_last_frame: bool = False):
        """
        Inicia a análise de um frame.
        
        Args:
            frame: Frame para analisar
            is_last_frame: Indica se é o último frame do vídeo
        """
        try:
            # Preparar frame
            frame = resize_frame(frame, target_height=MODEL_CONFIG['target_height'])
            if frame is None:
                raise ValueError("Frame inválido após redimensionamento")
                
            frame_rgb = bgr_to_rgb(frame.copy())
            if frame_rgb is None:
                raise ValueError("Erro na conversão BGR->RGB")
            
            # Criar e configurar worker
            worker = AnalysisWorker(
                frame_rgb,
                self.current_frame_count,
                self.current_video_time,
                is_last_frame=is_last_frame
            )
            
            # Conectar sinais
            worker.analysis_complete.connect(self._handle_analysis_complete)
            worker.analysis_error.connect(self._handle_analysis_error)
            worker.metrics_update.connect(self._handle_metrics_update)
            
            # Iniciar análise
            self.active_workers.append(worker)
            worker.start()
            
            logger.debug(f"Análise iniciada para frame {self.current_frame_count}")
            
        except Exception as e:
            logger.error(f"Erro ao criar worker: {str(e)}")
            self.analysis_error.emit(str(e))
    
    def _handle_analysis_complete(self, result: Dict[str, Any]):
        """
        Processa o resultado da análise.
        
        Args:
            result: Resultado da análise
        """
        try:
            # Atualizar métricas
            self.total_analyses += 1
            self.total_detections += len(result.get('detections', []))
            
            # Emitir resultado
            self.analysis_complete.emit(result)
            
        except Exception as e:
            logger.error(f"Erro ao processar resultado: {str(e)}")
    
    def _handle_analysis_error(self, error_msg: str):
        """
        Trata erros na análise.
        
        Args:
            error_msg: Mensagem de erro
        """
        logger.error(f"Erro na análise do frame {self.current_frame_count}: {error_msg}")
        self.analysis_error.emit(error_msg)
    
    def _handle_metrics_update(self, metrics: Dict[str, Any]):
        """
        Processa atualização de métricas.
        
        Args:
            metrics: Métricas atualizadas
        """
        try:
            # Adicionar métricas globais
            runtime = datetime.now().timestamp() - self.start_time
            metrics.update({
                'total_analyses': self.total_analyses,
                'total_detections': self.total_detections,
                'runtime': runtime,
                'analyses_per_second': self.total_analyses / runtime if runtime > 0 else 0
            })
            
            # Emitir métricas
            self.metrics_update.emit(metrics)
            
        except Exception as e:
            logger.error(f"Erro ao processar métricas: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do gerenciador.
        
        Returns:
            Dict com estatísticas
        """
        runtime = datetime.now().timestamp() - self.start_time
        return {
            'total_frames': self.current_frame_count,
            'analyzed_frames': self.total_analyses,
            'total_detections': self.total_detections,
            'active_workers': len(self.active_workers),
            'runtime': runtime,
            'analyses_per_second': self.total_analyses / runtime if runtime > 0 else 0,
            'detection_rate': self.total_detections / self.total_analyses if self.total_analyses > 0 else 0
        }
    
    def cleanup(self):
        """Limpa recursos do gerenciador."""
        try:
            # Parar workers ativos
            for worker in self.active_workers:
                if not worker.isFinished():
                    worker.terminate()
                    worker.wait()
            
            self.active_workers.clear()
            self.last_frame = None
            logger.info("Recursos do gerenciador de análise liberados")
            
        except Exception as e:
            logger.error(f"Erro ao limpar recursos: {str(e)}")