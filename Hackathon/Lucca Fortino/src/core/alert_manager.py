"""
Gerenciador de alertas otimizado para processamento local.
"""

import os
import json
import cv2
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import asyncio
import shutil
from .detector import Detection, DetectionResult, ObjectDetector
from .email_sender import EmailSender
from config.app_config import ALERT_CONFIG, LOG_DIRS
from config.logging_config import get_logger

class AlertManager:
    """Gerenciador de alertas otimizado para processamento local."""
    
    def __init__(self, detector: ObjectDetector, min_confidence: float = 0.25, max_alerts: int = 1000):
        """
        Inicializa o gerenciador de alertas.
        
        Args:
            detector: Instância do detector de objetos
            min_confidence: Confiança mínima para gerar alertas
            max_alerts: Número máximo de alertas a manter
        """
        self.logger = get_logger('alert_manager')
        self.alert_dir = Path(LOG_DIRS['alerts'])
        self.detector = detector
        self.min_confidence = min_confidence
        self.max_alerts = max_alerts
        self.total_alerts = 0
        self.last_alert_time = None
        
        # Inicializar email sender
        self.email_sender = EmailSender()
        if ALERT_CONFIG['enable_email_alerts']:
            self.logger.info("Sistema de alertas por email habilitado")
        
        self._setup_directories()
        self._load_existing_alerts()
        
    def _setup_directories(self):
        """Configura os diretórios necessários."""
        try:
            # Garantir que o diretório base existe
            self.alert_dir.mkdir(parents=True, exist_ok=True)
            
            # Criar e verificar subdiretórios
            images_dir = self.alert_dir / 'images'
            data_dir = self.alert_dir / 'data'
            archive_dir = self.alert_dir / 'archive'
            
            for dir_path in [images_dir, data_dir, archive_dir]:
                dir_path.mkdir(exist_ok=True)
                if not dir_path.exists():
                    raise RuntimeError(f"Falha ao criar diretório: {dir_path}")
                self.logger.info(f"Diretório criado/verificado: {dir_path}")
            
            self.logger.info(f"Diretório de alertas configurado: {self.alert_dir}")
            self.logger.info(f"Diretório de imagens: {images_dir}")
        except Exception as e:
            self.logger.error(f"Erro ao criar diretório de alertas: {str(e)}")
            raise

    def _load_existing_alerts(self):
        """Carrega informações sobre alertas existentes."""
        try:
            data_dir = self.alert_dir / 'data'
            json_files = list(data_dir.glob("*.json"))
            self.total_alerts = len(json_files)
            
            if json_files:
                latest_file = max(json_files, key=lambda x: x.stat().st_mtime)
                self.last_alert_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
                
            self.logger.info(f"Carregados {self.total_alerts} alertas existentes")
            
            # Rotacionar alertas se necessário
            if self.total_alerts > self.max_alerts:
                self._rotate_alerts()
                
        except Exception as e:
            self.logger.error(f"Erro ao carregar alertas existentes: {str(e)}")
            self.total_alerts = 0
            self.last_alert_time = None

    def _rotate_alerts(self):
        """Move alertas antigos para o arquivo."""
        try:
            data_dir = self.alert_dir / 'data'
            json_files = sorted(
                data_dir.glob("*.json"),
                key=lambda x: x.stat().st_mtime
            )
            
            # Manter apenas os max_alerts mais recentes
            files_to_archive = json_files[:-self.max_alerts]
            
            for json_file in files_to_archive:
                try:
                    # Mover arquivo JSON
                    archive_json = self.alert_dir / 'archive' / json_file.name
                    shutil.move(str(json_file), str(archive_json))
                    
                    # Mover imagem correspondente
                    image_file = (self.alert_dir / 'images' / json_file.stem).with_suffix('.jpg')
                    if image_file.exists():
                        archive_image = (self.alert_dir / 'archive' / image_file.name)
                        shutil.move(str(image_file), str(archive_image))
                        
                except Exception as e:
                    self.logger.error(f"Erro ao arquivar alerta {json_file.name}: {str(e)}")
                    
            self.total_alerts = len(list(data_dir.glob("*.json")))
            self.logger.info(f"Arquivados {len(files_to_archive)} alertas antigos")
            
        except Exception as e:
            self.logger.error(f"Erro ao rotacionar alertas: {str(e)}")

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

            # Verificar intervalo mínimo entre alertas (ignorar para o último frame)
            if not getattr(result, 'is_last_frame', False):  # Adicionar verificação de último frame
                if (self.last_alert_time and
                    (datetime.now() - self.last_alert_time).total_seconds() * 1000 <
                    ALERT_CONFIG['min_time_between_alerts']):
                    return False

            # Gerar alerta
            alert_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            alert_data = {
                "alert_id": alert_id,
                "timestamp": result.timestamp.isoformat(),
                "video_time": video_time,
                "detections": [det.to_dict() for det in high_confidence_detections],
                "confidence_threshold": self.min_confidence,
                "alert_triggered": 1,
                "analysis_time": 0.0,
                "frame_number": 0
            }
            
            # Salvar dados do alerta
            json_path = self.alert_dir / 'data' / f"{alert_id}.json"
            self.logger.info(f"Dados do alerta antes de salvar: {alert_data}")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(alert_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Dados do alerta salvos em: {json_path}")
            
            # Verificar se os dados foram salvos corretamente
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                self.logger.info(f"Dados lidos do arquivo: {saved_data}")
            # Salvar imagem se disponível
            if frame is not None and ALERT_CONFIG['save_frames']:
                try:
                    # Verificar frame
                    if frame.size == 0:
                        self.logger.error("Frame está vazio")
                        return False
                    
                    self.logger.info(f"Frame shape: {frame.shape}, dtype: {frame.dtype}")
                    
                    # Criar diretório se não existir
                    images_dir = self.alert_dir / 'images'
                    images_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Desenhar detecções no frame
                    frame_with_detections = self.detector.draw_detections(frame, high_confidence_detections)
                    
                    # Salvar imagem
                    image_path = images_dir / f"{alert_id}.jpg"
                    self.logger.info(f"Tentando salvar imagem em: {image_path}")
                    success = cv2.imwrite(str(image_path), frame_with_detections)
                    
                    if success:
                        image_path_abs = str(image_path.absolute())
                        alert_data['has_image'] = True
                        alert_data['image_path'] = image_path_abs
                        self.logger.info(f"Imagem salva com sucesso: {image_path_abs}")
                        
                        # Verificar se o arquivo foi realmente criado
                        if not image_path.exists():
                            self.logger.error("Arquivo não foi criado mesmo com sucesso=True")
                            return False
                            
                        # Atualizar o JSON com o caminho da imagem
                        json_path = self.alert_dir / 'data' / f"{alert_id}.json"
                        if json_path.exists():
                            self.logger.info("Atualizando JSON com caminho da imagem")
                            with open(json_path, 'r', encoding='utf-8') as f:
                                json_data = json.load(f)
                            json_data['has_image'] = True
                            json_data['image_path'] = image_path_abs
                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(json_data, f, indent=2, ensure_ascii=False)
                            self.logger.info("JSON atualizado com sucesso")
                    else:
                        self.logger.error("Falha ao salvar imagem do alerta")
                        return False
                except Exception as e:
                    self.logger.error(f"Erro ao salvar imagem do alerta: {str(e)}")
                    return False
            
            self.total_alerts += 1
            self.last_alert_time = datetime.now()
            
            # Rotacionar alertas se necessário
            if self.total_alerts > self.max_alerts:
                await asyncio.to_thread(self._rotate_alerts)
            
            # Enviar email se habilitado
            if ALERT_CONFIG['enable_email_alerts'] and ALERT_CONFIG['notification_email']:
                try:
                    # Usar o mesmo frame com detecções para o email
                    asyncio.create_task(self._send_alert_email(
                        ALERT_CONFIG['notification_email'],
                        high_confidence_detections,
                        frame_with_detections if frame is not None else None,
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
                              detections: List[Detection],
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
            success = await self.email_sender.send_alert(
                recipient_email,
                [det.to_dict() for det in detections],
                frame,
                video_time
            )
            
            if success:
                self.logger.info(f"Email de alerta enviado para {recipient_email}")
            else:
                self.logger.error("Falha ao enviar email de alerta")
                
        except Exception as e:
            self.logger.error(f"Erro ao enviar email de alerta: {str(e)}")

    def get_recent_alerts(self, limit: int = 10, include_archived: bool = False) -> List[Dict]:
        """
        Retorna os alertas mais recentes.
        
        Args:
            limit: Número máximo de alertas a retornar
            include_archived: Se deve incluir alertas arquivados
            
        Returns:
            Lista de alertas ordenados por data
        """
        try:
            data_dir = self.alert_dir / 'data'
            json_files = list(data_dir.glob("*.json"))
            
            if include_archived:
                archive_dir = self.alert_dir / 'archive'
                json_files.extend(archive_dir.glob("*.json"))
            
            # Ordenar por data de modificação
            json_files = sorted(
                json_files,
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:limit]
            
            alerts = []
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        alert_data = json.load(f)
                    
                    # Verificar se existe imagem correspondente
                    image_path = (self.alert_dir / 'images' / json_file.stem).with_suffix('.jpg')
                    archive_path = (self.alert_dir / 'archive' / json_file.stem).with_suffix('.jpg')
                    
                    self.logger.info(f"Verificando imagem para alerta {json_file.stem}")
                    self.logger.info(f"Procurando em: {image_path}")
                    
                    # Se o caminho da imagem já existe nos dados do alerta, usar ele
                    if 'image_path' in alert_data and Path(alert_data['image_path']).exists():
                        self.logger.info(f"Usando caminho de imagem existente: {alert_data['image_path']}")
                        alert_data['has_image'] = True
                    # Senão, procurar a imagem
                    elif image_path.exists():
                        self.logger.info(f"Imagem encontrada em: {image_path}")
                        alert_data['has_image'] = True
                        alert_data['image_path'] = str(image_path.absolute())
                    elif archive_path.exists():
                        self.logger.info(f"Imagem encontrada no arquivo: {archive_path}")
                        alert_data['has_image'] = True
                        alert_data['image_path'] = str(archive_path.absolute())
                    else:
                        self.logger.warning(f"Nenhuma imagem encontrada para o alerta {json_file.stem}")
                        alert_data['has_image'] = False
                    
                    self.logger.info(f"Dados do alerta: {alert_data}")
                    alert_data['is_archived'] = 'archive' in str(json_file)
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
        # Verificar na pasta de imagens atual
        image_path = self.alert_dir / 'images' / f"{alert_id}.jpg"
        if image_path.exists():
            return str(image_path)
            
        # Verificar no arquivo
        archive_path = self.alert_dir / 'archive' / f"{alert_id}.jpg"
        return str(archive_path) if archive_path.exists() else None

    def clear_alerts(self, include_archived: bool = False):
        """
        Limpa alertas salvos.
        
        Args:
            include_archived: Se deve limpar também os alertas arquivados
        """
        try:
            # Limpar pasta de dados
            data_dir = self.alert_dir / 'data'
            for file in data_dir.glob("*.*"):
                try:
                    file.unlink()
                except Exception as e:
                    self.logger.error(f"Erro ao remover {file}: {str(e)}")
            
            # Limpar pasta de imagens
            images_dir = self.alert_dir / 'images'
            for file in images_dir.glob("*.*"):
                try:
                    file.unlink()
                except Exception as e:
                    self.logger.error(f"Erro ao remover {file}: {str(e)}")
            
            # Limpar arquivo se solicitado
            if include_archived:
                archive_dir = self.alert_dir / 'archive'
                for file in archive_dir.glob("*.*"):
                    try:
                        file.unlink()
                    except Exception as e:
                        self.logger.error(f"Erro ao remover {file}: {str(e)}")
            
            self.total_alerts = 0
            self.last_alert_time = None
            self.logger.info("Alertas limpos com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar alertas: {str(e)}")

    def get_stats(self) -> Dict:
        """Retorna estatísticas do gerenciador de alertas."""
        try:
            data_dir = self.alert_dir / 'data'
            archive_dir = self.alert_dir / 'archive'
            
            current_alerts = len(list(data_dir.glob("*.json")))
            archived_alerts = len(list(archive_dir.glob("*.json")))
            
            disk_usage = sum(
                f.stat().st_size for f in self.alert_dir.rglob("*.*")
            ) / (1024 * 1024)  # MB
            
            return {
                "total_alerts": self.total_alerts,
                "current_alerts": current_alerts,
                "archived_alerts": archived_alerts,
                "last_alert": self.last_alert_time.isoformat() if self.last_alert_time else None,
                "alert_dir": str(self.alert_dir),
                "disk_usage_mb": round(disk_usage, 2),
                "email_enabled": ALERT_CONFIG['enable_email_alerts'],
                "notification_email": ALERT_CONFIG['notification_email'] if ALERT_CONFIG['enable_email_alerts'] else None,
                "min_confidence": self.min_confidence,
                "max_alerts": self.max_alerts
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return {
                "error": str(e)
            }