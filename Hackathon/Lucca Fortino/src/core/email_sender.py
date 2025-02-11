import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
import logging
from pathlib import Path
from typing import Optional, List
import cv2

logger = logging.getLogger(__name__)

class EmailSender:
    """Gerenciador de envio de emails."""
    
    def __init__(self, 
                 smtp_server: str = "smtp.gmail.com",
                 smtp_port: int = 587,
                 sender_email: Optional[str] = None,
                 sender_password: Optional[str] = None):
        """
        Inicializa o gerenciador de emails.
        
        Args:
            smtp_server: Servidor SMTP
            smtp_port: Porta SMTP
            sender_email: Email do remetente (opcional)
            sender_password: Senha do app do remetente (opcional)
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
        # Tentar carregar credenciais do ambiente
        self.sender_email = sender_email or os.getenv('SMTP_EMAIL')
        self.sender_password = sender_password or os.getenv('SMTP_PASSWORD')
        
        if not (self.sender_email and self.sender_password):
            logger.warning("Credenciais de email não configuradas")
            
    def send_alert(self, 
                   recipient_email: str,
                   detections: List[dict],
                   frame: Optional[cv2.Mat] = None,
                   video_time: int = 0) -> bool:
        """
        Envia um email de alerta.
        
        Args:
            recipient_email: Email do destinatário
            detections: Lista de detecções
            frame: Frame da detecção (opcional)
            video_time: Tempo do vídeo em ms
            
        Returns:
            bool indicando sucesso do envio
        """
        if not (self.sender_email and self.sender_password):
            logger.error("Credenciais de email não configuradas")
            return False
            
        try:
            # Criar mensagem
            msg = MIMEMultipart()
            msg['Subject'] = f'VisionGuard - Alerta de Detecção ({datetime.now().strftime("%H:%M:%S")})'
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Corpo do email
            body = self._create_alert_body(detections, video_time)
            msg.attach(MIMEText(body, 'html'))
            
            # Anexar imagem se disponível
            if frame is not None:
                img_data = cv2.imencode('.jpg', frame)[1].tobytes()
                image = MIMEImage(img_data)
                image.add_header('Content-ID', '<detection_image>')
                msg.attach(image)
            
            # Enviar email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            logger.info(f"Alerta enviado para {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {str(e)}")
            return False
            
    def _create_alert_body(self, detections: List[dict], video_time: int) -> str:
        """
        Cria o corpo HTML do email de alerta.
        
        Args:
            detections: Lista de detecções
            video_time: Tempo do vídeo em ms
            
        Returns:
            String HTML do corpo do email
        """
        # Cabeçalho
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #f44336;">⚠️ Alerta de Detecção</h2>
            <p>O sistema VisionGuard detectou objetos cortantes:</p>
            
            <div style="margin: 20px 0; padding: 10px; background-color: #f5f5f5; border-radius: 5px;">
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Tempo do vídeo:</strong> {video_time/1000:.1f}s</p>
            </div>
            
            <h3>Detecções:</h3>
            <ul>
        """
        
        # Lista de detecções
        for det in detections:
            confidence = det.get('confidence', 0) * 100
            html += f"""
                <li style="margin-bottom: 10px;">
                    <strong>{det.get('class_name', 'Desconhecido')}</strong>
                    <div style="
                        width: 200px;
                        height: 20px;
                        background-color: #eee;
                        border-radius: 10px;
                        overflow: hidden;
                        margin: 5px 0;
                    ">
                        <div style="
                            width: {confidence}%;
                            height: 100%;
                            background-color: {'#4CAF50' if confidence > 70 else '#FFC107' if confidence > 50 else '#f44336'};
                        "></div>
                    </div>
                    <span style="color: #666;">Confiança: {confidence:.1f}%</span>
                </li>
            """
            
        # Rodapé
        html += """
            </ul>
            
            <div style="margin-top: 20px;">
                <p>Imagem da detecção em anexo (se disponível).</p>
            </div>
            
            <hr style="margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">
                Este é um email automático do sistema VisionGuard.
                Por favor, não responda este email.
            </p>
        </body>
        </html>
        """
        
        return html
        
    def test_connection(self) -> bool:
        """
        Testa a conexão com o servidor SMTP.
        
        Returns:
            bool indicando sucesso da conexão
        """
        if not (self.sender_email and self.sender_password):
            return False
            
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
            return True
        except Exception as e:
            logger.error(f"Erro ao testar conexão SMTP: {str(e)}")
            return False