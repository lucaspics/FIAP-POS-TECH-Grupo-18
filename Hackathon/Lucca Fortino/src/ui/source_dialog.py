from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QProgressDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import cv2
import platform
import time
from config.logging_config import logger

class CameraDetectionThread(QThread):
    """Thread para detectar câmeras sem bloquear a interface."""
    camera_found = pyqtSignal(int, str)
    finished = pyqtSignal()
    
    def run(self):
        """Executa a detecção de câmeras."""
        for i in range(2):  # Testa apenas os primeiros índices para ser mais rápido
            try:
                logger.info(f"Testando câmera {i}...")
                cap = cv2.VideoCapture(i)
                
                if not cap.isOpened():
                    logger.warning(f"Câmera {i} não pôde ser aberta")
                    continue
                
                # Tenta ler um frame com timeout
                start_time = time.time()
                ret = False
                frame = None
                
                while time.time() - start_time < 0.3:  # timeout reduzido para 300ms
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        break
                    time.sleep(0.1)  # Pequena pausa entre tentativas
                
                # Libera a câmera imediatamente após o teste
                cap.release()
                
                if ret and frame is not None:
                    name = f"Câmera {i}"
                    logger.info(f"Câmera encontrada: {name}")
                    self.camera_found.emit(i, name)
                else:
                    logger.warning(f"Não foi possível ler frame da câmera {i}")
                    
            except Exception as e:
                logger.error(f"Erro ao testar câmera {i}: {str(e)}")
                if 'cap' in locals() and cap is not None:
                    cap.release()
                continue
                    
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