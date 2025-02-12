"""
Gerenciador de envio de emails assíncrono com worker dedicado.
"""

import os
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple
import cv2
import asyncio
import threading
from PyQt5.QtCore import QObject, QTimer, QMutex
from config.logging_config import get_logger
from config.app_config import ALERT_CONFIG

class EmailWorker:
    """Worker dedicado para envio de emails em background."""
    
    def __init__(self, smtp_config: Dict):
        """
        Inicializa o worker.
        
        Args:
            smtp_config: Configurações SMTP
        """
        self.logger = get_logger('email_worker')
        self.smtp_config = smtp_config
        self.queue = asyncio.Queue()
        self.running = True
        self._worker_thread = None
        
    def start(self):
        """Inicia o worker em uma thread separada."""
        self._worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self._worker_thread.start()
        
    def stop(self):
        """Para o worker."""
        self.running = False
        if self._worker_thread:
            self._worker_thread.join()
            
    def _run_worker(self):
        """Loop principal do worker."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self.running:
            try:
                # Processar emails da fila
                while not self.queue.empty():
                    email_data = loop.run_until_complete(self.queue.get())
                    self._send_email(email_data)
                    self.queue.task_done()
                    
                # Pequena pausa para não sobrecarregar a CPU
                loop.run_until_complete(asyncio.sleep(0.1))
                    
            except Exception as e:
                self.logger.error(f"Erro no worker de email: {str(e)}")
                
        loop.close()
        
    def _send_email(self, email_data: Dict):
        """
        Envia um email.
        
        Args:
            email_data: Dados do email a enviar
        """
        try:
            with smtplib.SMTP(self.smtp_config['server'],
                            self.smtp_config['port'],
                            timeout=10) as server:
                server.starttls()
                server.login(self.smtp_config['email'],
                           self.smtp_config['password'])
                server.send_message(email_data['message'])
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar email: {str(e)}")

class EmailSender(QObject):
    """Gerenciador de envio de emails assíncrono com worker dedicado."""
    
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
        super().__init__()
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
            
        # Inicializar worker
        self.worker = EmailWorker({
            'server': self.smtp_server,
            'port': self.smtp_port,
            'email': self.sender_email,
            'password': self.sender_password
        })
        self.worker.start()
            
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
        Envia um alerta por email de forma assíncrona.
        
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
            # Criar mensagem
            msg = self._create_message(
                recipient_email,
                detections,
                [frame] if frame is not None else [],
                [video_time] if frame is not None else []
            )
            
            # Adicionar à fila do worker
            await self.worker.queue.put({
                'message': msg
            })
            
            self.logger.info(f"Email adicionado à fila para {recipient_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao enviar alerta: {str(e)}")
            return False
            
    def _create_message(self,
                       recipient_email: str,
                       detections: List[Dict],
                       frames: List[cv2.Mat],
                       video_times: List[int]) -> MIMEMultipart:
        """
        Cria a mensagem de email.
        
        Args:
            recipient_email: Email do destinatário
            detections: Lista de detecções
            frames: Lista de frames das detecções
            video_times: Lista de tempos dos vídeos
            
        Returns:
            Mensagem MIME montada
        """
        try:
            msg = MIMEMultipart()
            msg['Subject'] = ALERT_CONFIG['alert_subject']
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Corpo do email
            body = self._create_alert_body(detections, video_times)
            msg.attach(MIMEText(body, 'html'))
            
            # Anexar imagens
            for i, frame in enumerate(frames):
                try:
                    # Processar imagem de forma segura
                    success, img_data = cv2.imencode('.jpg', frame)
                    if success:
                        image = MIMEImage(img_data.tobytes())
                        image.add_header('Content-ID', f'<detection_image_{i}>')
                        msg.attach(image)
                    else:
                        self.logger.warning(f"Falha ao codificar imagem {i} para email")
                except Exception as e:
                    self.logger.error(f"Erro ao processar imagem {i}: {str(e)}")
            
            return msg
            
        except Exception as e:
            self.logger.error(f"Erro ao criar mensagem: {str(e)}")
            raise

    def _create_alert_body(self, detections: List[Dict], video_times: List[int]) -> str:
        """
        Cria o corpo HTML do email de alerta.
        
        Args:
            detections: Lista de detecções
            video_times: Lista de tempos dos vídeos
            
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
                    <p><strong>Detecções agrupadas:</strong> {len(detections)}</p>
                    <p><strong>Imagens:</strong> {len(video_times)}</p>
                    <p><strong>Tempos de vídeo:</strong> {', '.join(f'{t/1000:.1f}s' for t in video_times)}</p>
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
                
            # Imagens
            html += """
                </ul>
                
                <div style="margin-top: 20px;">
                    <h3>Imagens das Detecções:</h3>
            """
            
            for i in range(len(video_times)):
                html += f"""
                    <div style="margin: 20px 0;">
                        <p><strong>Detecção {i+1}</strong> (Tempo: {video_times[i]/1000:.1f}s)</p>
                        <img src="cid:detection_image_{i}" style="max-width: 100%; border: 1px solid #ddd; border-radius: 4px;">
                    </div>
                """
            
            # Rodapé
            html += """
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
            # Criar uma mensagem de teste
            msg = MIMEText("Teste de conexão")
            msg['Subject'] = "Teste VisionGuard"
            msg['From'] = self.sender_email
            msg['To'] = self.sender_email
            
            # Tentar adicionar à fila do worker
            await self.worker.queue.put({
                'message': msg
            })
            
            return {
                'success': True,
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port,
                'sender_email': self.sender_email
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }