"""
Diálogo para seleção da fonte de vídeo.
"""

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QComboBox,
    QProgressDialog,
    QFrame,
    QMessageBox,
    QSpacerItem,
    QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
import cv2
import platform
import time
from typing import Optional, Tuple, List, Dict
from config.logging_config import get_logger
from config.app_config import VIDEO_CONFIG

logger = get_logger('source_dialog')

class CameraBackend:
    """Gerenciador de câmera simplificado."""
    
    @staticmethod
    def try_backend(camera_id: int,
                   backend: Optional[int] = None) -> Tuple[Optional[cv2.VideoCapture], Optional[str]]:
        """Inicializa uma câmera de forma direta."""
        cap = cv2.VideoCapture(camera_id)
        return (cap, None) if cap.isOpened() else (None, "Câmera não disponível")

class CameraInfo:
    """Informações sobre uma câmera."""
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
        self.width = 0
        self.height = 0
        self.fps = 0
        self.capture = None
    
    def __str__(self) -> str:
        return f"{self.name} ({self.width}x{self.height} @ {self.fps:.1f}fps)"


class VideoSourceDialog(QDialog):
    """Diálogo para seleção da fonte de vídeo."""
    
    def __init__(self, parent=None):
        """Inicializa o diálogo."""
        super().__init__(parent)
        self.source_type = None
        self.camera_id = 0
        self.available_cameras: List[CameraInfo] = []
        self.setup_ui()
    
    def closeEvent(self, event):
        """Evento chamado quando o diálogo é fechado."""
        try:
            self._cleanup_cameras()
        except Exception as e:
            logger.error(f"Erro ao fechar diálogo: {str(e)}")
        super().closeEvent(event)
    
    def setup_ui(self):
        """Configura a interface do diálogo."""
        try:
            self.setWindowTitle("Selecionar Fonte de Vídeo")
            self.setFixedWidth(500)
            self.setStyleSheet("""
                QDialog {
                    background-color: white;
                }
                QPushButton {
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QComboBox {
                    padding: 4px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                }
            """)
            
            layout = QVBoxLayout(self)
            layout.setSpacing(15)
            
            # Título
            title = QLabel("Escolha a Fonte de Vídeo")
            title.setFont(QFont("Arial", 14, QFont.Bold))
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            
            # Status
            self.status_frame = QFrame()
            self.status_frame.setFrameStyle(QFrame.StyledPanel)
            status_layout = QVBoxLayout(self.status_frame)
            
            self.status_label = QLabel("Clique em 'Conectar a Câmera' para buscar câmeras disponíveis")
            self.status_label.setAlignment(Qt.AlignCenter)
            status_layout.addWidget(self.status_label)
            
            self.progress_label = QLabel()
            self.progress_label.setAlignment(Qt.AlignCenter)
            self.progress_label.hide()
            status_layout.addWidget(self.progress_label)
            
            layout.addWidget(self.status_frame)
            
            # Botões de fonte
            source_layout = QHBoxLayout()
            
            self.camera_btn = QPushButton("Câmera")
            self.camera_btn.setIcon(QIcon.fromTheme("camera-web"))
            self.camera_btn.clicked.connect(self.select_camera)
            source_layout.addWidget(self.camera_btn)
            
            self.video_btn = QPushButton("Arquivo de Vídeo")
            self.video_btn.setIcon(QIcon.fromTheme("video-x-generic"))
            self.video_btn.clicked.connect(self.select_video)
            source_layout.addWidget(self.video_btn)
            
            layout.addLayout(source_layout)

            # Botão de busca de câmeras
            self.search_camera_btn = QPushButton("Conectar a Câmera")
            self.search_camera_btn.setIcon(QIcon.fromTheme("camera-web"))
            self.search_camera_btn.clicked.connect(self.detect_cameras)
            self.search_camera_btn.hide()
            layout.addWidget(self.search_camera_btn)
            
            # Seletor de câmera
            self.camera_frame = QFrame()
            self.camera_frame.setFrameStyle(QFrame.StyledPanel)
            camera_layout = QVBoxLayout(self.camera_frame)
            
            self.camera_combo = QComboBox()
            self.camera_combo.currentIndexChanged.connect(self._update_camera_info)
            camera_layout.addWidget(self.camera_combo)
            
            self.camera_info = QLabel()
            self.camera_info.setStyleSheet("color: #666;")
            camera_layout.addWidget(self.camera_info)
            
            self.camera_frame.hide()
            layout.addWidget(self.camera_frame)
            
            # Botões de ação
            buttons = QHBoxLayout()
            
            self.cancel_btn = QPushButton("Cancelar")
            self.cancel_btn.setIcon(QIcon.fromTheme("dialog-cancel"))
            self.cancel_btn.clicked.connect(self.reject)
            buttons.addWidget(self.cancel_btn)
            
            buttons.addSpacerItem(
                QSpacerItem(20, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
            )
            
            self.ok_btn = QPushButton("Conectar")
            self.ok_btn.setIcon(QIcon.fromTheme("dialog-ok"))
            self.ok_btn.clicked.connect(self.accept)
            self.ok_btn.hide()
            buttons.addWidget(self.ok_btn)
            
            layout.addLayout(buttons)
            
        except Exception as e:
            logger.error(f"Erro ao configurar interface: {str(e)}")
            self.show_error_ui()
    
    def show_error_ui(self):
        """Exibe interface de erro."""
        layout = QVBoxLayout(self)
        error = QLabel("Erro ao carregar interface")
        error.setStyleSheet("color: red;")
        layout.addWidget(error)
    
    def _cleanup_cameras(self):
        """Libera os recursos das câmeras de forma otimizada."""
        for camera in self.available_cameras:
            if camera.capture and camera.capture.isOpened():
                camera.capture.release()
                camera.capture = None
        self.available_cameras.clear()
        self.camera_combo.clear()
    
    def detect_cameras(self):
        """Detecta câmeras de forma rápida e direta."""
        self._cleanup_cameras()
        
        cap, error = CameraBackend.try_backend(0)
        if not cap:
            self.status_label.setText("Nenhuma câmera detectada")
            self.status_label.setStyleSheet("color: red;")
            return
        
        # Configura câmera com informações básicas
        info = CameraInfo(0, "Câmera Principal")
        info.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        info.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        info.capture = cap
        
        # Atualiza interface rapidamente
        self.available_cameras.append(info)
        self.camera_combo.addItem(str(info), info)
        self.camera_frame.show()
        self.ok_btn.show()
        self.status_label.setText("Câmera conectada")
        self.status_label.setStyleSheet("color: green;")
    
    def _update_camera_info(self, index: int):
        """Atualiza informações básicas da câmera."""
        if index >= 0:
            camera = self.camera_combo.itemData(index)
            self.camera_info.setText(f"Resolução: {camera.width}x{camera.height}")
    
    def select_camera(self):
        """Seleciona câmera como fonte."""
        try:
            self.source_type = "camera"
            self.camera_frame.hide()  # Esconde o frame de seleção até detectar câmeras
            self.ok_btn.hide()  # Esconde o botão OK até selecionar uma câmera
            self.search_camera_btn.show()  # Mostra o botão de busca
            self.camera_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                }
            """)
            self.video_btn.setStyleSheet("")
            self.status_label.setText("Clique em 'Conectar a Câmera' para buscar câmeras disponíveis")
            self.status_label.setStyleSheet("")
            logger.info("Modo câmera selecionado")
            
        except Exception as e:
            logger.error(f"Erro ao selecionar câmera: {str(e)}")
    
    def select_video(self):
        """Seleciona vídeo como fonte."""
        try:
            self.source_type = "video"
            self.camera_frame.hide()
            self.video_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                }
            """)
            self.camera_btn.setStyleSheet("")
            logger.info("Modo vídeo selecionado")
            self.accept()
            
        except Exception as e:
            logger.error(f"Erro ao selecionar vídeo: {str(e)}")
    
    def get_camera_info(self) -> Optional[CameraInfo]:
        """Retorna as informações da câmera selecionada."""
        camera = self.camera_combo.currentData()
        if not camera:
            return None
            
        # Reutiliza a conexão existente se estiver ativa
        if camera.capture and camera.capture.isOpened():
            return camera
            
        # Cria nova conexão apenas se necessário
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimiza buffer
            camera.capture = cap
            return camera
            
        return None
    
    def get_camera_id(self) -> Optional[int]:
        """Retorna o ID da câmera selecionada."""
        camera = self.get_camera_info()
        return camera.id if camera else None