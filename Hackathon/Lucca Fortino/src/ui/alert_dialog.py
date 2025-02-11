"""
Dialog para exibição detalhada de alertas.
"""

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QWidget,
    QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QIcon
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import os
from config.logging_config import get_logger

logger = get_logger('alert_dialog')

class DetectionImageLabel(QLabel):
    """Label customizado para exibir imagem com detecções."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.detections = []
        self.setMinimumSize(600, 400)
        self.setStyleSheet("""
            QLabel {
                background-color: #2c2c2c;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
    def set_detections(self, detections: List[Dict]):
        """Define as detecções a serem desenhadas."""
        self.detections = detections
        self.update()
        
    def paintEvent(self, event):
        """Sobrescreve o evento de pintura para desenhar as detecções."""
        super().paintEvent(event)
        
        if not self.pixmap() or not self.detections:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Configurar fonte
        font = QFont("Arial", 10)
        font.setBold(True)
        painter.setFont(font)
        
        # Calcular escala
        scale_x = self.width() / self.pixmap().width()
        scale_y = self.height() / self.pixmap().height()
        scale = min(scale_x, scale_y)
        
        # Offset para centralizar
        offset_x = (self.width() - self.pixmap().width() * scale) / 2
        offset_y = (self.height() - self.pixmap().height() * scale) / 2
        
        for det in self.detections:
            bbox = det.get('bbox', [])
            if bbox:
                # Escalar coordenadas
                x1, y1, x2, y2 = bbox
                x1 = int(x1 * scale + offset_x)
                y1 = int(y1 * scale + offset_y)
                x2 = int(x2 * scale + offset_x)
                y2 = int(y2 * scale + offset_y)
                
                # Desenhar retângulo com borda brilhante
                pen = QPen(QColor(255, 50, 50))
                pen.setWidth(3)
                painter.setPen(pen)
                painter.drawRect(x1, y1, x2 - x1, y2 - y1)
                
                # Fundo do texto
                conf = det.get('confidence', 0) * 100
                text = f"{det.get('class_name', 'Desconhecido')} ({conf:.1f}%)"
                text_rect = painter.fontMetrics().boundingRect(text)
                text_rect.moveTop(y1 - text_rect.height() - 5)
                text_rect.moveLeft(x1)
                text_rect.adjust(-5, -2, 5, 2)
                
                painter.fillRect(text_rect, QColor(40, 40, 40, 180))
                
                # Texto com borda
                painter.setPen(QPen(QColor(0, 0, 0), 2))
                painter.drawText(x1, y1 - 8, text)
                painter.setPen(QPen(QColor(255, 50, 50)))
                painter.drawText(x1, y1 - 8, text)

class AlertDialog(QDialog):
    """Dialog para exibição detalhada de alertas."""
    
    def __init__(self, alert_data: Dict[str, Any], parent=None):
        """
        Inicializa o dialog de alerta.
        
        Args:
            alert_data: Dados do alerta
            parent: Widget pai opcional
        """
        super().__init__(parent)
        self.alert_data = alert_data
        self.init_ui()
        
    def init_ui(self):
        """Inicializa a interface do usuário."""
        try:
            # Configurar janela
            self.setWindowTitle("Detalhes do Alerta")
            self.setMinimumWidth(800)
            self.setMinimumHeight(600)
            
            # Layout principal
            layout = QVBoxLayout(self)
            layout.setSpacing(20)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # Cabeçalho com timestamp
            header = QFrame()
            header.setStyleSheet("""
                QFrame {
                    background-color: #2c2c2c;
                    border-radius: 8px;
                    padding: 15px;
                }
                QLabel {
                    color: white;
                }
            """)
            header_layout = QHBoxLayout(header)
            
            # Ícone de alerta
            icon_label = QLabel()
            icon_label.setPixmap(QIcon.fromTheme("dialog-warning").pixmap(32, 32))
            header_layout.addWidget(icon_label)
            
            # Timestamp
            timestamp = datetime.fromisoformat(self.alert_data.get('timestamp', ''))
            time_label = QLabel(f"Alerta detectado em {timestamp.strftime('%d/%m/%Y às %H:%M:%S')}")
            time_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            header_layout.addWidget(time_label)
            header_layout.addStretch()
            
            layout.addWidget(header)
            
            # Container principal
            main_container = QFrame()
            main_container.setStyleSheet("""
                QFrame {
                    background-color: #f5f5f5;
                    border-radius: 8px;
                }
            """)
            main_layout = QHBoxLayout(main_container)
            main_layout.setSpacing(20)
            
            # Imagem
            alert_id = self.alert_data.get('alert_id')
            if alert_id:
                image_path = str(Path(self.alert_data.get('image_path', '')))
                logger.info(f"Tentando carregar imagem: {image_path}")
                
                if os.path.exists(image_path):
                    logger.info("Arquivo de imagem existe")
                    
                    # Usar label customizado
                    image_label = DetectionImageLabel()
                    image_label.setAlignment(Qt.AlignCenter)
                    pixmap = QPixmap(image_path)
                    if not pixmap.isNull():
                        logger.info("Imagem carregada com sucesso")
                        scaled_pixmap = pixmap.scaled(
                            600, 400,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                        image_label.setPixmap(scaled_pixmap)
                        
                        # Definir detecções
                        if self.alert_data.get('detections'):
                            image_label.set_detections(self.alert_data['detections'])
                        
                        main_layout.addWidget(image_label)
                    else:
                        logger.error("Falha ao carregar pixmap da imagem")
                else:
                    logger.error(f"Arquivo de imagem não encontrado: {image_path}")
            
            # Painel de detalhes
            if self.alert_data.get('detections'):
                details_panel = QFrame()
                details_panel.setStyleSheet("""
                    QFrame {
                        background-color: #2c2c2c;
                        border-radius: 8px;
                        padding: 15px;
                        min-width: 250px;
                    }
                    QLabel {
                        color: white;
                        padding: 5px;
                    }
                """)
                details_layout = QVBoxLayout(details_panel)
                
                # Título do painel
                title = QLabel("Detecções")
                title.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
                details_layout.addWidget(title)
                
                # Lista de detecções
                for det in self.alert_data['detections']:
                    det_frame = QFrame()
                    det_frame.setStyleSheet("""
                        QFrame {
                            background-color: #3c3c3c;
                            border-radius: 5px;
                            margin: 5px;
                            padding: 10px;
                        }
                    """)
                    det_layout = QVBoxLayout(det_frame)
                    
                    # Classe e confiança
                    conf = det.get('confidence', 0) * 100
                    class_label = QLabel(f"🎯 {det.get('class_name', 'Desconhecido')}")
                    class_label.setStyleSheet("font-weight: bold; color: #ff3232;")
                    det_layout.addWidget(class_label)
                    
                    conf_label = QLabel(f"Confiança: {conf:.1f}%")
                    det_layout.addWidget(conf_label)
                    
                    # Bounding box
                    bbox = det.get('bbox', [])
                    if bbox:
                        pos_label = QLabel(
                            f"Posição: ({int(bbox[0])}, {int(bbox[1])}) - "
                            f"({int(bbox[2])}, {int(bbox[3])})"
                        )
                        pos_label.setStyleSheet("color: #aaa;")
                        det_layout.addWidget(pos_label)
                    
                    details_layout.addWidget(det_frame)
                
                details_layout.addStretch()
                main_layout.addWidget(details_panel)
            
            layout.addWidget(main_container)
            
            # Botão de fechar
            button_container = QFrame()
            button_container.setStyleSheet("""
                QPushButton {
                    background-color: #2c2c2c;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 20px;
                    font-weight: bold;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #404040;
                }
            """)
            button_layout = QHBoxLayout(button_container)
            close_button = QPushButton("Fechar")
            close_button.clicked.connect(self.accept)
            button_layout.addStretch()
            button_layout.addWidget(close_button)
            button_layout.addStretch()
            
            layout.addWidget(button_container)
            
            logger.info(f"Dialog inicializado com dados: {self.alert_data}")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar UI do dialog: {str(e)}")
            # Criar UI mínima em caso de erro
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Erro ao carregar detalhes do alerta"))
            close_button = QPushButton("Fechar")
            close_button.clicked.connect(self.accept)
            layout.addWidget(close_button)