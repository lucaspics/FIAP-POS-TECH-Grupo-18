from ultralytics import YOLO
import numpy as np
import cv2
from typing import List, Dict
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

# Lista de todas as classes necessárias para carregar o modelo
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

class ObjectDetector:
    def __init__(self, model_path: str):
        """
        Inicializa o detector de objetos.
        
        Args:
            model_path: Caminho para o modelo YOLOv8 treinado
        """
        self.logger = logging.getLogger(__name__)
        self.model_path = Path(model_path)
        self.start_time = datetime.now()
        self.total_detections = 0
        
        try:
            # Adicionar classes necessárias aos globals seguros do PyTorch
            with safe_globals(SAFE_CLASSES):
                # Forçar carregamento sem weights_only
                original_load = torch.load
                torch.load = lambda f, *args, **kwargs: original_load(f, weights_only=False, *args, **kwargs)
                
                try:
                    self.model = YOLO(model_path)
                    self.classes = self.model.names
                    self.logger.info(f"Modelo carregado com sucesso: {model_path}")
                    self.logger.info(f"Classes disponíveis: {self.classes}")
                finally:
                    torch.load = original_load
            
            # Realizar warmup do modelo
            self.logger.info("Iniciando warmup do modelo...")
            self._warmup_model()
            self.logger.info("Warmup concluído com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo: {str(e)}")
            raise

    def _warmup_model(self):
        """Realiza warmup do modelo com uma imagem em branco."""
        try:
            # Criar imagem em branco para warmup
            dummy_image = np.zeros((320, 320, 3), dtype=np.uint8)
            
            # Realizar algumas inferências para aquecer o modelo
            with torch.no_grad():
                for _ in range(3):  # 3 inferências de warmup
                    self.model(dummy_image)
                    
            if hasattr(torch, 'cuda'):
                torch.cuda.empty_cache()
                
        except Exception as e:
            self.logger.error(f"Erro durante warmup: {str(e)}")
            # Não levantar exceção para não impedir a inicialização

    async def detect(self, image: np.ndarray, conf_threshold: float = 0.25) -> List[Dict]:
        """
        Realiza detecção de objetos em uma imagem.
        
        Args:
            image: Imagem numpy array (BGR)
            conf_threshold: Threshold de confiança mínima
            
        Returns:
            Lista de detecções no formato:
            [
                {
                    "class": str,
                    "confidence": float,
                    "bbox": [x1, y1, x2, y2]
                },
                ...
            ]
        """
        try:
            # Log do estado inicial
            self.logger.info("\n=== Iniciando Nova Detecção ===")
            self.logger.info(f"Timestamp: {datetime.now().isoformat()}")
            self.logger.info(f"Confidence threshold: {conf_threshold}")
            self.logger.info(f"Dimensões da imagem: {image.shape}")
            
            if hasattr(torch, 'cuda'):
                self.logger.info(f"Memória CUDA antes da limpeza: {torch.cuda.memory_allocated() / 1024 / 1024:.2f}MB")
                torch.cuda.empty_cache()
                self.logger.info(f"Memória CUDA após limpeza: {torch.cuda.memory_allocated() / 1024 / 1024:.2f}MB")
                self.logger.info(f"Dispositivo CUDA: {torch.cuda.get_device_name() if torch.cuda.is_available() else 'N/A'}")
            
            # Executar inferência (temporariamente sem timeout)
            try:
                # Criar tarefa de inferência em uma nova thread
                self.logger.info("Iniciando inferência do modelo...")
                start_time = time.time()
                
                def inference_job():
                    with torch.no_grad():  # Reduzir uso de memória
                        return self.model(image, conf=conf_threshold)[0]
                
                # Executar inferência de forma assíncrona
                results = await asyncio.to_thread(inference_job)
                
                inference_time = time.time() - start_time
                self.logger.info(f"Inferência concluída com sucesso em {inference_time:.2f}s")
                
            except Exception as e:
                self.logger.error(f"Erro durante inferência: {str(e)}")
                if hasattr(torch, 'cuda'):
                    torch.cuda.empty_cache()
                return []
            
            finally:
                if hasattr(torch, 'cuda'):
                    torch.cuda.empty_cache()
                
            if results is None:
                return []
                
            try:
                # Processar resultados YOLO
                self.logger.info("\n=== Processando Resultados YOLO ===")
                self.logger.info("Convertendo resultados para CPU...")
                start_process = time.time()
                
                # Converter boxes para numpy e liberar memória CUDA
                boxes_np = results.boxes.data.cpu().numpy()
                process_time = time.time() - start_process
                self.logger.info(f"Conversão para CPU concluída em {process_time:.2f}s")
                
                del results
                if hasattr(torch, 'cuda'):
                    torch.cuda.empty_cache()
                    self.logger.info("Memória CUDA liberada")
                
                self.logger.info(f"Shape dos boxes numpy: {boxes_np.shape}")
                self.logger.info(f"Uso de memória atual: {torch.cuda.memory_allocated() if hasattr(torch, 'cuda') else 'N/A'}")
                
                # Processar cada detecção
                detections = []
                for i, box in enumerate(boxes_np):
                    try:
                        x1, y1, x2, y2, conf, cls = map(float, box)
                        cls_id = int(cls)
                        
                        detection = {
                            "class_name": str(self.classes[cls_id]),
                            "confidence": float(conf),
                            "bbox": [float(x1), float(y1), float(x2), float(y2)]
                        }
                        
                        detections.append(detection)
                        self.logger.info(f"Detecção {i+1} processada: {detection}")
                        
                    except Exception as e:
                        self.logger.error(f"Erro ao processar detecção {i}: {str(e)}")
                        continue
                
                self.total_detections += len(detections)
                self.logger.info(f"Detecção concluída. {len(detections)} objetos encontrados")
                return detections
                
            except Exception as e:
                self.logger.error(f"Erro ao processar resultados: {str(e)}")
                return []
                
            finally:
                # Limpar memória novamente
                if hasattr(torch, 'cuda'):
                    torch.cuda.empty_cache()
            
        except Exception as e:
            self.logger.error(f"Erro durante detecção: {str(e)}")
            if hasattr(torch, 'cuda'):
                torch.cuda.empty_cache()
            return []

    def draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Desenha as detecções na imagem.
        
        Args:
            image: Imagem numpy array (BGR)
            detections: Lista de detecções do método detect()
            
        Returns:
            Imagem com as detecções desenhadas
        """
        img_draw = image.copy()
        
        for det in detections:
            # Extrair informações
            try:
                x1, y1, x2, y2 = map(int, det["bbox"])
                label = f"{det['class_name']} {det['confidence']:.2f}"
                
                # Definir cor baseada na classe e confiança
                color = self._get_color(det["class_name"], det["confidence"])
            except KeyError as e:
                self.logger.error(f"Erro ao acessar chave no dicionário de detecção: {str(e)}")
                continue
            except Exception as e:
                self.logger.error(f"Erro ao processar detecção para desenho: {str(e)}")
                continue
            
            # Desenhar bbox
            cv2.rectangle(img_draw, (x1, y1), (x2, y2), color, 2)
            
            # Adicionar label
            font_scale = 0.6
            font_thickness = 1
            (label_width, label_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
            )
            
            # Desenhar background do texto
            cv2.rectangle(
                img_draw,
                (x1, y1 - label_height - 10),
                (x1 + label_width, y1),
                color,
                -1
            )
            
            # Desenhar texto
            cv2.putText(
                img_draw,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (0, 0, 0),  # Cor preta para o texto
                font_thickness
            )
            
        return img_draw

    def is_model_loaded(self) -> bool:
        """Verifica se o modelo está carregado corretamente."""
        return hasattr(self, "model") and self.model is not None

    def get_uptime(self) -> str:
        """Retorna o tempo de execução do detector."""
        uptime = datetime.now() - self.start_time
        return str(uptime)

    def get_model_info(self) -> Dict:
        """Retorna informações sobre o modelo carregado."""
        return {
            "path": str(self.model_path),
            "classes": self.classes,
            "type": self.model.task,
            "total_detections": self.total_detections
        }

    def _get_color(self, class_name: str, confidence: float = 0.0) -> tuple:
        """
        Retorna amarelo brilhante para todas as detecções.
        
        Args:
            class_name: Nome da classe (não usado)
            confidence: Nível de confiança (não usado)
            
        Returns:
            Tupla BGR (Amarelo)
        """
        return (0, 255, 255)  # Amarelo em BGR