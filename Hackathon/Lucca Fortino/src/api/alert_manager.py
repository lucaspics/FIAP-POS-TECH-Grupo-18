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

    async def send_alert(self, image: np.ndarray, detections: List[Dict]):
        """
        Envia alerta com detecções.
        
        Args:
            image: Imagem numpy array (BGR)
            detections: Lista de detecções
        """
        timestamp = datetime.now()
        alert_id = f"alert_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Criar tarefas assíncronas para salvar arquivos
            save_tasks = []
            
            # Tarefa para salvar imagem
            image_path = self.alerts_dir / f"{alert_id}.jpg"
            save_tasks.append(
                asyncio.to_thread(cv2.imwrite, str(image_path), image)
            )
            
            # Tarefa para salvar JSON
            alert_data = {
                "timestamp": timestamp.isoformat(),
                "detections": detections,
                "image_path": str(image_path)
            }
            json_path = self.alerts_dir / f"{alert_id}.json"
            save_tasks.append(
                self._save_json(json_path, alert_data)
            )
            
            # Executar salvamentos em paralelo
            await asyncio.gather(*save_tasks)
            
            # Iniciar envio de email em background com timeout
            email_task = asyncio.create_task(
                self._send_email_alert(alert_id, image_path, detections)
            )
            
            # Definir timeout para o email (10 segundos)
            try:
                await asyncio.wait_for(email_task, timeout=10.0)
                self.logger.info(f"Email enviado com sucesso para alerta {alert_id}")
            except asyncio.TimeoutError:
                self.logger.warning(f"Timeout no envio do email para alerta {alert_id}")
            except Exception as email_err:
                self.logger.error(f"Erro no envio do email para alerta {alert_id}: {str(email_err)}")
            
            self.total_alerts += 1
            self.logger.info(f"Alerta {alert_id} registrado com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao processar alerta {alert_id}: {str(e)}")
            # Não propagar o erro para não impactar o fluxo principal

    async def _save_json(self, path: Path, data: dict):
        """Salva dados JSON de forma assíncrona."""
        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(data, indent=2))

    async def _send_email_alert(self, alert_id: str, image_path: Path, detections: List[Dict]):
        """
        Envia email de alerta.
        
        Args:
            alert_id: ID único do alerta
            image_path: Caminho para a imagem do alerta
            detections: Lista de detecções
        """
        try:
            msg = MIMEMultipart()
            msg["Subject"] = f"VisionGuard - Alerta de Segurança {alert_id}"
            msg["From"] = self.settings.smtp_username
            msg["To"] = self.settings.alert_email
            
            # Corpo do email
            body = self._create_alert_body(alert_id, detections)
            msg.attach(MIMEText(body, "html"))
            
            # Anexar imagem
            with open(image_path, "rb") as f:
                img = MIMEImage(f.read())
                img.add_header("Content-ID", f"<{alert_id}>")
                msg.attach(img)
            
            # Conectar ao servidor SMTP
            server = smtplib.SMTP(self.settings.smtp_server, self.settings.smtp_port)
            server.starttls()
            server.login(self.settings.smtp_username, self.settings.smtp_password)
            
            # Enviar email
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email de alerta: {str(e)}")
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