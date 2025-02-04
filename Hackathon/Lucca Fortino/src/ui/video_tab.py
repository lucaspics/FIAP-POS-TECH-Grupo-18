import os
import cv2
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QListWidget, QTextEdit
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt
from config.logging_config import logger
from config.app_config import VIDEO_WIDTH, VIDEO_HEIGHT, OVERLAY_PATH
from utils.video_utils import frame_to_pixmap
from utils.alert_utils import AlertManager

class VideoTab(QWidget):
    """Aba principal com controles de vídeo e visualização."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface da aba de vídeo."""
        self.video_layout = QHBoxLayout()
        self.setLayout(self.video_layout)
        
        # Layout esquerdo (vídeo e controles)
        self.setup_left_panel()
        
        # Layout direito (logs)
        self.setup_right_panel()
        
    def setup_left_panel(self):
        """Configura o painel esquerdo com vídeo e controles."""
        self.left_layout = QVBoxLayout()
        self.video_layout.addLayout(self.left_layout)
        
        # Título
        self.video_title = QLabel("Monitoramento de Vídeo")
        self.video_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.left_layout.addWidget(self.video_title)
        
        # Área de vídeo
        self.setup_video_area()
        
        # Tempo
        self.time_label = QLabel("Tempo: 0s")
        self.left_layout.addWidget(self.time_label)
        
        # Botão de conexão
        self.connect_button = QPushButton("Conectar à Câmera")
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        self.connect_button.clicked.connect(self.parent.connect_camera if self.parent else None)
        self.left_layout.addWidget(self.connect_button)
        
        # Controles de reprodução
        self.setup_playback_controls()
        
        # Botão de alerta
        self.alert_button = QPushButton("Disparar Alerta")
        self.alert_button.setEnabled(False)
        self.alert_button.setStyleSheet("background-color: #e7e7e7; color: black; font-size: 14px;")
        self.alert_button.clicked.connect(self.parent.trigger_alert if self.parent else None)
        self.left_layout.addWidget(self.alert_button)
        
    def setup_video_area(self):
        """Configura a área de exibição do vídeo."""
        self.video_label = QLabel("Feed da câmera aparecerá aqui")
        self.video_label.setFixedSize(VIDEO_WIDTH, VIDEO_HEIGHT)
        self.video_label.setStyleSheet("background-color: black;")
        self.left_layout.addWidget(self.video_label)
        
        # Overlay
        self.overlay_label = QLabel(self.video_label)
        self.overlay_label.setFixedSize(VIDEO_WIDTH, VIDEO_HEIGHT)
        self.overlay_label.setAlignment(Qt.AlignCenter)
        self.overlay_label.setStyleSheet("background: transparent;")
        
        # Carregar overlay
        if os.path.exists(OVERLAY_PATH):
            self.overlay_pixmap = QPixmap(OVERLAY_PATH).scaled(
                VIDEO_WIDTH, VIDEO_HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.overlay_label.setPixmap(self.overlay_pixmap)
        else:
            logger.warning(f"Overlay não encontrado: {OVERLAY_PATH}")
            
    def setup_playback_controls(self):
        """Configura os controles de reprodução."""
        self.controls_layout = QHBoxLayout()
        
        # Play/Pause
        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.setEnabled(False)
        self.play_pause_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 14px;")
        self.play_pause_button.clicked.connect(self.parent.toggle_play_pause if self.parent else None)
        self.controls_layout.addWidget(self.play_pause_button)
        
        # Retroceder
        self.rewind_button = QPushButton("Retroceder 5s")
        self.rewind_button.setEnabled(False)
        self.rewind_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")
        self.rewind_button.clicked.connect(self.parent.rewind_video if self.parent else None)
        self.controls_layout.addWidget(self.rewind_button)
        
        # Avançar
        self.forward_button = QPushButton("Avançar 5s")
        self.forward_button.setEnabled(False)
        self.forward_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")
        self.forward_button.clicked.connect(self.parent.forward_video if self.parent else None)
        self.controls_layout.addWidget(self.forward_button)
        
        self.left_layout.addLayout(self.controls_layout)
        
    def setup_right_panel(self):
        """Configura o painel direito com logs."""
        self.right_layout = QVBoxLayout()
        self.video_layout.addLayout(self.right_layout)
        
        # Logs de análise
        self.logs_title = QLabel("Logs de Análise")
        self.logs_title.setFont(QFont("Arial", 12, QFont.Bold))
        self.right_layout.addWidget(self.logs_title)
        
        self.analysis_logs = QTextEdit()
        self.analysis_logs.setReadOnly(True)
        self.analysis_logs.setFixedWidth(300)
        self.analysis_logs.setFixedHeight(200)
        self.analysis_logs.setStyleSheet("background-color: #f0f0f0;")
        self.right_layout.addWidget(self.analysis_logs)
        
        # Lista de alertas
        self.alerts_title = QLabel("Alertas Detectados")
        self.alerts_title.setFont(QFont("Arial", 12, QFont.Bold))
        self.right_layout.addWidget(self.alerts_title)
        
        self.logs_list = QListWidget()
        self.logs_list.setFixedWidth(300)
        self.logs_list.itemClicked.connect(self.parent.jump_to_alert if self.parent else None)
        self.right_layout.addWidget(self.logs_list)
        
    def update_video_frame(self, frame):
        """Atualiza o frame de vídeo exibido."""
        if frame is not None:
            pixmap = frame_to_pixmap(frame)
            self.video_label.setPixmap(pixmap)
            self.overlay_label.raise_()
            
    def update_time(self, time_ms):
        """Atualiza o label de tempo."""
        self.time_label.setText(f"Tempo: {int(time_ms/1000)}s")
        
    def add_log(self, message):
        """Adiciona uma mensagem aos logs de análise."""
        self.analysis_logs.append(message)
        
    def add_alert(self, frame, time_ms):
        """Adiciona um novo alerta à lista."""
        alert_frame_path = AlertManager.save_alert_frame(frame, time_ms)
        list_item, widget = AlertManager.create_alert_widget(alert_frame_path, time_ms)
        self.logs_list.addItem(list_item)
        self.logs_list.setItemWidget(list_item, widget)
        
    def enable_controls(self, enabled=True):
        """Habilita ou desabilita os controles de vídeo."""
        self.play_pause_button.setEnabled(enabled)
        self.rewind_button.setEnabled(enabled)
        self.forward_button.setEnabled(enabled)
        self.alert_button.setEnabled(enabled)
        self.connect_button.setEnabled(not enabled)  # Inverso dos outros