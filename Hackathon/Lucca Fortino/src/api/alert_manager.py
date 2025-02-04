import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import cv2
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import List, Dict, Optional
import json
import aiofiles
import asyncio
from .config import Settings
from ..config.app_config import CONFIDENCE_LEVELS, REQUIRED_DETECTIONS, DETECTION_WINDOWS, MAX_BUFFER_IMAGES

class AlertManager:
    def __init__(self, settings: Settings, detector):
        """
        Inicializa o gerenciador de alertas.
        
        Args:
            settings: Configurações da aplicação
            detector: Instância do ObjectDetector para desenhar as detecções
        """
        self.settings = settings
        self.detector = detector
        self.logger = logging.getLogger(__name__)
        self.total_alerts = 0
        
        # Criar diretório de alertas
        self.alerts_dir = Path("logs/alerts")
        self.alerts_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar fila de alertas
        self.alert_queue = asyncio.Queue()
        
        # Buffer de detecções por classe
        self.detection_buffer = {}  # {class_name: [{"timestamp": dt, "confidence": float, "image_path": str}]}
        
        # Flag para controle do worker
        self.is_running = True
        
        # Iniciar workers
        self.worker_task = asyncio.create_task(self._process_alert_queue())
        self.cleanup_task = asyncio.create_task(self._cleanup_buffer())

    def _get_confidence_level(self, confidence: float) -> str:
        """Determina o nível de confiança da detecção."""
        if confidence >= CONFIDENCE_LEVELS["HIGH"]:
            return "HIGH"
        elif confidence >= CONFIDENCE_LEVELS["MEDIUM"]:
            return "MEDIUM"
        return "LOW"

    async def _should_send_email(self, class_name: str) -> bool:
        """Verifica se deve enviar email baseado no buffer de detecções."""
        now = datetime.now()
        
        if class_name not in self.detection_buffer:
            return False
            
        # Pegar última detecção para determinar o nível
        last_detection = self.detection_buffer[class_name][-1]
        level = self._get_confidence_level(last_detection["confidence"])
        
        # Filtrar detecções dentro da janela de tempo
        window = DETECTION_WINDOWS[level]
        window_start = now - timedelta(seconds=window)
        
        recent_detections = [
            d for d in self.detection_buffer[class_name]
            if d["timestamp"] >= window_start
        ]
        
        # Verificar número de confirmações necessárias
        return len(recent_detections) >= REQUIRED_DETECTIONS[level]

    async def _cleanup_buffer(self):
        """Limpa detecções antigas do buffer periodicamente"""
        while self.is_running:
            try:
                now = datetime.now()
                max_window = max(DETECTION_WINDOWS.values())
                
                for class_name in list(self.detection_buffer.keys()):
                    cutoff = now - timedelta(seconds=max_window)
                    
                    # Remover detecções antigas
                    old_detections = [
                        d for d in self.detection_buffer[class_name]
                        if d["timestamp"] < cutoff
                    ]
                    
                    # Remover imagens antigas
                    for det in old_detections:
                        try:
                            if "image_path" in det:
                                Path(det["image_path"]).unlink(missing_ok=True)
                        except Exception as e:
                            self.logger.error(f"Erro ao remover imagem antiga: {str(e)}")
                    
                    # Atualizar buffer
                    self.detection_buffer[class_name] = [
                        d for d in self.detection_buffer[class_name]
                        if d["timestamp"] >= cutoff
                    ]
                    
            except Exception as e:
                self.logger.error(f"Erro na limpeza do buffer: {str(e)}")
                
            await asyncio.sleep(60)  # Limpa a cada minuto

    async def send_alert(self, image: np.ndarray, detections: List[Dict], video_time: int = 0):
        """Processa detecções e gerencia alertas."""
        timestamp = datetime.now()
        alert_id = f"alert_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Sempre salvar a imagem imediatamente
            image_path = self.alerts_dir / f"{alert_id}.jpg"
            image_with_detections = self.detector.draw_detections(image, detections)
            await asyncio.to_thread(cv2.imwrite, str(image_path), image_with_detections)
            
            # Salvar dados do alerta
            alert_data = {
                "timestamp": timestamp.isoformat(),
                "video_time": video_time,  # Tempo relativo do vídeo em ms
                "detections": detections,
                "image_path": str(image_path)
            }
            
            json_path = self.alerts_dir / f"{alert_id}.json"
            await self._save_json(json_path, alert_data)
            
            # Atualizar buffer de detecções
            for det in detections:
                class_name = det["class_name"]
                confidence = det["confidence"]
                
                if class_name not in self.detection_buffer:
                    self.detection_buffer[class_name] = []
                
                self.detection_buffer[class_name].append({
                    "timestamp": timestamp,
                    "confidence": confidence,
                    "image_path": str(image_path)
                })
                
                # Verificar se deve enviar email
                if await self._should_send_email(class_name):
                    await self.alert_queue.put({
                        "alert_id": alert_id,
                        "trigger_class": class_name,
                        "detections": detections,
                        "buffer": self.detection_buffer[class_name][-MAX_BUFFER_IMAGES:]
                    })
                    self.total_alerts += 1
            
        except Exception as e:
            self.logger.error(f"Erro ao processar alerta {alert_id}: {str(e)}")

    async def _process_alert_queue(self):
        """Processa a fila de alertas em background."""
        while self.is_running:
            try:
                # Aguardar próximo alerta
                try:
                    alert = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                try:
                    # Processar alerta
                    async with asyncio.timeout(10):
                        await self._send_email_alert(
                            alert["alert_id"],
                            alert["trigger_class"],
                            alert["detections"],
                            alert["buffer"]
                        )
                except asyncio.TimeoutError:
                    self.logger.error(f"Timeout ao enviar alerta {alert['alert_id']}")
                except Exception as e:
                    self.logger.error(f"Erro ao enviar alerta {alert['alert_id']}: {str(e)}")
                finally:
                    self.alert_queue.task_done()
                    
            except Exception as e:
                self.logger.error(f"Erro no processamento de alertas: {str(e)}")
                await asyncio.sleep(1)

    async def cleanup(self):
        """Limpa recursos e encerra os workers."""
        self.is_running = False
        
        try:
            if not self.alert_queue.empty():
                await self.alert_queue.join()
            
            if not self.worker_task.done():
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass
                    
            if not self.cleanup_task.done():
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {str(e)}")

    async def _save_json(self, path: Path, data: dict):
        """Salva dados JSON de forma assíncrona."""
        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(data, indent=2))

    async def _send_email_alert(self, alert_id: str, trigger_class: str, detections: List[Dict], buffer: List[Dict]):
        """Envia email de alerta com todas as imagens do buffer."""
        try:
            msg = MIMEMultipart()
            msg["Subject"] = f"VisionGuard - Alerta de Segurança {alert_id}"
            msg["From"] = self.settings.smtp_username
            msg["To"] = self.settings.alert_email
            
            body = self._create_alert_body(alert_id, trigger_class, detections, len(buffer))
            msg.attach(MIMEText(body, "html"))
            
            # Anexar todas as imagens do buffer
            for i, detection in enumerate(buffer):
                image_path = detection["image_path"]
                with open(image_path, "rb") as f:
                    img = MIMEImage(f.read())
                    img.add_header("Content-ID", f"<{alert_id}_{i}>")
                    msg.attach(img)
            
            server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)
            server.starttls()
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {str(e)}")
            raise

    def _create_alert_body(self, alert_id: str, trigger_class: str, detections: List[Dict], num_images: int) -> str:
        """
        Cria o corpo HTML do email de alerta.
        
        Args:
            alert_id: ID único do alerta
            trigger_class: Classe que disparou o alerta
            detections: Lista de detecções
            num_images: Número de imagens no buffer
            
        Returns:
            String HTML formatada
        """
        detection_list = "\n".join([
            f"<li>{det['class_name']} (Confiança: {det['confidence']:.2%})</li>"
            for det in detections
        ])
        
        # Criar galeria de imagens
        image_gallery = "\n".join([
            f'<img src="cid:{alert_id}_{i}" style="max-width: 100%; margin: 10px 0;">'
            for i in range(num_images)
        ])
        
        return f"""
        <html>
            <body>
                <h2>🚨 Alerta de Segurança - VisionGuard</h2>
                <p><strong>ID do Alerta:</strong> {alert_id}</p>
                <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                <p><strong>Classe Detectada:</strong> {trigger_class}</p>
                
                <h3>Objetos Detectados:</h3>
                <ul>
                    {detection_list}
                </ul>
                
                <h3>Sequência de Detecções:</h3>
                {image_gallery}
                
                <hr>
                <p><small>Este é um email automático. Por favor, não responda.</small></p>
            </body>
        </html>
        """