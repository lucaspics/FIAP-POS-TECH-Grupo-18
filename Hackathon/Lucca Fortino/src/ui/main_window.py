import os
import cv2
import json
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QTabWidget, QFileDialog
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from config.logging_config import logger
from config.app_config import (
    DEFAULT_ANALYSIS_INTERVAL, FRAME_INTERVAL,
    MIN_TIME_BETWEEN_ALERTS, LOG_DIRS
)
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
        self.clear_alerts()  # Limpa alertas antigos ao iniciar
        
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
        self.last_analyzed_frame = 0
        self.active_workers = []
        self.max_concurrent_workers = 2
        
        # Cache do último frame para alertas
        self.last_frame = None
        self.current_video_time = 0
        
        # Controle de alertas processados
        self.processed_alerts = set()
        self.alert_timer = None
        
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
        
    def clear_alerts(self):
        """Limpa todos os arquivos de alerta."""
        try:
            alerts_dir = os.path.join(LOG_DIRS['base'], 'alerts')
            if os.path.exists(alerts_dir):
                shutil.rmtree(alerts_dir)
            os.makedirs(alerts_dir, exist_ok=True)
            logger.info("Diretório de alertas limpo")
            
            # Limpar lista de alertas na interface
            if hasattr(self, 'video_tab'):
                self.video_tab.logs_list.clear()
                self.processed_alerts.clear()
            
        except Exception as e:
            logger.error(f"Erro ao limpar alertas: {str(e)}")
            
    def setup_alert_timer(self):
        """Configura timer para verificar novos alertas."""
        if self.alert_timer is None:
            self.alert_timer = QTimer(self)
            self.alert_timer.timeout.connect(self.check_new_alerts)
        self.alert_timer.start(1000)  # Verifica a cada segundo
        logger.info("Monitoramento de alertas iniciado")
        
    def stop_alert_timer(self):
        """Para o timer de alertas."""
        if self.alert_timer is not None:
            self.alert_timer.stop()
            logger.info("Monitoramento de alertas parado")
        
    def check_new_alerts(self):
        """Verifica se há novos alertas para exibir."""
        try:
            alerts_dir = os.path.join(LOG_DIRS['base'], 'alerts')
            if not os.path.exists(alerts_dir):
                return
                
            # Procurar por novos arquivos JSON de alerta
            for filename in os.listdir(alerts_dir):
                if not filename.endswith('.json'):
                    continue
                    
                json_path = os.path.join(alerts_dir, filename)
                if json_path in self.processed_alerts:
                    continue
                    
                # Carregar dados do alerta
                try:
                    with open(json_path, 'r') as f:
                        alert_data = json.load(f)
                        
                    # Verificar se há imagem correspondente
                    image_path = json_path.replace('.json', '.jpg')
                    if not os.path.exists(image_path):
                        continue
                        
                    # Carregar e processar imagem
                    frame = cv2.imread(image_path)
                    if frame is not None:
                        # Criar thumbnail
                        height, width = frame.shape[:2]
                        thumb_width = 100
                        thumb_height = int(height * (thumb_width / width))
                        thumbnail = cv2.resize(frame, (thumb_width, thumb_height))
                        
                        # Converter para QPixmap
                        rgb_image = cv2.cvtColor(thumbnail, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb_image.shape
                        bytes_per_line = ch * w
                        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qt_image)
                        
                        # Usar o tempo atual do vídeo para o alerta
                        self.video_tab.add_alert(pixmap, self.current_video_time)
                        self.processed_alerts.add(json_path)
                        logger.info(f"Alerta processado: {filename} em {self.current_video_time}ms")
                            
                except Exception as e:
                    logger.error(f"Erro ao processar alerta {filename}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Erro ao verificar novos alertas: {str(e)}")
        
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
                self.clear_alerts()  # Limpa alertas ao conectar
                self.setup_alert_timer()  # Inicia monitoramento
                self.toggle_play_pause()  # Inicia reprodução
            else:
                logger.error("Erro ao carregar o vídeo.")
                
    def disconnect_camera(self):
        """Desconecta a fonte de vídeo."""
        if self.cap:
            self.cap.release()
            self.cap = None
            self.video_tab.enable_controls(False)
            self.stop_alert_timer()  # Para monitoramento
            self.clear_alerts()  # Limpa alertas ao desconectar
            logger.info("Câmera desconectada")
                
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
        self.last_frame = frame.copy()  # Cache do frame para alertas
        self.video_tab.update_video_frame(frame)
        
        # Atualizar tempo
        self.current_video_time = int(self.cap.get(cv2.CAP_PROP_POS_MSEC))
        self.video_tab.update_time(self.current_video_time)
        
        # Incrementar contador e verificar necessidade de análise
        self.current_frame_count += 1
        
        # Limpar workers concluídos
        self.active_workers = [w for w in self.active_workers if not w.isFinished()]
        
        # Verificar se devemos analisar este frame
        frames_since_last = self.current_frame_count - self.last_analyzed_frame
        if (frames_since_last >= self.analysis_interval and 
            len(self.active_workers) < self.max_concurrent_workers):
            self.analyze_frame(frame)
            self.last_analyzed_frame = self.current_frame_count
            
    def analyze_frame(self, frame):
        """Inicia a análise de um frame."""
        try:
            frame_rgb = bgr_to_rgb(frame.copy())
            worker = AnalysisWorker(frame_rgb, self.current_frame_count)
            
            # Conectar sinais
            worker.analysis_complete.connect(self.handle_analysis_result)
            worker.analysis_error.connect(self.handle_analysis_error)
            
            # Adicionar à lista de workers ativos e iniciar
            self.active_workers.append(worker)
            worker.start()
            
        except Exception as e:
            logger.error(f"Erro ao criar worker: {str(e)}")
            
    def handle_analysis_result(self, result):
        """Processa o resultado da análise."""
        try:
            detections = result.get('detections', [])
            self.video_tab.add_log(f"Detecções encontradas: {len(detections)}")
            
            for det in detections:
                det_info = f"- Classe: {det.get('class_name', 'unknown')}, Confiança: {float(det['confidence']):.2f}"
                self.video_tab.add_log(det_info)
                    
        except Exception as e:
            logger.error(f"Erro ao processar resultado: {str(e)}")
            
    def handle_analysis_error(self, error_msg):
        """Trata erros na análise."""
        logger.error(f"Erro na análise do frame {self.current_frame_count}: {error_msg}")
        
    def jump_to_alert(self, item):
        """Salta para um momento específico do vídeo."""
        if not self.cap:
            return
            
        alert_time = item.data(0)
        if alert_time is None:
            logger.error("Tempo do alerta não encontrado")
            return
            
        target_time = max(0, alert_time - 1000)  # 1 segundo antes
        logger.info(f"Pulando para o tempo {target_time}ms")
        self.cap.set(cv2.CAP_PROP_POS_MSEC, target_time)
        
        # Atualizar frame
        ret, frame = self.cap.read()
        if ret:
            frame = resize_frame(frame)
            self.video_tab.update_video_frame(frame)
            self.current_video_time = target_time
            self.video_tab.update_time(target_time)
            
    def closeEvent(self, event):
        """Evento chamado ao fechar a aplicação."""
        self.disconnect_camera()
        event.accept()