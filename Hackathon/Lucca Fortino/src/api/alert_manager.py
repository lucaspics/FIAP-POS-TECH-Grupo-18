import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import cv2
import numpy as np
from datetime import datetime
import logging
from pathlib import Path
from typing import List, Dict
import json
import aiofiles
import asyncio
from .config import Settings

class AlertManager:
    def __init__(self, settings: Settings):
        """
        Inicializa o gerenciador de alertas.
        
        Args:
            settings: Configurações da aplicação
        """
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.total_alerts = 0
        
        # Criar diretório de alertas
        self.alerts_dir = Path("logs/alerts")
        self.alerts_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar fila de alertas
        self.alert_queue = asyncio.Queue()
        
        # Flag para controle do worker
        self.is_running = True
        
        # Iniciar worker
        self.worker_task = asyncio.create_task(self._process_alert_queue())

    async def send_alert(self, image: np.ndarray, detections: List[Dict]):
        """Adiciona alerta à fila de processamento."""
        timestamp = datetime.now()
        alert_id = f"alert_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Salvar imagem e dados
            image_path = self.alerts_dir / f"{alert_id}.jpg"
            await asyncio.to_thread(cv2.imwrite, str(image_path), image)
            
            alert_data = {
                "timestamp": timestamp.isoformat(),
                "detections": detections,
                "image_path": str(image_path)
            }
            
            json_path = self.alerts_dir / f"{alert_id}.json"
            await self._save_json(json_path, alert_data)
            
            # Adicionar à fila
            await self.alert_queue.put({
                "alert_id": alert_id,
                "image_path": image_path,
                "detections": detections
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
                            alert["image_path"],
                            alert["detections"]
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
        """Limpa recursos e encerra o worker."""
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
            
        except Exception as e:
            self.logger.error(f"Erro na limpeza: {str(e)}")

    async def _save_json(self, path: Path, data: dict):
        """Salva dados JSON de forma assíncrona."""
        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(data, indent=2))

    async def _send_email_alert(self, alert_id: str, image_path: Path, detections: List[Dict]):
        """Envia email de alerta."""
        try:
            msg = MIMEMultipart()
            msg["Subject"] = f"VisionGuard - Alerta de Segurança {alert_id}"
            msg["From"] = self.settings.smtp_username
            msg["To"] = self.settings.alert_email
            
            body = self._create_alert_body(alert_id, detections)
            msg.attach(MIMEText(body, "html"))
            
            with open(image_path, "rb") as f:
                img = MIMEImage(f.read())
                img.add_header("Content-ID", f"<{alert_id}>")
                msg.attach(img)
            
            server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)
            server.starttls()
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {str(e)}")
            raise

    def _create_alert_body(self, alert_id: str, detections: List[Dict]) -> str:
        """
        Cria o corpo HTML do email de alerta.
        
        Args:
            alert_id: ID único do alerta
            detections: Lista de detecções
            
        Returns:
            String HTML formatada
        """
        detection_list = "\n".join([
            f"<li>{det['class_name']} (Confiança: {det['confidence']:.2%})</li>"
            for det in detections
        ])
        
        return f"""
        <html>
            <body>
                <h2>🚨 Alerta de Segurança - VisionGuard</h2>
                <p><strong>ID do Alerta:</strong> {alert_id}</p>
                <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
                
                <h3>Objetos Detectados:</h3>
                <ul>
                    {detection_list}
                </ul>
                
                <p>Imagem em anexo.</p>
                
                <hr>
                <p><small>Este é um email automático. Por favor, não responda.</small></p>
            </body>
        </html>
        """