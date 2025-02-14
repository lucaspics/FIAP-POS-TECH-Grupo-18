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
    QGridLayout,
    QScrollArea,
    QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path
import os
from config.logging_config import get_logger
from core.alert_utils import ConfidenceWidget

logger = get_logger('alert_dialog')

class DetectionImageLabel(QLabel):
    """Label customizado para exibir imagem com detecções."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 400)
        self.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)

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
            layout.setSpacing(24)
            layout.setContentsMargins(24, 24, 24, 24)
            
            # Cabeçalho com timestamp
            header = QFrame()
            header.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 16px;
                }
                QLabel {
                    color: #333333;
                }
            """)
            header_layout = QHBoxLayout(header)
            header_layout.setSpacing(16)
            
            # Ícone de alerta
            icon_label = QLabel()
            icon_label.setPixmap(QIcon.fromTheme("dialog-warning").pixmap(32, 32))
            header_layout.addWidget(icon_label)
            
            # Timestamp
            timestamp = datetime.fromisoformat(self.alert_data.get('timestamp', ''))
            time_label = QLabel(f"Alerta detectado em {timestamp.strftime('%d/%m/%Y às %H:%M:%S')}")
            time_label.setStyleSheet("""
                font-family: 'Segoe UI';
                font-size: 18px;
                font-weight: 600;
                color: #1a1a1a;
            """)
            header_layout.addWidget(time_label)
            header_layout.addStretch()
            
            layout.addWidget(header)
            
            # Container principal
            main_container = QFrame()
            main_container.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                }
            """)
            main_layout = QHBoxLayout(main_container)
            main_layout.setSpacing(24)
            main_layout.setContentsMargins(16, 16, 16, 16)
            
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
                        main_layout.addWidget(image_label)
                    else:
                        logger.error("Falha ao carregar pixmap da imagem")
                else:
                    logger.error(f"Arquivo de imagem não encontrado: {image_path}")
            
            # Painel de detalhes com scroll
            if self.alert_data.get('detections'):
                # Container para o conteúdo
                details_panel = QFrame()
                details_panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                details_panel.setStyleSheet("""
                    QFrame {
                        background-color: #f8f9fa;
                        border: 1px solid #e0e0e0;
                        border-radius: 8px;
                        padding: 12px;
                    }
                    QLabel {
                        color: #333333;
                        padding: 4px;
                    }
                """)
                details_layout = QVBoxLayout(details_panel)
                details_layout.setSpacing(12)
                details_layout.setContentsMargins(8, 8, 8, 8)
                
                # Título do painel
                title = QLabel("Detecções")
                title.setStyleSheet("""
                    font-family: 'Segoe UI';
                    font-size: 16px;
                    font-weight: 600;
                    color: #1a1a1a;
                """)
                details_layout.addWidget(title)
                
                # Lista de detecções
                for det in self.alert_data['detections']:
                    det_frame = QFrame()
                    det_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                    det_frame.setStyleSheet("""
                        QFrame {
                            background-color: white;
                            border: 1px solid #e0e0e0;
                            border-radius: 6px;
                            padding: 8px;
                        }
                    """)
                    det_layout = QHBoxLayout(det_frame)
                    det_layout.setSpacing(8)
                    det_layout.setContentsMargins(8, 8, 8, 8)
                    
                    class_label = QLabel(f"🎯 {det.get('class_name', 'Desconhecido')}")
                    class_label.setStyleSheet("""
                        font-family: 'Segoe UI';
                        font-size: 14px;
                        font-weight: 600;
                        color: #FF3232;
                    """)
                    det_layout.addWidget(class_label)
                    
                    # Indicador de confiança
                    confidence = det.get('confidence', 0)
                    confidence_widget = ConfidenceWidget(confidence)
                    det_layout.addWidget(confidence_widget)
                    det_layout.addStretch()
                    
                    details_layout.addWidget(det_frame)
                
                details_layout.addStretch()
                main_layout.addWidget(details_panel)
            
            layout.addWidget(main_container)
            
            # Botão de fechar
            button_container = QFrame()
            button_container.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    color: #1a1a1a;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    padding: 8px 24px;
                    font-family: 'Segoe UI';
                    font-size: 14px;
                    font-weight: 500;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    border-color: #dee2e6;
                }
                QPushButton:pressed {
                    background-color: #dee2e6;
                }
            """)
            button_layout = QHBoxLayout(button_container)
            close_button = QPushButton("Fechar")
            close_button.clicked.connect(self.accept)
            button_layout.addStretch()
            button_layout.addWidget(close_button)
            button_layout.addStretch()
            
            layout.addWidget(button_container)
            
            # Estilo global do dialog
            self.setStyleSheet("""
                QDialog {
                    background-color: #f8f9fa;
                }
            """)
            
            logger.info(f"Dialog inicializado com dados: {self.alert_data}")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar UI do dialog: {str(e)}")
            # Criar UI mínima em caso de erro
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Erro ao carregar detalhes do alerta"))
            close_button = QPushButton("Fechar")
            close_button.clicked.connect(self.accept)
            layout.addWidget(close_button)