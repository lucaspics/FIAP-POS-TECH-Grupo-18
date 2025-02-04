import os
import cv2
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QTabWidget, QFileDialog
from PyQt5.QtCore import QTimer
from config.logging_config import logger
from config.app_config import DEFAULT_ANALYSIS_INTERVAL, FRAME_INTERVAL
from workers.analysis_worker import AnalysisWorker
from ui.video_tab import VideoTab
from ui.settings_tab import SettingsTab
from utils.video_utils import resize_frame, bgr_to_rgb

class SecurityCameraApp(QWidget):
    """Janela principal da aplicação."""
    
    def __init__(self):
        super().__init__()
        self.init_variables()
        self.setup_ui()
        
    def init_variables(self):
        """Inicializa as variáveis de controle."""
        self.video_path = None
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.is_playing = False
        
        # Variáveis de análise
        self.analysis_interval = DEFAULT_ANALYSIS_INTERVAL
        self.current_frame_count = 0
        self.analysis_in_progress = False
        self.worker = None
        
    def setup_ui(self):
        """Configura a interface do usuário."""
        self.setWindowTitle("Sistema de Câmera de Segurança")
        self.setGeometry(100, 100, 1000, 600)
        
        # Layout principal
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)
        
        # Tabs
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)
        
        # Aba de vídeo
        self.video_tab = VideoTab(self)
        self.tabs.addTab(self.video_tab, "Vídeo")
        
        # Aba de configurações
        self.settings_tab = SettingsTab(self)
        self.tabs.addTab(self.settings_tab, "Configurações")
        
    def connect_camera(self):
        """Conecta à fonte de vídeo."""
        options = QFileDialog.Options()
        self.video_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione o vídeo",
            "",
            "Arquivos de Vídeo (*.mp4 *.avi *.mov)",
            options=options
        )
        
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            if self.cap.isOpened():
                self.video_tab.enable_controls(True)
                logger.info(f"Vídeo carregado: {self.video_path}")
                self.toggle_play_pause()  # Inicia reprodução
            else:
                logger.error("Erro ao carregar o vídeo.")
                
    def toggle_play_pause(self):
        """Alterna entre play e pause."""
        if self.is_playing:
            self.timer.stop()
            self.video_tab.play_pause_button.setText("Play")
        else:
            self.timer.start(FRAME_INTERVAL)
            self.video_tab.play_pause_button.setText("Pause")
        self.is_playing = not self.is_playing
        
    def rewind_video(self):
        """Retrocede o vídeo em 5 segundos."""
        if not self.cap:
            return
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        target_frame = max(0, current_frame - 150)  # 5 segundos (30 FPS * 5)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
    def forward_video(self):
        """Avança o vídeo em 5 segundos."""
        if not self.cap:
            return
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        target_frame = min(total_frames - 1, current_frame + 150)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
    def update_frame(self):
        """Atualiza o frame atual do vídeo."""
        if not self.cap:
            return
            
        ret, frame = self.cap.read()
        if not ret:
            logger.info("Fim do vídeo.")
            self.timer.stop()
            self.is_playing = False
            self.video_tab.play_pause_button.setText("Play")
            return
            
        # Processar frame
        frame = resize_frame(frame)
        self.video_tab.update_video_frame(frame)
        
        # Atualizar tempo
        current_time = int(self.cap.get(cv2.CAP_PROP_POS_MSEC))
        self.video_tab.update_time(current_time)
        
        # Incrementar contador e verificar necessidade de análise
        self.current_frame_count += 1
        if self.current_frame_count % self.analysis_interval == 0 and not self.analysis_in_progress:
            self.analyze_frame(frame)
            
    def analyze_frame(self, frame):
        """Inicia a análise de um frame."""
        try:
            # Limpar worker anterior
            if self.worker:
                try:
                    self.worker.disconnect()
                    self.worker.deleteLater()
                except Exception as e:
                    logger.error(f"Erro ao limpar worker anterior: {str(e)}")
                self.worker = None
            
            # Criar novo worker
            self.analysis_in_progress = True
            frame_rgb = bgr_to_rgb(frame.copy())
            self.worker = AnalysisWorker(frame_rgb, self.current_frame_count)
            
            # Conectar sinais
            self.worker.analysis_complete.connect(self.handle_analysis_result)
            self.worker.analysis_error.connect(self.handle_analysis_error)
            self.worker.finished.connect(self._on_analysis_finished)
            
            # Iniciar análise
            self.worker.start()
            self.video_tab.add_log(f"Frame {self.current_frame_count} - Iniciando análise...")
            
        except Exception as e:
            logger.error(f"Erro ao criar worker: {str(e)}")
            self.analysis_in_progress = False
            
    def handle_analysis_result(self, result):
        """Processa o resultado da análise."""
        try:
            self.video_tab.add_log("=== Análise do Frame ===")
            self.video_tab.add_log(f"Timestamp: {result.get('timestamp')}")
            self.video_tab.add_log(f"Detecções encontradas: {len(result.get('detections', []))}")
            
            for det in result.get('detections', []):
                det_info = f"- Classe: {det.get('class_name', 'unknown')}, Confiança: {float(det['confidence']):.2f}"
                self.video_tab.add_log(det_info)
            
            # Verificar necessidade de alerta
            alert_value = int(result.get('alert_triggered', 0))
            if alert_value == 1:
                self.video_tab.add_log(">>> ALERTA DETECTADO!")
                _, frame = self.cap.read()
                if frame is not None:
                    self.trigger_alert(frame=frame)
                    
        except Exception as e:
            logger.error(f"Erro ao processar resultado: {str(e)}")
            self.video_tab.add_log(f"Erro ao processar resultado: {str(e)}")
            
    def handle_analysis_error(self, error_msg):
        """Trata erros na análise."""
        logger.error(f"Erro na análise do frame {self.current_frame_count}: {error_msg}")
        self.video_tab.add_log(f"ERRO no frame {self.current_frame_count}: {error_msg}")
        
    def _on_analysis_finished(self):
        """Chamado quando a análise é finalizada."""
        logger.info(f"Análise do frame {self.current_frame_count} finalizada")
        self.analysis_in_progress = False
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
            
    def trigger_alert(self, frame=None):
        """Dispara um alerta."""
        if not self.cap or not self.cap.isOpened():
            logger.error("Erro: Nenhum vídeo conectado.")
            return
            
        if frame is None:
            current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos - 1)
            ret, frame = self.cap.read()
            if not ret:
                logger.error("Não foi possível capturar o frame.")
                return
                
        current_time = int(self.cap.get(cv2.CAP_PROP_POS_MSEC))
        self.video_tab.add_alert(frame, current_time)
        logger.info("Alerta registrado - o email será enviado pela API")
        
    def jump_to_alert(self, item):
        """Salta para um momento específico do vídeo."""
        if not self.cap:
            return
            
        alert_time = item.data(0)
        target_time = max(0, alert_time - 1000)  # 1 segundo antes
        self.cap.set(cv2.CAP_PROP_POS_MSEC, target_time)
        
        # Atualizar frame
        ret, frame = self.cap.read()
        if ret:
            frame = resize_frame(frame)
            self.video_tab.update_video_frame(frame)