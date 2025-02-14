"""
Utilitários para manipulação de alertas na interface gráfica.
"""

import os
import cv2
from datetime import datetime
from typing import Tuple, Optional, Dict, Any, List
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
from PyQt5.QtGui import QPixmap, QIcon, QColor, QPainter, QPen
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QSize, QRectF
from config.logging_config import get_logger
from config.app_config import LOG_DIRS, ALERT_CONFIG

logger = get_logger('alert_utils')

class ConfidenceIndicator(QWidget):
    """Widget para exibir indicador visual de confiança."""
    
    def __init__(self, confidence: float, parent: Optional[QWidget] = None):
        """
        Inicializa o indicador de confiança.
        
        Args:
            confidence: Valor de confiança (0-1)
            parent: Widget pai opcional
        """
        super().__init__(parent)
        self.confidence = confidence
        self.setMinimumSize(80, 20)
        self.setMaximumHeight(20)
        
        # Configurações do indicador
        self.num_segments = 10
        self.segment_spacing = 2
        self.segment_colors = self._generate_segment_colors()
    
    def _generate_segment_colors(self) -> List[QColor]:
        """Gera as cores para cada segmento."""
        colors = []
        for i in range(self.num_segments):
            if i < self.num_segments * 0.4:  # Primeiros 40% - Verde/Amarelo
                colors.append(QColor("#FFD700"))  # Amarelo
            elif i < self.num_segments * 0.7:  # 40-70% - Laranja
                colors.append(QColor("#FFA500"))  # Laranja
            else:  # Últimos 30% - Vermelho
                colors.append(QColor("#FF0000"))  # Vermelho
        return colors
    
    def paintEvent(self, event):
        """Desenha o indicador com segmentos."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calcular dimensões dos segmentos
        total_width = self.width() - (self.num_segments - 1) * self.segment_spacing
        segment_width = int(total_width / self.num_segments)
        segment_height = self.height()
        
        # Número de segmentos ativos baseado na confiança
        active_segments = int(round(self.confidence * self.num_segments))
        
        # Desenhar segmentos
        x = 0
        for i in range(self.num_segments):
            # Definir cor do segmento
            if i < active_segments:
                painter.setBrush(self.segment_colors[i])
                painter.setPen(Qt.NoPen)
            else:
                painter.setBrush(QColor("#f0f0f0"))
                painter.setPen(QPen(QColor("#d0d0d0"), 1))
            
            # Criar retângulo para o segmento
            rect = QRectF(
                float(x),
                0.0,
                float(segment_width),
                float(segment_height)
            )
            
            # Desenhar segmento
            painter.drawRoundedRect(rect, 2.0, 2.0)
            
            x += segment_width + self.segment_spacing

class ConfidenceWidget(QWidget):
    """Widget que combina label de porcentagem e indicador visual."""
    
    def __init__(self, confidence: float, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Label de porcentagem
        self.percent_label = QLabel(f"{confidence * 100:.1f}%")
        self.percent_label.setStyleSheet("color: #666; min-width: 45px;")
        layout.addWidget(self.percent_label)
        
        # Indicador visual
        self.indicator = ConfidenceIndicator(confidence)
        layout.addWidget(self.indicator)
        
        # Stretch para alinhar à esquerda
        layout.addStretch()

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
            
            # Detecções com indicadores visuais
            if self.detections:
                for det in self.detections:
                    det_container = QWidget()
                    det_layout = QHBoxLayout(det_container)
                    det_layout.setContentsMargins(0, 0, 0, 0)
                    det_layout.setSpacing(10)
                    
                    # Nome da classe
                    class_name = det.get('class_name', 'Desconhecido')
                    class_label = QLabel(f"{class_name}:")
                    class_label.setStyleSheet("color: #666;")
                    class_label.setMinimumWidth(80)
                    det_layout.addWidget(class_label)
                    
                    # Widget de confiança (porcentagem + indicador)
                    confidence = det.get('confidence', 0)
                    confidence_widget = ConfidenceWidget(confidence)
                    det_layout.addWidget(confidence_widget)
                    
                    info_layout.addWidget(det_container)
            
            frame_layout.addLayout(info_layout)
            layout.addWidget(frame)
            
            # Fazer o widget inteiro clicável
            self.setCursor(Qt.PointingHandCursor)
            
            # Conectar o clique do widget ao sinal
            frame.mousePressEvent = lambda e: self.alert_clicked.emit(self.alert_id)
            
            # Estilo
            self.setStyleSheet("""
                QFrame {
                    background-color: #f5f5f5;
                    border-radius: 5px;
                    padding: 8px;
                    border: 1px solid #ddd;
                    transition: background-color 0.2s;
                }
                QFrame:hover {
                    background-color: #e0e0e0;
                    border-color: #bbb;
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