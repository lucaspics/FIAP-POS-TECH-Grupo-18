"""
Aba de visualização e controle de vídeo.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QFrame,
    QProgressBar,
    QSpacerItem,
    QSizePolicy
)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, pyqtSignal
from datetime import datetime
from config.logging_config import get_logger
from config.app_config import VIDEO_CONFIG, UI_CONFIG
from core.video_utils import frame_to_pixmap

logger = get_logger('video_tab')

class CompactProgressBar(QProgressBar):
    """Barra de progresso customizada mais compacta."""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(4)
        self.setTextVisible(False)
        self.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #f0f0f0;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)

class VideoTab(QWidget):
    """Aba principal com controles de vídeo e visualização."""
    
    # Sinais
    connect_clicked = pyqtSignal()
    disconnect_clicked = pyqtSignal()
    play_pause_clicked = pyqtSignal()
    rewind_clicked = pyqtSignal()
    forward_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        """Inicializa a aba de vídeo."""
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface da aba de vídeo."""
        try:
            # Layout principal
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
            
            # Título
            title = QLabel(UI_CONFIG['window_title'])
            title.setFont(QFont("Arial", 16, QFont.Bold))
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            
            # Área de vídeo
            self.setup_video_area(layout)
            
            # Controles
            self.setup_controls(layout)
            
            # Logs
            self.setup_logs(layout)
            
            # Estado inicial
            self.is_playing = False
            self.enable_controls(False)
            
            logger.info("Interface da aba de vídeo inicializada")
            
        except Exception as e:
            logger.error(f"Erro ao configurar interface: {str(e)}")
            self.show_error_ui()
    
    def setup_video_area(self, layout):
        """Configura a área de exibição do vídeo."""
        try:
            # Container do vídeo
            video_frame = QFrame()
            video_frame.setFrameStyle(QFrame.StyledPanel)
            video_frame.setStyleSheet("""
                QFrame {
                    background-color: black;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                }
            """)
            
            video_layout = QVBoxLayout(video_frame)
            video_layout.setContentsMargins(0, 0, 0, 0)
            
            # Label do vídeo
            self.video_label = QLabel()
            self.video_label.setFixedSize(VIDEO_CONFIG['width'], VIDEO_CONFIG['height'])
            self.video_label.setAlignment(Qt.AlignCenter)
            self.video_label.setStyleSheet("color: white;")
            self.video_label.setText("Aguardando fonte de vídeo...")
            video_layout.addWidget(self.video_label, alignment=Qt.AlignCenter)
            
            # Overlay
            self.overlay_label = QLabel(self.video_label)
            self.overlay_label.setFixedSize(VIDEO_CONFIG['width'], VIDEO_CONFIG['height'])
            self.overlay_label.setAlignment(Qt.AlignCenter)
            self.overlay_label.setStyleSheet("background: transparent;")
            
            # Carregar overlay se existir
            if VIDEO_CONFIG.get('overlay_path'):
                try:
                    overlay = QPixmap(VIDEO_CONFIG['overlay_path'])
                    if not overlay.isNull():
                        self.overlay_label.setPixmap(
                            overlay.scaled(
                                VIDEO_CONFIG['width'],
                                VIDEO_CONFIG['height'],
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation
                            )
                        )
                except Exception as e:
                    logger.error(f"Erro ao carregar overlay: {str(e)}")
            
            layout.addWidget(video_frame)
            
            # Barra de progresso
            self.progress_bar = CompactProgressBar()
            layout.addWidget(self.progress_bar)
            
            # Tempo
            self.time_label = QLabel("00:00:00")
            self.time_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(self.time_label)
            
        except Exception as e:
            logger.error(f"Erro ao configurar área de vídeo: {str(e)}")
            raise
    
    def setup_controls(self, layout):
        """Configura os controles de reprodução."""
        try:
            controls = QWidget()
            controls_layout = QHBoxLayout(controls)
            controls_layout.setContentsMargins(0, 0, 0, 0)
            
            # Botão de conexão
            self.connect_button = QPushButton("Conectar")
            self.connect_button.setIcon(QIcon.fromTheme("network-wired"))
            self.connect_button.clicked.connect(self.connect_clicked.emit)
            self.connect_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                }
            """)
            controls_layout.addWidget(self.connect_button)
            
            # Espaçador
            controls_layout.addSpacerItem(
                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            )
            
            # Controles de reprodução
            self.rewind_button = QPushButton("⏪")
            self.rewind_button.setFont(QFont("Arial", 14))
            self.rewind_button.clicked.connect(self.rewind_clicked.emit)
            controls_layout.addWidget(self.rewind_button)
            
            self.play_pause_button = QPushButton("⏵")
            self.play_pause_button.setFont(QFont("Arial", 14))
            self.play_pause_button.clicked.connect(self._handle_play_pause)
            controls_layout.addWidget(self.play_pause_button)
            
            self.forward_button = QPushButton("⏩")
            self.forward_button.setFont(QFont("Arial", 14))
            self.forward_button.clicked.connect(self.forward_clicked.emit)
            controls_layout.addWidget(self.forward_button)
            
            # Espaçador
            controls_layout.addSpacerItem(
                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            )
            
            layout.addWidget(controls)
            
        except Exception as e:
            logger.error(f"Erro ao configurar controles: {str(e)}")
            raise
    
    def setup_logs(self, layout):
        """Configura a área de logs."""
        try:
            # Título dos logs
            logs_title = QLabel("Logs de Análise")
            logs_title.setFont(QFont("Arial", 10, QFont.Bold))
            layout.addWidget(logs_title)
            
            # Área de logs
            self.logs_text = QTextEdit()
            self.logs_text.setReadOnly(True)
            self.logs_text.setMaximumHeight(150)
            self.logs_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px;
                }
            """)
            layout.addWidget(self.logs_text)
            
        except Exception as e:
            logger.error(f"Erro ao configurar logs: {str(e)}")
            raise
    
    def show_error_ui(self):
        """Exibe interface de erro."""
        layout = QVBoxLayout(self)
        error_label = QLabel("Erro ao carregar interface")
        error_label.setStyleSheet("color: red;")
        layout.addWidget(error_label)
    
    def update_frame(self, frame):
        """
        Atualiza o frame de vídeo.
        
        Args:
            frame: Frame OpenCV para exibir
        """
        try:
            pixmap = frame_to_pixmap(frame)
            if pixmap:
                self.video_label.setPixmap(pixmap)
                self.overlay_label.raise_()
            else:
                logger.warning("Frame inválido recebido")
                
        except Exception as e:
            logger.error(f"Erro ao atualizar frame: {str(e)}")
    
    def update_time(self, time_ms: int):
        """
        Atualiza o tempo exibido.
        
        Args:
            time_ms: Tempo em milissegundos
        """
        try:
            hours = time_ms // 3600000
            minutes = (time_ms % 3600000) // 60000
            seconds = (time_ms % 60000) // 1000
            self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        except Exception as e:
            logger.error(f"Erro ao atualizar tempo: {str(e)}")
    
    def set_playing(self, is_playing: bool):
        """
        Define o estado de reprodução.
        
        Args:
            is_playing: Se está reproduzindo
        """
        try:
            self.is_playing = is_playing
            self.play_pause_button.setText("⏸" if is_playing else "⏵")
        except Exception as e:
            logger.error(f"Erro ao definir estado de reprodução: {str(e)}")
    
    def enable_controls(self, enabled: bool):
        """
        Habilita/desabilita controles.
        
        Args:
            enabled: Se os controles devem estar habilitados
        """
        try:
            self.play_pause_button.setEnabled(enabled)
            self.rewind_button.setEnabled(enabled)
            self.forward_button.setEnabled(enabled)
            self.connect_button.setEnabled(not enabled)
        except Exception as e:
            logger.error(f"Erro ao habilitar controles: {str(e)}")
    
    def add_log(self, message: str):
        """
        Adiciona mensagem aos logs.
        
        Args:
            message: Mensagem para adicionar
        """
        try:
            self.logs_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
            self.logs_text.verticalScrollBar().setValue(
                self.logs_text.verticalScrollBar().maximum()
            )
        except Exception as e:
            logger.error(f"Erro ao adicionar log: {str(e)}")
    
    def clear_display(self):
        """Limpa a exibição."""
        try:
            self.video_label.clear()
            self.video_label.setText("Aguardando fonte de vídeo...")
            self.time_label.setText("00:00:00")
            self.progress_bar.setValue(0)
            self.logs_text.clear()
        except Exception as e:
            logger.error(f"Erro ao limpar display: {str(e)}")
    
    def _handle_play_pause(self):
        """Manipula clique no botão play/pause."""
        try:
            self.play_pause_clicked.emit()
        except Exception as e:
            logger.error(f"Erro ao manipular play/pause: {str(e)}")