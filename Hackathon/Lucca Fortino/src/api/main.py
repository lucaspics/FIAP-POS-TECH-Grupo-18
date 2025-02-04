from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import numpy as np
import cv2
from typing import List, Dict
import logging
from datetime import datetime
import asyncio
from pathlib import Path
import json
import time
from pydantic import BaseModel

class Detection(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float]

    class Config:
        extra = "forbid"  # Proibir campos extras

class DetectionResponse(BaseModel):
    timestamp: str
    detections: List[Detection]
    alert_triggered: int

    class Config:
        extra = "forbid"  # Proibir campos extras

    @property
    def dict(self):
        data = super().dict()
        # Garantir que alert_triggered é int
        data['alert_triggered'] = int(data['alert_triggered'])
        return data

    def model_dump(self):
        data = super().model_dump()
        # Garantir que alert_triggered é int
        data['alert_triggered'] = int(data['alert_triggered'])
        return data

from src.api.detector import ObjectDetector
from src.api.alert_manager import AlertManager
from src.api.config import Settings

app = FastAPI(title="VisionGuard API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Carregar configurações
settings = Settings()

# Inicializar detector e gerenciador de alertas
detector = ObjectDetector(settings.model_path)
alert_manager = AlertManager(settings, detector)

@app.on_event("startup")
async def startup_event():
    """Evento de inicialização da API."""
    logger.info("Iniciando API VisionGuard...")
    
    # Criar diretórios necessários
    Path("logs").mkdir(exist_ok=True)
    Path("temp").mkdir(exist_ok=True)
    
    # Verificar modelo
    if not Path(settings.model_path).exists():
        logger.error(f"Modelo não encontrado: {settings.model_path}")
        raise RuntimeError("Modelo de detecção não encontrado")

@app.on_event("shutdown")
async def shutdown_event():
    """Evento de finalização da API."""
    logger.info("Finalizando API VisionGuard...")
    
    # Limpar recursos do AlertManager
    try:
        await alert_manager.cleanup()
        logger.info("AlertManager finalizado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao finalizar AlertManager: {str(e)}")

@app.get("/")
async def root():
    """Endpoint raiz para verificação de status."""
    return {
        "status": "online",
        "version": "1.0.0",
        "model": settings.model_path
    }

@app.post("/detect")
async def detect_objects(
    frame: UploadFile = File(...),
    confidence: float = 0.1,
    return_image: bool = False
) -> Dict:
    """
    Detecta objetos cortantes em um frame.
    
    Args:
        frame: Arquivo de imagem
        confidence: Threshold de confiança
        return_image: Se deve retornar a imagem com as detecções
        
    Returns:
        Dicionário com resultados da detecção
    """
    request_start = time.time()
    
    # Criar resposta padrão vazia
    empty_response = {
        "timestamp": datetime.now().isoformat(),
        "detections": [],
        "alert_triggered": 0
    }
    
    try:
        # Log básico da requisição
        logger.info("Nova requisição de detecção recebida")
        
        if not frame:
            logger.error("Nenhum frame recebido")
            return JSONResponse(content=empty_response)
            
        # Definir content-type
        content_type = getattr(frame, 'content_type', None) or \
                      (frame.headers.get('content-type') if hasattr(frame, 'headers') else None) or \
                      'image/jpeg'
        
        # Atribuir o content-type ao frame
        frame._content_type = content_type
        
        try:
            # Processar imagem
            contents = await frame.read()
            if len(contents) == 0:
                logger.error("Frame vazio recebido")
                return JSONResponse(content=empty_response)
            
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("Falha ao decodificar imagem")
                return JSONResponse(content=empty_response)
            
            # Redimensionar imagem
            height, width = image.shape[:2]
            target_height = 320
            target_width = int(width * (target_height / height))
            image = cv2.resize(image, (target_width, target_height), interpolation=cv2.INTER_AREA)
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {str(e)}")
            return JSONResponse(content=empty_response)
            
        # Realizar detecção
        try:
            detections = await detector.detect(image, conf_threshold=confidence)
            
            if not detections:
                logger.info("Nenhuma detecção encontrada no frame")
            else:
                logger.info(f"Encontradas {len(detections)} detecções")
            
        except Exception as e:
            logger.error(f"Erro durante detecção: {str(e)}")
            return JSONResponse(
                status_code=200,
                content={
                    "timestamp": datetime.now().isoformat(),
                    "detections": [],
                    "alert_triggered": 0,
                    "error": str(e)
                }
            )
        
        # Verificar alertas
        alert_check = any(d["confidence"] > settings.alert_threshold for d in detections)
        alert_triggered = 1 if alert_check else 0
        
        if alert_triggered:
            logger.info(f"Alerta ativado - {len(detections)} objetos detectados")
        # Validar detecções
        try:
            validated_detections = []
            for det in detections:
                try:
                    detection = Detection(
                        class_name=str(det.get("class_name", det.get("class", "unknown"))),
                        confidence=float(det["confidence"]),
                        bbox=[float(x) for x in det["bbox"]]
                    )
                    validated_detections.append(detection)
                except Exception as det_err:
                    logger.error(f"Erro ao validar detecção: {str(det_err)}")
                    continue
            
            if not validated_detections and detections:
                logger.error("Falha na validação das detecções")
                return JSONResponse(content=empty_response)
            
            results = DetectionResponse(
                timestamp=str(datetime.now().isoformat()),
                detections=validated_detections,
                alert_triggered=int(alert_triggered)
            )
            
        except Exception as e:
            logger.error(f"Erro na validação: {str(e)}")
            return JSONResponse(content=empty_response)
        
        # Se houver detecções acima do threshold de alerta, notificar
        # Se houver detecções acima do threshold de alerta, notificar
        if results.alert_triggered == 1:
            try:
                # Converter detecções para o formato correto
                formatted_detections = [
                    {
                        "class_name": det.class_name,
                        "confidence": det.confidence,
                        "bbox": det.bbox
                    }
                    for det in validated_detections
                ]
                await alert_manager.send_alert(image, formatted_detections)
            except Exception as e:
                logger.error(f"Erro ao enviar alerta: {str(e)}")
                # Continua a execução mesmo se o alerta falhar
        
        try:
            # Serializar resposta
            serialized_data = {
                "timestamp": str(results.timestamp),
                "alert_triggered": int(results.alert_triggered),
                "detections": [
                    {
                        "class_name": str(det.class_name),
                        "confidence": float(det.confidence),
                        "bbox": [float(x) for x in det.bbox]
                    }
                    for det in results.detections
                ]
            }

            # Adicionar imagem se solicitado
            if bool(return_image):
                try:
                    draw_detections = [
                        {
                            "class_name": det.class_name,
                            "confidence": det.confidence,
                            "bbox": det.bbox
                        }
                        for det in results.detections
                    ]
                    annotated_image = detector.draw_detections(image, draw_detections)
                    serialized_data["image"] = _encode_image(annotated_image)
                except Exception as img_err:
                    logger.error(f"Erro ao processar imagem de retorno: {str(img_err)}")

            # Log de performance
            request_time = time.time() - request_start
            logger.info(f"Processamento concluído em {request_time:.2f}s")
            
            return JSONResponse(content=serialized_data)
        except Exception as e:
            logger.error(f"Erro na serialização: {str(e)}")
            return JSONResponse(content=empty_response)
        
    except Exception as e:
        logger.error("Erro no processamento da detecção:", exc_info=True)
        return JSONResponse(
            content={
                "timestamp": datetime.now().isoformat(),
                "detections": [],
                "alert_triggered": 0,
                "error": "Erro interno no processamento da detecção"
            }
        )

@app.get("/health")
async def health_check():
    """Verificação de saúde da API."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "model_loaded": detector.is_model_loaded()
    }

@app.get("/stats")
async def get_stats():
    """Retorna estatísticas da API."""
    return {
        "total_detections": detector.total_detections,
        "total_alerts": alert_manager.total_alerts,
        "uptime": detector.get_uptime(),
        "model_info": detector.get_model_info()
    }

def _encode_image(image: np.ndarray) -> str:
    """
    Codifica imagem em base64 para retorno na API.
    """
    import base64
    _, buffer = cv2.imencode(".jpg", image)
    img_bytes = buffer.tobytes()
    img_base64 = base64.b64encode(img_bytes).decode()
    return f"data:image/jpeg;base64,{img_base64}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)