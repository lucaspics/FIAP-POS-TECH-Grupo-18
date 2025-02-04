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
alert_manager = AlertManager(settings)

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
        # Log detalhado da requisição recebida
        logger.info("\n==== Nova Requisição de Detecção ====")
        logger.info(f"Timestamp início: {datetime.now().isoformat()}")
        
        if not frame:
            logger.error("Nenhum frame recebido")
            return JSONResponse(content=empty_response)
        logger.info(f"Tipo do objeto frame: {type(frame)}")
        logger.info(f"Atributos disponíveis: {dir(frame)}")
        logger.info(f"Arquivo: {frame.filename}")
        # Verificar se o objeto tem o atributo headers antes de tentar acessá-lo
        if hasattr(frame, 'headers'):
            logger.info(f"Headers: {frame.headers}")
        else:
            logger.info("Frame não possui atributo headers")
            
        # Tentar obter o content-type de várias formas
        content_type = None
        # Verificar content_type de forma mais elegante
        content_type = None
        
        if hasattr(frame, 'content_type'):
            content_type = frame.content_type
            logger.info(f"Content-Type do atributo: {content_type}")
        elif hasattr(frame, 'headers') and frame.headers:
            content_type = frame.headers.get('content-type')
            logger.info(f"Content-Type dos headers: {content_type}")
        else:
            logger.info("Não foi possível determinar o content-type do frame")
        
        if content_type is None:
            content_type = 'image/jpeg'  # Valor padrão
            logger.info(f"Usando content-type padrão: {content_type}")
            
        # Atribuir o content-type ao frame
        frame._content_type = content_type
        
        logger.info(f"Content-Type final: {content_type}")
        logger.info(f"Confidence: {confidence}")
        logger.info(f"Return Image: {return_image}")
        
        try:
            # Ler e processar imagem
            contents = await frame.read()
            logger.info(f"Tamanho dos dados recebidos: {len(contents)} bytes")
            
            if len(contents) == 0:
                logger.error("Frame vazio recebido")
                return JSONResponse(content=empty_response)
            
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                logger.error("Falha ao decodificar imagem")
                return JSONResponse(content=empty_response)
            
            logger.info(f"Imagem decodificada com sucesso. Dimensões: {image.shape}")
        except Exception as e:
            logger.error(f"Erro ao processar imagem: {str(e)}")
            return JSONResponse(content=empty_response)
            
        # Realizar detecção com tratamento de erros melhorado
        logger.info("\n=== Debug Detecção ===")
        logger.info(f"Tipo do confidence threshold: {type(confidence)}")
        logger.info(f"Valor do confidence threshold: {confidence}")
        
        try:
            detections = await detector.detect(image, conf_threshold=confidence)
            
            # Se não houver detecções, logar como informação
            if not detections:
                logger.info("Nenhuma detecção encontrada no frame")
            else:
                logger.info("\n=== Debug Detecções ===")
                logger.info(f"Número de detecções: {len(detections)}")
                for i, det in enumerate(detections):
                    logger.info(f"\nDetecção {i+1}:")
                    for key, value in det.items():
                        logger.info(f"  {key}: {value} (tipo: {type(value)})")
            
        except Exception as e:
            logger.error(f"Erro durante detecção: {str(e)}")
            # Retornar resposta vazia em vez de erro 500
            return JSONResponse(
                status_code=200,
                content={
                    "timestamp": datetime.now().isoformat(),
                    "detections": [],
                    "alert_triggered": 0,
                    "error": str(e)
                }
            )
        
        # Verificar confiança das detecções
        confidences = [d["confidence"] for d in detections]
        logger.info(f"Confidence threshold: {settings.alert_threshold}")
        logger.info(f"Detecções confidences: {confidences}")
        
        # Calcular alert_triggered
        alert_check = any(d["confidence"] > settings.alert_threshold for d in detections)
        logger.info(f"Alert check (bool): {alert_check}, type: {type(alert_check)}")
        
        alert_triggered = 1 if alert_check else 0
        logger.info(f"Alert triggered (int): {alert_triggered}, type: {type(alert_triggered)}")
        # Validar e converter tipos antes de criar a resposta
        try:
            # Criar objetos Detection validados
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
            
            # Se todas as validações falharem, retornar resposta vazia
            if not validated_detections and detections:
                logger.error("Todas as detecções falharam na validação")
                return JSONResponse(content=empty_response)
            
            try:
                # Criar resposta com tipos validados
                results = DetectionResponse(
                    timestamp=str(datetime.now().isoformat()),
                    detections=validated_detections,
                    alert_triggered=int(alert_triggered)
                )
                
                # Log detalhado dos tipos
                logger.info("=== Validação de Tipos ===")
                logger.info(f"Timestamp type: {type(results.timestamp)}")
                logger.info(f"Alert triggered type: {type(results.alert_triggered)}")
                logger.info(f"Detections type: {type(results.detections)}")
                logger.info(f"DetectionResponse criado com sucesso: {results.model_dump()}")
                
            except Exception as resp_err:
                logger.error(f"Erro ao criar DetectionResponse: {str(resp_err)}")
                return JSONResponse(content=empty_response)
                
        except Exception as e:
            logger.error(f"Erro na validação de tipos: {str(e)}")
            return JSONResponse(content=empty_response)
        
        # Se houver detecções acima do threshold de alerta, notificar
        # Se houver detecções acima do threshold de alerta, notificar
        if results.alert_triggered == 1:
            try:
                await alert_manager.send_alert(image, detections)
            except Exception as e:
                logger.error(f"Erro ao enviar alerta: {str(e)}")
                # Continua a execução mesmo se o alerta falhar
        
        try:
            # Serializar manualmente para garantir tipos corretos
            try:
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
            except Exception as ser_err:
                logger.error(f"Erro na serialização básica: {str(ser_err)}")
                return JSONResponse(content=empty_response)

            # Se solicitado, incluir imagem com detecções
            if bool(return_image):  # Converter explicitamente para bool
                try:
                    # Converter detecções validadas de volta para o formato original
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
                    # Continuar sem a imagem em caso de erro
            
            try:
                # Log detalhado da serialização
                logger.info("=== Serialização Final ===")
                logger.info(f"timestamp type: {type(serialized_data['timestamp'])}")
                logger.info(f"alert_triggered type: {type(serialized_data['alert_triggered'])}")
                logger.info(f"detections type: {type(serialized_data['detections'])}")
                
                # Criar versão do JSON para log (sem a imagem)
                log_data = serialized_data.copy()
                if 'image' in log_data:
                    log_data['image'] = '<imagem removida do log>'
                
                # Log da versão sem imagem
                logger.info(f"JSON string: {json.dumps(log_data)}")
            except Exception as log_err:
                logger.error(f"Erro ao gerar logs: {str(log_err)}")
                # Continuar mesmo se o logging falhar
            
            # Calcular e logar métricas de tempo
            try:
                request_time = time.time() - request_start
                logger.info("\n=== Métricas de Performance ===")
                logger.info(f"Tempo total de processamento: {request_time:.2f}s")
                logger.info(f"Timestamp fim: {datetime.now().isoformat()}")
                logger.info("================================\n")
            except Exception as perf_err:
                logger.error(f"Erro ao calcular métricas: {str(perf_err)}")
            
            return JSONResponse(content=serialized_data)
        except Exception as e:
            logger.error(f"Erro fatal na serialização: {str(e)}")
            return JSONResponse(content=empty_response)
        
    except Exception as e:
        try:
            request_time = time.time() - request_start
            logger.error(f"Erro ao processar detecção (após {request_time:.2f}s): {str(e)}")
            logger.error("Stacktrace completo:", exc_info=True)
        except:
            logger.error("Erro ao processar exceção", exc_info=True)
        
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