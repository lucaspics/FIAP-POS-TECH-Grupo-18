"""
Utilitários para manipulação de alertas na interface gráfica.
"""

import os
import cv2
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, 
    QHBoxLayout, 
    QVBoxLayout,
    QLabel, 
    QListWidgetItem,
    QPushButton,
    QFrame
)
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtCore import Qt, pyqtSignal
from config.logging_config import get_logger
from config.app_config import LOG_DIRS, ALERT_CONFIG

logger = get_logger('alert_utils')

def create_error_item(error_message: str) -> Tuple[QListWidgetItem, QWidget]:
    """Cria um item de erro para a lista."""
    error_widget = QWidget()
    error_layout = QHBoxLayout(error_widget)
    error_layout.addWidget(QLabel(error_message))
    
    item = QListWidgetItem()
    item.setSizeHint(error_widget.sizeHint())
    
    return item, error_widget

class AlertWidget(QWidget):
    """Widget personalizado para exibir um alerta na interface."""
    
    # Sinais
    alert_clicked = pyqtSignal(str)  # Emitido quando o alerta é clicado
    delete_clicked = pyqtSignal(str)  # Emitido quando o botão deletar é clicado
    
    def __init__(self,
                 alert_id: str,
                 timestamp: datetime,
                 video_time: int,
                 image_path: Optional[str] = None,
                 detections: Optional[Dict] = None,
                 parent: Optional[QWidget] = None):
        """
        Inicializa o widget de alerta.
        
        Args:
            alert_id: ID único do alerta
            timestamp: Timestamp do alerta
            video_time: Tempo do vídeo em ms
            image_path: Caminho da imagem do alerta (opcional)
            detections: Detecções associadas ao alerta (opcional)
            parent: Widget pai (opcional)
        """
        super().__init__(parent)
        
        # Armazenar dados
        self.alert_id = alert_id
        self.timestamp = timestamp
        self.video_time = video_time
        self.image_path = image_path
        self.detections = detections or {}
        
        # Inicializar UI
        self._init_ui()
        
    def _init_ui(self):
        """Inicializa a interface do widget."""
        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        try:
            # Frame com borda
            frame = QFrame()
            frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
            frame.setLineWidth(1)
            frame_layout = QHBoxLayout(frame)
            
            # Container para thumbnail
            thumb_container = QWidget()
            thumb_container.setMinimumSize(120, 90)
            thumb_container.setMaximumSize(120, 90)
            thumb_layout = QVBoxLayout(thumb_container)
            thumb_layout.setContentsMargins(0, 0, 0, 0)
            
            # Thumbnail
            thumb_label = QLabel()
            thumb_label.setMinimumSize(120, 90)
            thumb_label.setAlignment(Qt.AlignCenter)
            
            # Tentar carregar a imagem
            if self.image_path and os.path.exists(self.image_path):
                logger.info(f"Tentando carregar: {self.image_path}")
                pixmap = QPixmap(self.image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        120, 90,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    thumb_label.setPixmap(scaled_pixmap)
                    logger.info("Thumbnail carregada")
                else:
                    thumb_label.setText("Erro")
            else:
                thumb_label.setText("Sem\nImagem")
            
            thumb_layout.addWidget(thumb_label)
            frame_layout.addWidget(thumb_container)
            
            # Informações
            info_layout = QVBoxLayout()
            
            # Timestamp e tempo do vídeo
            time_label = QLabel(
                f"<b>{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</b><br>"
                f"Tempo do vídeo: {self.video_time/1000:.1f}s"
            )
            info_layout.addWidget(time_label)
            
            # Detecções
            if self.detections:
                detections_text = []
                for det in self.detections:
                    conf = det.get('confidence', 0) * 100
                    detections_text.append(
                        f"{det.get('class_name', 'Desconhecido')}: {conf:.1f}%"
                    )
                det_label = QLabel("<br>".join(detections_text))
                det_label.setStyleSheet("color: #666;")
                info_layout.addWidget(det_label)
            
            frame_layout.addLayout(info_layout)
            
            # Botões
            button_layout = QVBoxLayout()
            
            # Botão de visualizar
            view_btn = QPushButton("👁 Ver")
            view_btn.setToolTip("Visualizar alerta")
            view_btn.clicked.connect(
                lambda: self.alert_clicked.emit(self.alert_id)
            )
            view_btn.setMinimumWidth(60)
            button_layout.addWidget(view_btn)
            
            # Botão de deletar
            delete_btn = QPushButton("🗑 Del")
            delete_btn.setToolTip("Deletar alerta")
            delete_btn.clicked.connect(
                lambda: self.delete_clicked.emit(self.alert_id)
            )
            delete_btn.setMinimumWidth(60)
            button_layout.addWidget(delete_btn)
            
            # Ajustar layout dos botões
            button_layout.setSpacing(5)
            button_layout.setContentsMargins(0, 0, 0, 0)
            
            frame_layout.addLayout(button_layout)
            layout.addWidget(frame)
            
            # Estilo
            self.setStyleSheet("""
                QFrame {
                    background-color: #f5f5f5;
                    border-radius: 5px;
                    padding: 8px;
                    border: 1px solid #ddd;
                }
                QPushButton {
                    padding: 5px;
                    border-radius: 3px;
                    background-color: #ffffff;
                    border: 1px solid #ddd;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QLabel {
                    color: #333;
                }
            """)
            
            # Definir tamanho mínimo para o widget
            self.setMinimumHeight(100)
            thumb_container.setStyleSheet("""
                background-color: #eee;
                border: 1px solid #ddd;
                border-radius: 3px;
            """)
            
        except Exception as e:
            logger.error(f"Erro ao inicializar UI do AlertWidget: {str(e)}")
            # Criar UI mínima em caso de erro
            layout = QHBoxLayout(self)
            layout.addWidget(QLabel("Erro ao carregar alerta"))

def create_alert_list_item(alert_data: Dict[str, Any]) -> Tuple[QListWidgetItem, AlertWidget]:
    """
    Cria um item de lista com widget de alerta.
    
    Args:
        alert_data: Dados do alerta
        
    Returns:
        Tupla (QListWidgetItem, AlertWidget)
    """
    try:
        # Verificar dados do alerta
        logger.info(f"Criando item de alerta com dados: {alert_data}")
        
        # Usar o ID do alerta do próprio alert_data
        alert_id = alert_data.get('alert_id')
        if not alert_id:
            logger.error("Alerta não possui ID")
            return create_error_item("Erro: Alerta sem ID")
            
        logger.info(f"Criando widget para alerta ID: {alert_id}")
        
        # Construir caminho da imagem
        image_path = str(Path(LOG_DIRS['alerts']) / 'images' / f"{alert_id}.jpg")
        logger.info(f"Caminho da imagem: {image_path}")
        
        try:
            # Criar widget
            widget = AlertWidget(
                alert_id=alert_id,
                timestamp=datetime.fromisoformat(alert_data.get('timestamp', '')),
                video_time=alert_data.get('video_time', 0),
                image_path=image_path if Path(image_path).exists() else None,
                detections=alert_data.get('detections', [])
            )
            
            # Criar item
            item = QListWidgetItem()
            item.setSizeHint(widget.sizeHint())
            
            # Armazenar dados para referência
            alert_data['alert_id'] = alert_id  # Garantir que o ID está nos dados
            item.setData(Qt.UserRole, alert_data)
            
            return item, widget
            
        except Exception as e:
            logger.error(f"Erro ao criar widget: {str(e)}")
            return create_error_item(f"Erro ao criar alerta: {str(e)}")
        
        # Criar item
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        
        # Armazenar dados para referência
        item.setData(Qt.UserRole, alert_data)
        
        return item, widget
        
    except Exception as e:
        logger.error(f"Erro ao criar item de alerta: {str(e)}")
        return create_error_item("Erro ao carregar alerta")

def save_alert_frame(frame: cv2.Mat, 
                    alert_id: str,
                    video_time: int) -> Optional[str]:
    """
    Salva um frame de alerta.
    
    Args:
        frame: Frame OpenCV para salvar
        alert_id: ID do alerta
        video_time: Tempo do vídeo em ms
        
    Returns:
        Caminho do arquivo salvo ou None em caso de erro
    """
    try:
        # Garantir que o diretório existe
        alert_dir = Path(LOG_DIRS['alerts']) / 'images'
        alert_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar nome do arquivo
        image_path = alert_dir / f"{alert_id}.jpg"
        
        # Salvar frame
        cv2.imwrite(str(image_path), frame)
        logger.info(f"Frame de alerta salvo em: {image_path}")
        
        return str(image_path)
        
    except Exception as e:
        logger.error(f"Erro ao salvar frame de alerta: {str(e)}")
        return None

def format_alert_time(video_time: int) -> str:
    """
    Formata o tempo do vídeo para exibição.
    
    Args:
        video_time: Tempo em milissegundos
        
    Returns:
        String formatada (HH:MM:SS.mmm)
    """
    try:
        total_seconds = video_time / 1000
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        milliseconds = int((total_seconds * 1000) % 1000)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
        
    except Exception as e:
        logger.error(f"Erro ao formatar tempo: {str(e)}")
        return "00:00:00.000"