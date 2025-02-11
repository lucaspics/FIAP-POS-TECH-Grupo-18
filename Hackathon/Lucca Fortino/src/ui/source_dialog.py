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

class CameraInfo:
    """Informações sobre uma câmera."""
    def __init__(self, id: int, name: str, backend: Optional[int] = None):
        self.id = id
        self.name = name
        self.backend = backend
        self.width = 0
        self.height = 0
        self.fps = 0
        self.backend_name = self._get_backend_name()
    
    def _get_backend_name(self) -> str:
        """Retorna o nome do backend."""
        if self.backend is None:
            return "Padrão"
        elif self.backend == cv2.CAP_DSHOW:
            return "DirectShow"
        elif self.backend == cv2.CAP_MSMF:
            return "Media Foundation"
        else:
            return f"Backend {self.backend}"
    
    def __str__(self) -> str:
        return (
            f"{self.name} ({self.width}x{self.height} @ {self.fps:.1f}fps) "
            f"[{self.backend_name}]"
        )

class CameraBackend:
    """Gerenciador de backends de câmera."""
    
    @staticmethod
    def get_available_backends() -> List[Optional[int]]:
        """
        Retorna lista de backends disponíveis para o sistema.
        
        Returns:
            Lista de backends
        """
        if platform.system() == 'Windows':
            return [cv2.CAP_MSMF, cv2.CAP_DSHOW, None]
        return [None]  # Backend padrão para outros sistemas
    
    @staticmethod
    def try_backend(camera_id: int,
                   backend: Optional[int],
                   timeout: float = 2.0) -> Tuple[Optional[cv2.VideoCapture], Optional[str]]:
        """
        Tenta inicializar uma câmera com um backend específico.
        
        Args:
            camera_id: ID da câmera
            backend: Backend a usar
            timeout: Tempo máximo de tentativa
            
        Returns:
            Tupla (captura, erro)
        """
        start_time = time.time()
        cap = None
        
        try:
            logger.info(f"Tentando câmera {camera_id} com backend {backend}")
            
            # Inicializar câmera
            if backend == cv2.CAP_DSHOW:
                cap = cv2.VideoCapture(camera_id + cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(camera_id)
            
            if not cap.isOpened():
                if cap:
                    cap.release()
                return None, "Não foi possível abrir a câmera"
            
            # Configurar propriedades
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_CONFIG['width'])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_CONFIG['height'])
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
            
            # Verificar estabilidade
            frames_read = 0
            required_frames = 3
            frame_times = []
            
            while time.time() - start_time < timeout:
                ret, frame = cap.read()
                if ret and frame is not None:
                    frame_times.append(time.time())
                    frames_read += 1
                    
                    if frames_read >= required_frames:
                        # Calcular FPS real
                        if len(frame_times) >= 2:
                            intervals = [
                                frame_times[i+1] - frame_times[i]
                                for i in range(len(frame_times)-1)
                            ]
                            avg_interval = sum(intervals) / len(intervals)
                            fps = 1.0 / avg_interval if avg_interval > 0 else 0
                            logger.info(f"FPS calculado: {fps:.1f}")
                        
                        return cap, None
                else:
                    frames_read = 0
                    frame_times.clear()
                
                time.sleep(0.1)
            
            # Timeout
            if cap:
                cap.release()
            return None, "Timeout ao tentar ler frames"
            
        except Exception as e:
            logger.error(f"Erro ao testar câmera: {str(e)}")
            if cap:
                cap.release()
            return None, str(e)

class CameraDetectionThread(QThread):
    """Thread para detectar câmeras disponíveis."""
    
    camera_found = pyqtSignal(CameraInfo)  # Emitido quando uma câmera é encontrada
    progress = pyqtSignal(int, int)        # Emitido para atualizar progresso
    finished = pyqtSignal()                # Emitido quando a detecção termina
    
    def run(self):
        """Executa a detecção de câmeras."""
        try:
            backends = CameraBackend.get_available_backends()
            total_steps = len(backends) * 2  # 2 câmeras por backend
            current_step = 0
            
            for i in range(2):
                for backend in backends:
                    current_step += 1
                    self.progress.emit(current_step, total_steps)
                    
                    cap, error = CameraBackend.try_backend(i, backend)
                    if cap:
                        # Coletar informações
                        info = CameraInfo(i, f"Câmera {i}", backend)
                        info.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        info.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        info.fps = cap.get(cv2.CAP_PROP_FPS)
                        
                        cap.release()
                        self.camera_found.emit(info)
                        break  # Câmera encontrada, tentar próximo ID
            
            self.finished.emit()
            
        except Exception as e:
            logger.error(f"Erro na detecção de câmeras: {str(e)}")
            self.finished.emit()

class VideoSourceDialog(QDialog):
    """Diálogo para seleção da fonte de vídeo."""
    
    def __init__(self, parent=None):
        """Inicializa o diálogo."""
        super().__init__(parent)
        self.source_type = None
        self.camera_id = 0
        self.available_cameras: List[CameraInfo] = []
        self.setup_ui()
        self.detect_cameras()
    
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
            
            self.status_label = QLabel("Detectando câmeras...")
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
            self.camera_btn.setEnabled(False)
            source_layout.addWidget(self.camera_btn)
            
            self.video_btn = QPushButton("Arquivo de Vídeo")
            self.video_btn.setIcon(QIcon.fromTheme("video-x-generic"))
            self.video_btn.clicked.connect(self.select_video)
            source_layout.addWidget(self.video_btn)
            
            layout.addLayout(source_layout)
            
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
    
    def detect_cameras(self):
        """Inicia a detecção de câmeras."""
        try:
            self.detection_thread = CameraDetectionThread()
            self.detection_thread.camera_found.connect(self._add_camera)
            self.detection_thread.progress.connect(self._update_progress)
            self.detection_thread.finished.connect(self._detection_finished)
            self.detection_thread.start()
            
        except Exception as e:
            logger.error(f"Erro ao iniciar detecção: {str(e)}")
            self.status_label.setText("Erro ao detectar câmeras")
            self.status_label.setStyleSheet("color: red;")
    
    def _add_camera(self, camera: CameraInfo):
        """
        Adiciona uma câmera à lista.
        
        Args:
            camera: Informações da câmera
        """
        try:
            self.available_cameras.append(camera)
            self.camera_combo.addItem(str(camera), camera)
            logger.info(f"Câmera adicionada: {camera}")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar câmera: {str(e)}")
    
    def _update_progress(self, current: int, total: int):
        """
        Atualiza o progresso da detecção.
        
        Args:
            current: Passo atual
            total: Total de passos
        """
        try:
            self.progress_label.setText(f"Progresso: {current}/{total}")
            self.progress_label.show()
            
        except Exception as e:
            logger.error(f"Erro ao atualizar progresso: {str(e)}")
    
    def _detection_finished(self):
        """Finaliza o processo de detecção."""
        try:
            self.progress_label.hide()
            
            if self.available_cameras:
                self.status_label.setText(
                    f"Câmeras detectadas: {len(self.available_cameras)}"
                )
                self.status_label.setStyleSheet("color: green;")
                self.camera_btn.setEnabled(True)
                logger.info("Detecção concluída com sucesso")
            else:
                self.status_label.setText("Nenhuma câmera detectada")
                self.status_label.setStyleSheet("color: red;")
                self.camera_btn.setEnabled(False)
                logger.warning("Nenhuma câmera detectada")
            
        except Exception as e:
            logger.error(f"Erro ao finalizar detecção: {str(e)}")
    
    def _update_camera_info(self, index: int):
        """
        Atualiza informações da câmera selecionada.
        
        Args:
            index: Índice da câmera
        """
        try:
            if index >= 0:
                camera = self.camera_combo.itemData(index)
                self.camera_info.setText(
                    f"Resolução: {camera.width}x{camera.height}\n"
                    f"FPS: {camera.fps:.1f}\n"
                    f"Backend: {camera.backend_name}"
                )
            
        except Exception as e:
            logger.error(f"Erro ao atualizar info: {str(e)}")
    
    def select_camera(self):
        """Seleciona câmera como fonte."""
        try:
            self.source_type = "camera"
            self.camera_frame.show()
            self.ok_btn.show()
            self.camera_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                }
            """)
            self.video_btn.setStyleSheet("")
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
    
    def get_camera_id(self) -> Optional[int]:
        """
        Retorna o ID da câmera selecionada.
        
        Returns:
            ID da câmera ou None se nenhuma selecionada
        """
        try:
            camera = self.camera_combo.currentData()
            if camera:
                logger.info(f"Câmera retornada: {camera}")
                return camera.id
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter câmera: {str(e)}")
            return None