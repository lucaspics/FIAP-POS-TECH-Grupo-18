"""
Janela principal da aplicação VisionGuard.
"""

import os
import cv2
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QMessageBox,
    QFileDialog,
    QStatusBar
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
from config.logging_config import get_logger
from config.app_config import (
    MODEL_CONFIG,
    VIDEO_CONFIG,
    ALERT_CONFIG,
    LOG_DIRS,
    UI_CONFIG
)
from .camera_manager import CameraManager
from .analysis_manager import AnalysisManager
from .alert_view import AlertView
from .video_tab import VideoTab
from .settings_tab import SettingsTab
from .source_dialog import VideoSourceDialog
from .about_tab import AboutTab
from core.video_utils import resize_frame, bgr_to_rgb

logger = get_logger('main_window')

class SecurityCameraApp(QMainWindow):
    """Janela principal da aplicação."""
    
    def __init__(self):
        """Inicializa a aplicação."""
        super().__init__()
        self.init_managers()
        self.setup_ui()
        self.setup_connections()
        self.setup_timers()
        
    def init_managers(self):
        """Inicializa os gerenciadores."""
        try:
            # Gerenciador de câmera
            self.camera_manager = CameraManager()
            
            # Gerenciador de análise
            self.analysis_manager = AnalysisManager()
            if not self.analysis_manager.initialize(
                MODEL_CONFIG['path'],
                LOG_DIRS['alerts']
            ):
                raise RuntimeError("Falha ao inicializar sistema de análise")
            
            logger.info("Gerenciadores inicializados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar gerenciadores: {str(e)}")
            QMessageBox.critical(self, "Erro", "Falha ao inicializar sistema")
            raise
    
    def setup_ui(self):
        """Configura a interface do usuário."""
        try:
            # Configurações da janela
            self.setWindowTitle(UI_CONFIG['window_title'])
            self.setGeometry(100, 100, *UI_CONFIG['window_size'])
            
            # Widget central
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # Layout principal
            main_layout = QHBoxLayout(central_widget)
            
            # Área principal (vídeo + configurações)
            main_area = QWidget()
            main_layout.addWidget(main_area, stretch=2)
            
            main_area_layout = QVBoxLayout(main_area)
            main_area_layout.setContentsMargins(0, 0, 0, 0)
            
            # Tabs
            self.tabs = QTabWidget()
            main_area_layout.addWidget(self.tabs)
            
            # Aba de vídeo
            self.video_tab = VideoTab()
            self.tabs.addTab(self.video_tab, "Vídeo")
            
            # Aba de configurações
            self.settings_tab = SettingsTab()
            self.tabs.addTab(self.settings_tab, "Configurações")
            
            # Aba sobre desenvolvedores
            self.about_tab = AboutTab()
            self.tabs.addTab(self.about_tab, "Desenvolvido por")
            
            # Área de alertas
            self.alert_view = AlertView()
            main_layout.addWidget(self.alert_view, stretch=1)
            
            # Barra de status
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            
            logger.info("Interface inicializada com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao configurar interface: {str(e)}")
            QMessageBox.critical(self, "Erro", "Falha ao configurar interface")
            raise
    
    def setup_connections(self):
        """Configura as conexões de sinais."""
        try:
            # Conexões do VideoTab
            self.video_tab.connect_clicked.connect(self.connect_camera)
            self.video_tab.disconnect_clicked.connect(self.disconnect_camera)
            self.video_tab.play_pause_clicked.connect(self.toggle_play_pause)
            
            # Conexões do AnalysisManager
            self.analysis_manager.analysis_complete.connect(self.handle_analysis_result)
            self.analysis_manager.analysis_error.connect(self.handle_analysis_error)
            self.analysis_manager.metrics_update.connect(self.update_metrics)
            
            # Conexões do AlertView
            self.alert_view.jump_to_time.connect(self.jump_to_time)
            self.alert_view.alert_deleted.connect(self.delete_alert)
            
            logger.info("Conexões configuradas com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao configurar conexões: {str(e)}")
    
    def setup_timers(self):
        """Configura os timers."""
        try:
            # Timer de atualização de frame
            self.frame_timer = QTimer(self)
            self.frame_timer.timeout.connect(self.update_frame)
            
            # Timer de atualização de status
            self.status_timer = QTimer(self)
            self.status_timer.timeout.connect(self.update_status)
            self.status_timer.start(1000)  # Atualizar a cada segundo
            
            logger.info("Timers configurados com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao configurar timers: {str(e)}")
    
    def connect_camera(self):
        """Conecta à fonte de vídeo."""
        try:
            dialog = VideoSourceDialog(self)
            if dialog.exec_():
                if dialog.source_type == "camera":
                    self._connect_to_camera(dialog.get_camera_id())
                else:
                    self._connect_to_video()
                    
        except Exception as e:
            logger.error(f"Erro ao conectar fonte de vídeo: {str(e)}")
            QMessageBox.critical(self, "Erro", str(e))
    
    def _connect_to_camera(self, camera_id):
        """Conecta a uma câmera."""
        try:
            self.camera_manager.camera_id = camera_id
            self.camera_manager.is_camera = True
            
            if not self.camera_manager.try_reconnect():
                raise RuntimeError("Não foi possível conectar à câmera")
            
            self.video_tab.enable_controls(True)
            self.alert_view.clear_all()
            self.toggle_play_pause()
            
            logger.info(f"Câmera {camera_id} conectada com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao conectar câmera: {str(e)}")
            self.disconnect_camera()
            raise
    
    def _connect_to_video(self):
        """Conecta a um arquivo de vídeo."""
        try:
            options = QFileDialog.Options()
            video_path, _ = QFileDialog.getOpenFileName(
                self,
                "Selecione o vídeo",
                "",
                "Arquivos de Vídeo (*.mp4 *.avi *.mov)",
                options=options
            )
            
            if video_path:
                self.camera_manager.cap = cv2.VideoCapture(video_path)
                self.camera_manager.is_camera = False
                self.camera_manager.video_path = video_path
                
                if not self.camera_manager.cap.isOpened():
                    raise RuntimeError("Não foi possível abrir o vídeo")
                
                self.video_tab.enable_controls(True)
                self.alert_view.clear_all()
                self.toggle_play_pause()
                
                logger.info(f"Vídeo carregado: {video_path}")
                
        except Exception as e:
            logger.error(f"Erro ao carregar vídeo: {str(e)}")
            self.disconnect_camera()
            raise
    
    def disconnect_camera(self):
        """Desconecta a fonte de vídeo."""
        try:
            self.frame_timer.stop()
            self.camera_manager.release()
            self.video_tab.enable_controls(False)
            self.video_tab.clear_display()
            self.alert_view.clear_all()
            
            logger.info("Fonte de vídeo desconectada")
            
        except Exception as e:
            logger.error(f"Erro ao desconectar: {str(e)}")
    
    def toggle_play_pause(self):
        """Alterna entre play e pause."""
        try:
            if self.frame_timer.isActive():
                self.frame_timer.stop()
                self.video_tab.set_playing(False)
            else:
                self.frame_timer.start(VIDEO_CONFIG['frame_interval'])
                self.video_tab.set_playing(True)
                
        except Exception as e:
            logger.error(f"Erro ao alternar play/pause: {str(e)}")
    
    def update_frame(self):
        """Atualiza o frame atual."""
        try:
            if self.camera_manager.is_camera:
                ret, frame = self.camera_manager.read_frame()
            else:
                ret, frame = self.camera_manager.cap.read()
                
            if not ret:
                if self.camera_manager.is_camera:
                    logger.error("Conexão com a câmera perdida")
                    self.disconnect_camera()
                    QMessageBox.warning(self, "Aviso", "Conexão com a câmera foi perdida")
                else:
                    logger.info("Fim do vídeo")
                    self.frame_timer.stop()
                    self.video_tab.set_playing(False)
                    # Reiniciar o vídeo
                    self.camera_manager.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.video_tab.update_time(0)
                return
            
            # Processar frame
            frame = resize_frame(frame, target_height=MODEL_CONFIG['target_height'])
            if frame is None:
                return
                
            # Atualizar interface
            self.video_tab.update_frame(frame)
            
            # Atualizar tempo do vídeo
            if not self.camera_manager.is_camera:
                video_time = self.camera_manager.get_current_time()
                self.video_tab.update_time(video_time)
            
            # Verificar se é o último frame do vídeo
            is_last_frame = False
            if not self.camera_manager.is_camera:
                total_frames = int(self.camera_manager.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                current_frame = int(self.camera_manager.cap.get(cv2.CAP_PROP_POS_FRAMES))
                is_last_frame = current_frame >= total_frames - 1

            # Analisar frame
            self.analysis_manager.process_frame(
                frame,
                self.camera_manager.get_current_time(),
                is_last_frame=is_last_frame
            )
            
        except Exception as e:
            logger.error(f"Erro ao atualizar frame: {str(e)}")
    
    def handle_analysis_result(self, result):
        """Processa o resultado da análise."""
        try:
            # Atualizar logs
            self.video_tab.add_log(
                f"Detecções: {len(result.get('detections', []))} | "
                f"Tempo: {result.get('analysis_time', 0):.3f}s"
            )
            
            # Verificar alertas
            if result.get('alert_triggered'):
                self.alert_view.add_alert(result)
                
        except Exception as e:
            logger.error(f"Erro ao processar resultado: {str(e)}")
    
    def handle_analysis_error(self, error_msg):
        """Trata erros na análise."""
        logger.error(f"Erro na análise: {error_msg}")
        self.status_bar.showMessage(f"Erro: {error_msg}", 5000)
    
    def update_metrics(self, metrics):
        """Atualiza métricas na interface."""
        try:
            fps = metrics.get('fps', 0)
            detections = metrics.get('detection_count', 0)
            self.status_bar.showMessage(
                f"FPS: {fps:.1f} | Detecções: {detections} | "
                f"Workers: {len(self.analysis_manager.active_workers)}"
            )
        except Exception as e:
            logger.error(f"Erro ao atualizar métricas: {str(e)}")
    
    def update_status(self):
        """Atualiza a barra de status."""
        try:
            if hasattr(self, 'camera_manager') and hasattr(self, 'analysis_manager'):
                if self.camera_manager.cap and self.camera_manager.cap.isOpened():
                    stats = self.analysis_manager.get_stats()
                    self.status_bar.showMessage(
                        f"Fonte: {'Câmera' if self.camera_manager.is_camera else 'Vídeo'} | "
                        f"Frames: {stats['total_frames']} | "
                        f"Análises: {stats['analyzed_frames']} | "
                        f"Detecções: {stats['total_detections']}"
                    )
        except Exception as e:
            logger.error(f"Erro ao atualizar status: {str(e)}")
    
    def jump_to_time(self, time_ms):
        """Salta para um momento específico do vídeo."""
        try:
            if not self.camera_manager.is_camera:
                if self.camera_manager.set_video_pos(time_ms):
                    self.video_tab.update_time(time_ms)
                    # Forçar atualização do frame
                    self.update_frame()
                    
        except Exception as e:
            logger.error(f"Erro ao pular para tempo {time_ms}ms: {str(e)}")
    
    def delete_alert(self, alert_id):
        """Deleta um alerta."""
        try:
            # Implementar deleção do alerta
            logger.info(f"Alerta deletado: {alert_id}")
            
        except Exception as e:
            logger.error(f"Erro ao deletar alerta: {str(e)}")
    
    def closeEvent(self, event):
        """Evento chamado ao fechar a aplicação."""
        try:
            self.disconnect_camera()
            self.analysis_manager.cleanup()
            event.accept()
            
        except Exception as e:
            logger.error(f"Erro ao fechar aplicação: {str(e)}")
            event.accept()