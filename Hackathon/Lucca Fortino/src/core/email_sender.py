"""
Gerenciador de envio de emails assíncrono.
"""

import os
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import cv2
import asyncio
from config.logging_config import get_logger
from config.app_config import ALERT_CONFIG

class EmailSender:
    """Gerenciador de envio de emails assíncrono."""
    
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
        self.logger = get_logger('email_sender')
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
        # Tentar carregar credenciais do ambiente
        self.sender_email = sender_email or os.getenv('SMTP_EMAIL')
        self.sender_password = sender_password or os.getenv('SMTP_PASSWORD')
        
        if not (self.sender_email and self.sender_password):
            self.logger.warning("Credenciais de email não configuradas")
        elif not self._validate_email(self.sender_email):
            self.logger.error(f"Email do remetente inválido: {self.sender_email}")
            self.sender_email = None
            
    def _validate_email(self, email: str) -> bool:
        """
        Valida um endereço de email.
        
        Args:
            email: Endereço de email a validar
            
        Returns:
            bool indicando se o email é válido
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    async def send_alert(self, 
                        recipient_email: str,
                        detections: List[Dict],
                        frame: Optional[cv2.Mat] = None,
                        video_time: int = 0) -> bool:
        """
        Envia um email de alerta de forma assíncrona.
        
        Args:
            recipient_email: Email do destinatário
            detections: Lista de detecções
            frame: Frame da detecção (opcional)
            video_time: Tempo do vídeo em ms
            
        Returns:
            bool indicando sucesso do envio
        """
        if not (self.sender_email and self.sender_password):
            self.logger.error("Credenciais de email não configuradas")
            return False
            
        if not self._validate_email(recipient_email):
            self.logger.error(f"Email do destinatário inválido: {recipient_email}")
            return False
            
        try:
            # Criar mensagem de forma assíncrona
            msg = await asyncio.to_thread(self._create_message,
                recipient_email,
                detections,
                frame,
                video_time
            )
            
            # Enviar email de forma assíncrona
            return await asyncio.to_thread(self._send_message, msg)
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {str(e)}")
            return False
            
    def _create_message(self,
                       recipient_email: str,
                       detections: List[Dict],
                       frame: Optional[cv2.Mat],
                       video_time: int) -> MIMEMultipart:
        """
        Cria a mensagem de email.
        
        Args:
            recipient_email: Email do destinatário
            detections: Lista de detecções
            frame: Frame da detecção
            video_time: Tempo do vídeo
            
        Returns:
            Mensagem MIME montada
        """
        try:
            msg = MIMEMultipart()
            msg['Subject'] = ALERT_CONFIG['alert_subject']
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Corpo do email
            body = self._create_alert_body(detections, video_time)
            msg.attach(MIMEText(body, 'html'))
            
            # Anexar imagem se disponível
            if frame is not None:
                try:
                    # Processar imagem de forma segura
                    success, img_data = cv2.imencode('.jpg', frame)
                    if success:
                        image = MIMEImage(img_data.tobytes())
                        image.add_header('Content-ID', '<detection_image>')
                        msg.attach(image)
                    else:
                        self.logger.warning("Falha ao codificar imagem para email")
                except Exception as e:
                    self.logger.error(f"Erro ao processar imagem: {str(e)}")
            
            return msg
            
        except Exception as e:
            self.logger.error(f"Erro ao criar mensagem: {str(e)}")
            raise

    def _send_message(self, msg: MIMEMultipart) -> bool:
        """
        Envia uma mensagem de email.
        
        Args:
            msg: Mensagem MIME para enviar
            
        Returns:
            bool indicando sucesso do envio
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            self.logger.info(f"Alerta enviado para {msg['To']}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            self.logger.error("Falha na autenticação SMTP")
            return False
        except smtplib.SMTPException as e:
            self.logger.error(f"Erro SMTP: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao enviar mensagem: {str(e)}")
            return False

    def _create_alert_body(self, detections: List[Dict], video_time: int) -> str:
        """
        Cria o corpo HTML do email de alerta.
        
        Args:
            detections: Lista de detecções
            video_time: Tempo do vídeo em ms
            
        Returns:
            String HTML do corpo do email
        """
        try:
            # Cabeçalho
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #f44336;">⚠️ {ALERT_CONFIG['alert_subject']}</h2>
                <p>{ALERT_CONFIG['alert_template'].format(
                    timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )}</p>
                
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
            
        except Exception as e:
            self.logger.error(f"Erro ao criar corpo do email: {str(e)}")
            return "Erro ao gerar conteúdo do email"

    async def test_connection(self) -> Dict:
        """
        Testa a conexão com o servidor SMTP de forma assíncrona.
        
        Returns:
            Dict com resultado do teste
        """
        if not (self.sender_email and self.sender_password):
            return {
                'success': False,
                'error': 'Credenciais não configuradas'
            }
            
        try:
            # Testar conexão de forma assíncrona
            result = await asyncio.to_thread(self._test_smtp_connection)
            return {
                'success': True,
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port,
                'sender_email': self.sender_email
            } if result else {
                'success': False,
                'error': 'Falha na conexão SMTP'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _test_smtp_connection(self) -> bool:
        """
        Testa a conexão SMTP.
        
        Returns:
            bool indicando sucesso da conexão
        """
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao testar conexão SMTP: {str(e)}")
            return False