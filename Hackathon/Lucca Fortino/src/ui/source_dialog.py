from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QProgressDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import cv2
import platform
import time
from config.logging_config import logger

class CameraBackend:
    """Classe para gerenciar diferentes backends de câmera."""
    
    @staticmethod
    def try_backend(camera_id, backend, timeout=2.0):
        """Tenta inicializar uma câmera com um backend específico."""
        start_time = time.time()
        cap = None
        backend_name = "padrão" if backend is None else (
            "DirectShow" if backend == cv2.CAP_DSHOW else str(backend)
        )
        
        try:
            logger.info(f"Tentando inicializar câmera {camera_id} com backend {backend_name}")
            
            # Configuração específica para DirectShow
            if backend == cv2.CAP_DSHOW:
                cap = cv2.VideoCapture(camera_id + cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(camera_id)
            
            if not cap.isOpened():
                if cap:
                    cap.release()
                logger.warning(f"Não foi possível abrir câmera {camera_id} com backend {backend_name}")
                return None, f"Não foi possível abrir câmera com backend {backend_name}"
            
            # Configurações básicas para estabilidade
            try:
                if backend == cv2.CAP_DSHOW:
                    # Tentar configurar propriedades uma por uma
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    time.sleep(0.1)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    time.sleep(0.1)
                    cap.set(cv2.CAP_PROP_FPS, 30)
                    time.sleep(0.1)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
                    time.sleep(0.1)
                    
                    # Verificar se as configurações foram aplicadas
                    actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                    actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    actual_fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    logger.info(f"Configurações da câmera: {actual_width}x{actual_height} @ {actual_fps}fps")
            except Exception as e:
                logger.warning(f"Erro ao configurar propriedades da câmera: {str(e)}")
            
            # Tenta ler múltiplos frames para garantir estabilidade
            frames_read = 0
            required_frames = 3
            last_frame_time = None
            
            while time.time() - start_time < timeout:
                ret, frame = cap.read()
                if ret and frame is not None:
                    current_time = time.time()
                    if last_frame_time is not None:
                        frame_interval = current_time - last_frame_time
                        logger.debug(f"Intervalo entre frames: {frame_interval:.3f}s")
                    
                    last_frame_time = current_time
                    frames_read += 1
                    
                    if frames_read >= required_frames:
                        logger.info(f"Câmera {camera_id} inicializada com sucesso usando backend {backend_name}")
                        return cap, None
                else:
                    frames_read = 0
                    logger.debug(f"Falha ao ler frame da câmera {camera_id}")
                
                time.sleep(0.1)
            
            # Se chegou aqui, houve timeout
            logger.warning(f"Timeout ao tentar ler frames consecutivos da câmera {camera_id} com backend {backend_name}")
            if cap:
                cap.release()
            return None, "Timeout ao tentar ler frames consecutivos"
            
        except Exception as e:
            logger.error(f"Erro ao tentar inicializar câmera {camera_id} com backend {backend_name}: {str(e)}")
            if cap:
                cap.release()
            return None, str(e)

class CameraDetectionThread(QThread):
    """Thread para detectar câmeras sem bloquear a interface."""
    camera_found = pyqtSignal(int, str)
    finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.backends = []
        if platform.system() == 'Windows':
            # No Windows, tenta apenas o backend padrão
            self.backends = [None]
        else:
            # Em outros sistemas, usa apenas o backend padrão
            self.backends = [None]
    
    def run(self):
        """Executa a detecção de câmeras."""
        for i in range(2):  # Testa apenas os primeiros índices
            camera_detected = False
            
            for backend in self.backends:
                try:
                    cap, error = CameraBackend.try_backend(i, backend)
                    if cap:
                        # Câmera detectada com sucesso
                        name = f"Câmera {i}"
                        if backend == cv2.CAP_DSHOW:
                            name += " (DirectShow)"
                        
                        self.camera_found.emit(i, name)
                        camera_detected = True
                        cap.release()
                        break
                    else:
                        logger.warning(f"Falha ao testar câmera {i}: {error}")
                
                except Exception as e:
                    logger.error(f"Erro ao testar câmera {i}: {str(e)}")
            
            if not camera_detected:
                logger.warning(f"Não foi possível detectar câmera {i} com nenhum backend")
        
        self.finished.emit()
        logger.info("Detecção de câmeras concluída")

class VideoSourceDialog(QDialog):
    """Diálogo para seleção da fonte de vídeo."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.source_type = None
        self.camera_id = 0
        self.available_cameras = []
        self.setup_ui()
        self.detect_cameras()
    
    def detect_cameras(self):
        """Inicia a detecção de câmeras em uma thread separada."""
        self.progress = QProgressDialog("Detectando câmeras...", None, 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setMinimumDuration(0)
        self.progress.setCancelButton(None)
        self.progress.setWindowTitle("Aguarde")
        
        self.detection_thread = CameraDetectionThread()
        self.detection_thread.camera_found.connect(self.add_camera)
        self.detection_thread.finished.connect(self.detection_finished)
        logger.info("Iniciando detecção de câmeras...")
        self.detection_thread.start()
    
    def add_camera(self, camera_id, name):
        """Adiciona uma câmera encontrada à lista."""
        self.available_cameras.append((camera_id, name))
        self.camera_combo.addItem(name, camera_id)
        logger.info(f"Câmera adicionada: {name} (ID: {camera_id})")
    
    def detection_finished(self):
        """Chamado quando a detecção de câmeras termina."""
        self.progress.close()
        
        if self.available_cameras:
            self.status_label.setText(f"Câmeras detectadas: {len(self.available_cameras)}")
            self.status_label.setStyleSheet("color: green;")
            self.camera_btn.setEnabled(True)
            self.camera_btn.setToolTip("")
            logger.info(f"Total de câmeras detectadas: {len(self.available_cameras)}")
        else:
            self.status_label.setText("Nenhuma câmera detectada")
            self.status_label.setStyleSheet("color: red;")
            self.camera_btn.setEnabled(False)
            self.camera_btn.setToolTip("Nenhuma câmera detectada")
            logger.warning("Nenhuma câmera foi detectada")
    
    def setup_ui(self):
        """Configura a interface do diálogo."""
        self.setWindowTitle("Selecionar Fonte de Vídeo")
        self.setFixedWidth(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Título
        title = QLabel("Escolha a fonte de vídeo")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Status das câmeras
        self.status_label = QLabel("Detectando câmeras...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Botões de fonte
        btn_layout = QHBoxLayout()
        
        # Botão de câmera
        self.camera_btn = QPushButton("Câmera do Computador")
        self.camera_btn.setStyleSheet("padding: 10px;")
        self.camera_btn.clicked.connect(self.select_camera)
        self.camera_btn.setEnabled(False)
        btn_layout.addWidget(self.camera_btn)
        
        # Botão de vídeo
        self.video_btn = QPushButton("Carregar Vídeo")
        self.video_btn.setStyleSheet("padding: 10px;")
        self.video_btn.clicked.connect(self.select_video)
        btn_layout.addWidget(self.video_btn)
        
        layout.addLayout(btn_layout)
        
        # Seletor de câmera (inicialmente oculto)
        self.camera_layout = QHBoxLayout()
        self.camera_label = QLabel("Selecione a câmera:")
        self.camera_combo = QComboBox()
        
        self.camera_layout.addWidget(self.camera_label)
        self.camera_layout.addWidget(self.camera_combo)
        self.camera_widget = QLabel()
        self.camera_widget.setLayout(self.camera_layout)
        self.camera_widget.hide()
        layout.addWidget(self.camera_widget)
        
        # Botões de confirmação
        buttons_layout = QHBoxLayout()
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.hide()
        buttons_layout.addWidget(self.ok_btn)
        
        layout.addLayout(buttons_layout)
    
    def select_camera(self):
        """Seleciona câmera como fonte."""
        self.source_type = "camera"
        self.camera_widget.show()
        self.ok_btn.show()
        self.camera_btn.setEnabled(False)
        self.video_btn.setEnabled(True)
        logger.info("Modo câmera selecionado")
    
    def select_video(self):
        """Seleciona vídeo como fonte."""
        self.source_type = "video"
        self.camera_widget.hide()
        logger.info("Modo vídeo selecionado")
        self.accept()
    
    def get_camera_id(self):
        """Retorna o ID da câmera selecionada."""
        camera_id = self.camera_combo.currentData()
        logger.info(f"Câmera selecionada: ID {camera_id}")
        return camera_id