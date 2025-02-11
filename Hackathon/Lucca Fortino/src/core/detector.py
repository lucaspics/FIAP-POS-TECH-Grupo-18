"""
Detector de objetos otimizado para processamento local.
"""

from ultralytics import YOLO
import numpy as np
import cv2
from typing import List, Dict, Optional
import time
from datetime import datetime
import logging
from pathlib import Path
import asyncio
import torch
from torch.serialization import add_safe_globals, safe_globals
from ultralytics.nn.tasks import DetectionModel
from torch.nn.modules.container import Sequential
from ultralytics.nn.modules.conv import Conv
from ultralytics.nn.modules.block import C2f, Bottleneck, C3, C2, SPPF, C3TR
from ultralytics.nn.modules.head import Detect
from torch.nn.modules.conv import Conv2d
import functools
from config.app_config import MODEL_CONFIG

# Classes necessárias para carregar o modelo
SAFE_CLASSES = [
    DetectionModel,
    Sequential,
    Conv,
    C2f,
    Bottleneck,
    C3,
    C2,
    SPPF,
    C3TR,
    Detect,
    Conv2d
]

class Detection:
    """Classe para representar uma detecção individual."""
    def __init__(self, class_name: str, confidence: float, bbox: List[float]):
        self.class_name = class_name
        self.confidence = confidence
        self.bbox = bbox

    def to_dict(self) -> Dict:
        """Converte a detecção para dicionário."""
        return {
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": self.bbox
        }

class DetectionResult:
    """Classe para representar o resultado completo de uma detecção."""
    def __init__(self, detections: List[Detection], timestamp: datetime):
        self.detections = detections
        self.timestamp = timestamp

    def to_dict(self) -> Dict:
        """Converte o resultado para dicionário."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "detections": [det.to_dict() for det in self.detections]
        }

class ObjectDetector:
    """Detector de objetos otimizado para processamento local."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Inicializa o detector de objetos.
        
        Args:
            model_path: Caminho para o modelo YOLOv8 treinado. Se None, usa o caminho do MODEL_CONFIG
        """
        self.logger = logging.getLogger(__name__)
        self.model_path = Path(model_path) if model_path else Path(MODEL_CONFIG['path'])
        self.confidence_threshold = MODEL_CONFIG['confidence_threshold']
        self.target_height = MODEL_CONFIG['target_height']
        self.start_time = datetime.now()
        self.total_detections = 0
        self._load_model()
        
    def _load_model(self):
        """Carrega o modelo com configurações otimizadas."""
        try:
            # Adicionar classes necessárias aos globals seguros do PyTorch
            with safe_globals(SAFE_CLASSES):
                # Forçar carregamento sem weights_only
                original_load = torch.load
                torch.load = lambda f, *args, **kwargs: original_load(f, weights_only=False, *args, **kwargs)
                
                try:
                    self.model = YOLO(self.model_path)
                    self.classes = self.model.names
                    self.logger.info(f"Modelo carregado com sucesso: {self.model_path}")
                    self.logger.info(f"Classes disponíveis: {self.classes}")
                finally:
                    torch.load = original_load
            
            # Realizar warmup do modelo
            self._warmup_model()
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo: {str(e)}")
            raise

    def _warmup_model(self):
        """Realiza warmup do modelo com uma imagem em branco."""
        try:
            dummy_image = np.zeros((self.target_height, self.target_height, 3), dtype=np.uint8)
            with torch.no_grad():
                for _ in range(3):
                    self.model(dummy_image)
                    
            if hasattr(torch, 'cuda'):
                torch.cuda.empty_cache()
                
        except Exception as e:
            self.logger.error(f"Erro durante warmup: {str(e)}")

    async def detect(self, image: np.ndarray, conf_threshold: Optional[float] = None) -> DetectionResult:
        """
        Realiza detecção de objetos em uma imagem.
        
        Args:
            image: Imagem numpy array (BGR)
            conf_threshold: Threshold de confiança mínima. Se None, usa o valor do MODEL_CONFIG
            
        Returns:
            DetectionResult contendo as detecções encontradas
        """
        try:
            # Usar threshold das configurações se não especificado
            threshold = conf_threshold if conf_threshold is not None else self.confidence_threshold

            # Limpar memória CUDA se disponível
            if hasattr(torch, 'cuda'):
                torch.cuda.empty_cache()

            # Executar inferência de forma assíncrona na imagem original
            def inference_job():
                with torch.no_grad():
                    return self.model(image, conf=threshold, imgsz=image.shape[:2])[0]

            results = await asyncio.to_thread(inference_job)
            
            if results is None:
                return DetectionResult([], datetime.now())

            # Processar resultados
            boxes_np = results.boxes.data.cpu().numpy()
            del results  # Liberar memória
            
            if hasattr(torch, 'cuda'):
                torch.cuda.empty_cache()

            # Processar detecções
            detections = []
            for box in boxes_np:
                try:
                    x1, y1, x2, y2, conf, cls = map(float, box)
                    cls_id = int(cls)
                    
                    detection = Detection(
                        class_name=str(self.classes[cls_id]),
                        confidence=float(conf),
                        bbox=[float(x1), float(y1), float(x2), float(y2)]
                    )
                    detections.append(detection)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar detecção: {str(e)}")
                    continue

            self.total_detections += len(detections)
            return DetectionResult(detections, datetime.now())

        except Exception as e:
            self.logger.error(f"Erro durante detecção: {str(e)}")
            if hasattr(torch, 'cuda'):
                torch.cuda.empty_cache()
            return DetectionResult([], datetime.now())

    def draw_detections(self, image: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """
        Desenha as detecções na imagem.
        
        Args:
            image: Imagem numpy array (BGR)
            detections: Lista de detecções
            
        Returns:
            Imagem com as detecções desenhadas
        """
        img_draw = image.copy()
        
        for det in detections:
            try:
                x1, y1, x2, y2 = map(int, det.bbox)
                label = f"{det.class_name} {det.confidence:.2f}"
                
                # Usar cor amarela fixa para o bbox (BGR)
                color = (0, 255, 255)  # Amarelo em BGR
                
                # Desenhar bbox com espessura maior para melhor visibilidade
                cv2.rectangle(img_draw, (x1, y1), (x2, y2), color, 3)
                
                # Configurar texto
                font_scale = 1.0  # Aumentar tamanho da fonte
                font_thickness = 2
                (label_width, label_height), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
                )
                
                # Desenhar background do texto em amarelo
                cv2.rectangle(
                    img_draw,
                    (x1, y1 - label_height - 10),
                    (x1 + label_width, y1),
                    color,
                    -1
                )
                
                # Desenhar texto em preto com fonte maior
                cv2.putText(
                    img_draw,
                    label,
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    (0, 0, 0),  # Preto
                    font_thickness
                )
                
            except Exception as e:
                self.logger.error(f"Erro ao desenhar detecção: {str(e)}")
                continue
                
        return img_draw

    def is_model_loaded(self) -> bool:
        """Verifica se o modelo está carregado corretamente."""
        return hasattr(self, "model") and self.model is not None

    def get_uptime(self) -> str:
        """Retorna o tempo de execução do detector."""
        return str(datetime.now() - self.start_time)

    def get_model_info(self) -> Dict:
        """Retorna informações sobre o modelo carregado."""
        return {
            "path": str(self.model_path),
            "classes": self.classes,
            "type": self.model.task,
            "total_detections": self.total_detections,
            "confidence_threshold": self.confidence_threshold,
            "target_height": self.target_height
        }