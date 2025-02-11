import os
import json
import cv2
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import asyncio
from .detector import Detection, DetectionResult
from .email_sender import EmailSender
from config.app_config import ALERT_CONFIG

class AlertManager:
    """Gerenciador de alertas otimizado para processamento local."""
    
    def __init__(self, alert_dir: str, min_confidence: float = 0.25):
        """
        Inicializa o gerenciador de alertas.
        
        Args:
            alert_dir: Diretório para salvar os alertas
            min_confidence: Confiança mínima para gerar alertas
        """
        self.logger = logging.getLogger(__name__)
        self.alert_dir = Path(alert_dir)
        self.min_confidence = min_confidence
        self.total_alerts = 0
        self.last_alert_time = None
        self._setup_directories()
        
        # Inicializar email sender
        self.email_sender = EmailSender()
        if ALERT_CONFIG['enable_email_alerts']:
            self.logger.info("Sistema de alertas por email habilitado")
        
    def _setup_directories(self):
        """Configura os diretórios necessários."""
        try:
            self.alert_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Diretório de alertas configurado: {self.alert_dir}")
        except Exception as e:
            self.logger.error(f"Erro ao criar diretório de alertas: {str(e)}")
            raise

    async def process_detection(self, 
                              result: DetectionResult, 
                              frame: Optional[cv2.Mat] = None,
                              video_time: int = 0) -> bool:
        """
        Processa um resultado de detecção e gera alertas se necessário.
        
        Args:
            result: Resultado da detecção
            frame: Frame original (opcional)
            video_time: Tempo do vídeo em ms
            
        Returns:
            bool indicando se um alerta foi gerado
        """
        try:
            # Verificar se há detecções com confiança suficiente
            high_confidence_detections = [
                det for det in result.detections 
                if det.confidence >= self.min_confidence
            ]
            
            if not high_confidence_detections:
                return False

            # Gerar alerta
            alert_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            alert_data = {
                "timestamp": result.timestamp.isoformat(),
                "video_time": video_time,
                "detections": [det.to_dict() for det in high_confidence_detections]
            }
            
            # Salvar dados do alerta
            json_path = self.alert_dir / f"{alert_id}.json"
            with open(json_path, 'w') as f:
                json.dump(alert_data, f, indent=2)
            
            # Salvar imagem se disponível
            if frame is not None:
                image_path = self.alert_dir / f"{alert_id}.jpg"
                cv2.imwrite(str(image_path), frame)
            
            self.total_alerts += 1
            self.last_alert_time = datetime.now()
            
            # Enviar email se habilitado
            if ALERT_CONFIG['enable_email_alerts'] and ALERT_CONFIG['notification_email']:
                try:
                    # Criar lista de detecções para o email
                    detections = [det.to_dict() for det in high_confidence_detections]
                    
                    # Enviar email de forma assíncrona
                    asyncio.create_task(self._send_alert_email(
                        ALERT_CONFIG['notification_email'],
                        detections,
                        frame,
                        video_time
                    ))
                    
                except Exception as e:
                    self.logger.error(f"Erro ao enviar email de alerta: {str(e)}")
            
            self.logger.info(f"Alerta gerado: {alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao processar alerta: {str(e)}")
            return False

    async def _send_alert_email(self,
                              recipient_email: str,
                              detections: List[Dict],
                              frame: Optional[cv2.Mat],
                              video_time: int):
        """
        Envia email de alerta de forma assíncrona.
        
        Args:
            recipient_email: Email do destinatário
            detections: Lista de detecções
            frame: Frame da detecção
            video_time: Tempo do vídeo
        """
        try:
            success = self.email_sender.send_alert(
                recipient_email,
                detections,
                frame,
                video_time
            )
            
            if success:
                self.logger.info(f"Email de alerta enviado para {recipient_email}")
            else:
                self.logger.error("Falha ao enviar email de alerta")
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar email de alerta: {str(e)}")

    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """
        Retorna os alertas mais recentes.
        
        Args:
            limit: Número máximo de alertas a retornar
            
        Returns:
            Lista de alertas ordenados por data
        """
        try:
            # Listar arquivos JSON de alerta
            json_files = sorted(
                self.alert_dir.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:limit]
            
            alerts = []
            for json_file in json_files:
                try:
                    with open(json_file, 'r') as f:
                        alert_data = json.load(f)
                    
                    # Verificar se existe imagem correspondente
                    image_path = json_file.with_suffix('.jpg')
                    alert_data['has_image'] = image_path.exists()
                    alert_data['alert_id'] = json_file.stem
                    
                    alerts.append(alert_data)
                    
                except Exception as e:
                    self.logger.error(f"Erro ao ler alerta {json_file}: {str(e)}")
                    continue
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Erro ao listar alertas: {str(e)}")
            return []

    def get_alert_image(self, alert_id: str) -> Optional[str]:
        """
        Retorna o caminho da imagem de um alerta específico.
        
        Args:
            alert_id: ID do alerta
            
        Returns:
            Caminho da imagem ou None se não existir
        """
        image_path = self.alert_dir / f"{alert_id}.jpg"
        return str(image_path) if image_path.exists() else None

    def clear_alerts(self):
        """Limpa todos os alertas salvos."""
        try:
            # Remover arquivos JSON
            for json_file in self.alert_dir.glob("*.json"):
                try:
                    json_file.unlink()
                except Exception as e:
                    self.logger.error(f"Erro ao remover {json_file}: {str(e)}")
            
            # Remover imagens
            for image_file in self.alert_dir.glob("*.jpg"):
                try:
                    image_file.unlink()
                except Exception as e:
                    self.logger.error(f"Erro ao remover {image_file}: {str(e)}")
            
            self.total_alerts = 0
            self.last_alert_time = None
            self.logger.info("Alertas limpos com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar alertas: {str(e)}")

    def get_stats(self) -> Dict:
        """Retorna estatísticas do gerenciador de alertas."""
        return {
            "total_alerts": self.total_alerts,
            "last_alert": self.last_alert_time.isoformat() if self.last_alert_time else None,
            "alert_dir": str(self.alert_dir),
            "email_enabled": ALERT_CONFIG['enable_email_alerts'],
            "notification_email": ALERT_CONFIG['notification_email'] if ALERT_CONFIG['enable_email_alerts'] else None
        }