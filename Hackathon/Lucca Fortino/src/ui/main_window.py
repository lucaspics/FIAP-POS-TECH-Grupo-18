import os
import cv2
import json
import shutil
import platform
import time
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QTabWidget, QFileDialog, QMessageBox
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
from ui.source_dialog import VideoSourceDialog, CameraBackend
from utils.video_utils import resize_frame, bgr_to_rgb

class CameraManager:
    """Gerenciador de recursos da câmera."""
    
    def __init__(self):
        self.cap = None
        self.camera_id = None
        self.last_frame_time = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        self.frame_timeout = 2.0  # segundos
        
    def is_connection_stale(self):
        """Verifica se a conexão está estagnada."""
        if self.last_frame_time is None:
            return False
        return time.time() - self.last_frame_time > self.frame_timeout
    
    def try_reconnect(self):
        """Tenta reconectar à câmera."""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            return False
            
        logger.info(f"Tentativa de reconexão {self.reconnect_attempts + 1}/{self.max_reconnect_attempts}")
        self.release()
        
        # Tenta cada backend disponível
        backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, None] if platform.system() == 'Windows' else [None]
        
        for backend in backends:
            cap, error = CameraBackend.try_backend(self.camera_id, backend)
            if cap:
                self.cap = cap
                self.last_frame_time = time.time()
                logger.info(f"Reconexão bem sucedida usando backend {backend if backend else 'padrão'}")
                return True
        
        self.reconnect_attempts += 1
        return False
    
    def read_frame(self):
        """Lê um frame da câmera com verificações de estado."""
        if not self.cap or not self.cap.isOpened():
            return False, None
            
        ret, frame = self.cap.read()
        if ret and frame is not None:
            self.last_frame_time = time.time()
            self.reconnect_attempts = 0  # Reset contador de tentativas após sucesso
            return True, frame
            
        if self.is_connection_stale():
            if not self.try_reconnect():
                return False, None
        
        return False, None
    
    def release(self):
        """Libera os recursos da câmera."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.last_frame_time = None

class SecurityCameraApp(QWidget):
    """Janela principal da aplicação."""
    
    def __init__(self):
        super().__init__()
        self.init_variables()
        self.setup_ui()
        self.clear_alerts()
        
    def init_variables(self):
        """Inicializa as variáveis de controle."""
        self.video_path = None
        self.camera_manager = CameraManager()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.is_playing = False
        self.is_camera = False
        
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
        
    def connect_camera(self):
        """Conecta à fonte de vídeo."""
        dialog = VideoSourceDialog(self)
        if dialog.exec_():
            if dialog.source_type == "camera":
                camera_id = dialog.get_camera_id()
                logger.info(f"Tentando conectar à câmera {camera_id}")
                
                try:
                    self.camera_manager.camera_id = camera_id
                    backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW, None] if platform.system() == 'Windows' else [None]
                    
                    for backend in backends:
                        cap, error = CameraBackend.try_backend(camera_id, backend)
                        if cap:
                            self.camera_manager.cap = cap
                            self.camera_manager.last_frame_time = time.time()
                            self.is_camera = True
                            self.video_tab.enable_controls(True)
                            logger.info(f"Câmera {camera_id} conectada com sucesso usando backend {backend if backend else 'padrão'}")
                            self.clear_alerts()
                            self.setup_alert_timer()
                            self.toggle_play_pause()
                            return
                    
                    raise Exception("Não foi possível conectar à câmera com nenhum backend disponível")
                    
                except Exception as e:
                    logger.error(f"Erro ao conectar à câmera {camera_id}: {str(e)}")
                    self.camera_manager.release()
                    error_msg = "Não foi possível abrir a câmera"
                    error_msg += "\n\nVerifique:\n" \
                               "1. Se a câmera está conectada\n" \
                               "2. Se outro aplicativo não está usando a câmera\n" \
                               "3. As configurações de privacidade do Windows"
                    QMessageBox.critical(self, "Erro", error_msg)
                    
            else:  # Modo vídeo
                options = QFileDialog.Options()
                self.video_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Selecione o vídeo",
                    "",
                    "Arquivos de Vídeo (*.mp4 *.avi *.mov)",
                    options=options
                )
                
                if self.video_path:
                    self.camera_manager.cap = cv2.VideoCapture(self.video_path)
                    self.is_camera = False
                    if self.camera_manager.cap.isOpened():
                        self.video_tab.enable_controls(True)
                        logger.info(f"Vídeo carregado: {self.video_path}")
                        self.clear_alerts()
                        self.setup_alert_timer()
                        self.toggle_play_pause()
                    else:
                        logger.error("Erro ao carregar o vídeo.")
                        QMessageBox.critical(self, "Erro", "Não foi possível carregar o vídeo.")
                        
    def disconnect_camera(self):
        """Desconecta a fonte de vídeo."""
        self.camera_manager.release()
        self.video_path = None
        self.is_camera = False
        self.video_tab.enable_controls(False)
        self.stop_alert_timer()
        self.clear_alerts()
        logger.info("Fonte de vídeo desconectada")
        
    def update_frame(self):
        """Atualiza o frame atual do vídeo."""
        if not self.camera_manager.cap:
            return
            
        if self.is_camera:
            ret, frame = self.camera_manager.read_frame()
        else:
            ret, frame = self.camera_manager.cap.read()
            
        if not ret:
            if self.is_camera:
                logger.error("Erro ao ler frame da câmera")
                self.disconnect_camera()
                QMessageBox.warning(self, "Aviso", "Conexão com a câmera foi perdida.")
            else:
                logger.info("Fim do vídeo.")
                self.timer.stop()
                self.is_playing = False
                self.video_tab.play_pause_button.setText("Play")
            return
            
        # Processar frame
        frame = resize_frame(frame)
        self.last_frame = frame.copy()
        self.video_tab.update_video_frame(frame)
        
        # Atualizar tempo
        if not self.is_camera:
            self.current_video_time = int(self.camera_manager.cap.get(cv2.CAP_PROP_POS_MSEC))
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
        if not self.camera_manager.cap or self.is_camera:
            return
            
        current_frame = self.camera_manager.cap.get(cv2.CAP_PROP_POS_FRAMES)
        fps = self.camera_manager.cap.get(cv2.CAP_PROP_FPS)
        target_frame = max(0, current_frame - (fps * 5))  # 5 segundos
        self.camera_manager.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
    def forward_video(self):
        """Avança o vídeo em 5 segundos."""
        if not self.camera_manager.cap or self.is_camera:
            return
            
        current_frame = self.camera_manager.cap.get(cv2.CAP_PROP_POS_FRAMES)
        fps = self.camera_manager.cap.get(cv2.CAP_PROP_FPS)
        total_frames = self.camera_manager.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        target_frame = min(total_frames - 1, current_frame + (fps * 5))  # 5 segundos
        self.camera_manager.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
        
    def analyze_frame(self, frame):
        """Inicia a análise de um frame."""
        try:
            frame_rgb = bgr_to_rgb(frame.copy())
            worker = AnalysisWorker(
                frame_rgb,
                self.current_frame_count,
                self.current_video_time
            )
            
            worker.analysis_complete.connect(self.handle_analysis_result)
            worker.analysis_error.connect(self.handle_analysis_error)
            
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
        
    def clear_alerts(self):
        """Limpa todos os arquivos de alerta."""
        try:
            alerts_dir = os.path.join(LOG_DIRS['base'], 'alerts')
            if os.path.exists(alerts_dir):
                shutil.rmtree(alerts_dir)
            os.makedirs(alerts_dir, exist_ok=True)
            logger.info("Diretório de alertas limpo")
            
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
        self.alert_timer.start(1000)
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
                
            # Coletar e ordenar alertas por timestamp
            alert_files = []
            for filename in os.listdir(alerts_dir):
                if not filename.endswith('.json'):
                    continue
                    
                json_path = os.path.join(alerts_dir, filename)
                if json_path in self.processed_alerts:
                    continue
                    
                try:
                    with open(json_path, 'r') as f:
                        alert_data = json.load(f)
                    timestamp = datetime.fromisoformat(alert_data['timestamp'])
                    alert_files.append((timestamp, json_path, alert_data))
                except Exception as e:
                    logger.error(f"Erro ao ler alerta {filename}: {str(e)}")
                    continue
            
            # Ordenar por timestamp
            alert_files.sort(key=lambda x: x[0])
            
            # Processar alertas ordenados
            for _, json_path, alert_data in alert_files:
                try:
                    # Extrair informações de detecção
                    detections = alert_data.get('detections', [])
                    if not detections:
                        continue
                        
                    # Usar a detecção com maior confiança
                    best_detection = max(detections, key=lambda x: x.get('confidence', 0))
                    class_name = best_detection.get('class_name', 'unknown')
                    confidence = best_detection.get('confidence', 0.0)
                        
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
                        
                        # Usar o tempo relativo do vídeo
                        alert_time_ms = alert_data.get('video_time', 0)
                        
                        # Adicionar alerta com o timestamp exato da detecção
                        self.video_tab.add_alert(
                            pixmap=pixmap,
                            time_ms=alert_time_ms,
                            class_name=class_name,
                            confidence=confidence
                        )
                        self.processed_alerts.add(json_path)
                        logger.info(f"Alerta processado: {os.path.basename(json_path)} em {alert_time_ms}ms - {class_name} ({confidence:.2%})")
                            
                except Exception as e:
                    logger.error(f"Erro ao processar alerta {os.path.basename(json_path)}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Erro ao verificar novos alertas: {str(e)}")
            
    def jump_to_alert(self, item):
        """Salta para um momento específico do vídeo."""
        if not self.camera_manager.cap or self.is_camera:
            return
            
        alert_time = item.data(0)
        if alert_time is None:
            logger.error("Tempo do alerta não encontrado")
            return
            
        # Primeiro pausar o vídeo
        if self.is_playing:
            self.toggle_play_pause()
            
        # Garantir que o timer está parado
        self.timer.stop()
        
        # Posicionar o vídeo no tempo do alerta
        logger.info(f"Pulando para o tempo {alert_time}ms")
        self.camera_manager.cap.set(cv2.CAP_PROP_POS_MSEC, alert_time)
        
        # Ler alguns frames para garantir que estamos no frame correto
        for _ in range(3):
            ret, frame = self.camera_manager.cap.read()
            if not ret:
                break
        
        if ret and frame is not None:
            frame = resize_frame(frame)
            self.video_tab.update_video_frame(frame)
            
            # Usar o tempo do alerta
            self.current_video_time = alert_time
            self.video_tab.update_time(alert_time)
            logger.info(f"Frame atualizado para o tempo {alert_time}ms")
        else:
            logger.error("Não foi possível atualizar o frame")
            
    def closeEvent(self, event):
        """Evento chamado ao fechar a aplicação."""
        self.disconnect_camera()
        event.accept()