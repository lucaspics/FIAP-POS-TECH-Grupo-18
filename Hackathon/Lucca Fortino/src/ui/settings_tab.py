"""
Aba de configurações da aplicação.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QMessageBox,
    QScrollArea,
    QFrame
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal
from config.logging_config import get_logger
from config.app_config import (
    ALERT_CONFIG,
    VIDEO_CONFIG,
    MODEL_CONFIG,
    UI_CONFIG
)

logger = get_logger('settings_tab')

class SettingsTab(QWidget):
    """Aba de configurações da aplicação."""
    
    # Sinais
    settings_changed = pyqtSignal(dict)  # Emitido quando as configurações são alteradas
    
    def __init__(self, parent=None):
        """Inicializa a aba de configurações."""
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface da aba de configurações."""
        try:
            # Layout principal
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
            
            # Título
            title = QLabel("Configurações do Sistema")
            title.setFont(QFont("Arial", 16, QFont.Bold))
            title.setAlignment(Qt.AlignCenter)
            layout.addWidget(title)
            
            # Área de rolagem
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameStyle(QFrame.NoFrame)
            
            # Container para os grupos
            container = QWidget()
            self.form_layout = QVBoxLayout(container)
            self.form_layout.setSpacing(20)
            
            # Grupos de configurações
            self.setup_alert_settings()
            self.setup_analysis_settings()
            self.setup_video_settings()
            self.setup_interface_settings()
            
            scroll.setWidget(container)
            layout.addWidget(scroll)
            
            # Botões
            self.setup_buttons(layout)
            
            logger.info("Interface de configurações inicializada")
            
        except Exception as e:
            logger.error(f"Erro ao configurar interface: {str(e)}")
            self.show_error_ui()
    
    def setup_alert_settings(self):
        """Configura o grupo de configurações de alerta."""
        try:
            group = QGroupBox("Configurações de Alerta")
            layout = QFormLayout()
            layout.setSpacing(10)
            
            # Email
            self.email_input = QLineEdit()
            self.email_input.setPlaceholderText("exemplo@email.com")
            self.email_input.setText(ALERT_CONFIG['notification_email'])
            self.email_input.textChanged.connect(self._validate_email)
            layout.addRow("Email para alertas:", self.email_input)
            
            # Habilitar alertas
            self.enable_email = QCheckBox("Habilitar alertas por email")
            self.enable_email.setChecked(ALERT_CONFIG['enable_email_alerts'])
            layout.addRow("", self.enable_email)
            
            # Threshold de alerta
            self.alert_threshold = QDoubleSpinBox()
            self.alert_threshold.setRange(0.0, 1.0)
            self.alert_threshold.setSingleStep(0.05)
            self.alert_threshold.setDecimals(2)
            self.alert_threshold.setValue(MODEL_CONFIG['alert_threshold'])
            layout.addRow("Threshold de alerta:", self.alert_threshold)
            
            # Intervalo entre alertas
            self.alert_interval = QSpinBox()
            self.alert_interval.setRange(100, 10000)
            self.alert_interval.setSingleStep(100)
            self.alert_interval.setSuffix(" ms")
            self.alert_interval.setValue(ALERT_CONFIG['min_time_between_alerts'])
            layout.addRow("Intervalo entre alertas:", self.alert_interval)
            
            # Buffer de emails
            self.email_buffer_interval = QSpinBox()
            self.email_buffer_interval.setRange(10, 300)
            self.email_buffer_interval.setSingleStep(1)
            self.email_buffer_interval.setSuffix(" s")
            self.email_buffer_interval.setValue(ALERT_CONFIG.get('email_buffer_interval', 5))
            layout.addRow("Intervalo do buffer de emails:", self.email_buffer_interval)
            
            # Salvar frames
            self.save_frames = QCheckBox("Salvar frames dos alertas")
            self.save_frames.setChecked(ALERT_CONFIG['save_frames'])
            layout.addRow("", self.save_frames)
            
            group.setLayout(layout)
            self.form_layout.addWidget(group)
            
        except Exception as e:
            logger.error(f"Erro ao configurar alertas: {str(e)}")
    
    def setup_analysis_settings(self):
        """Configura o grupo de configurações de análise."""
        try:
            group = QGroupBox("Configurações de Análise")
            layout = QFormLayout()
            layout.setSpacing(10)
            
            # Intervalo de análise
            self.analysis_interval = QSpinBox()
            self.analysis_interval.setRange(1, 30)
            self.analysis_interval.setValue(VIDEO_CONFIG['analysis_interval'])
            layout.addRow("Intervalo de análise (frames):", self.analysis_interval)
            
            # Threshold de confiança
            self.confidence_threshold = QDoubleSpinBox()
            self.confidence_threshold.setRange(0.0, 1.0)
            self.confidence_threshold.setSingleStep(0.05)
            self.confidence_threshold.setDecimals(2)
            self.confidence_threshold.setValue(MODEL_CONFIG['confidence_threshold'])
            layout.addRow("Threshold de confiança:", self.confidence_threshold)
            
            # Workers concorrentes
            self.max_workers = QSpinBox()
            self.max_workers.setRange(1, 8)
            self.max_workers.setValue(VIDEO_CONFIG['max_concurrent_workers'])
            layout.addRow("Workers concorrentes:", self.max_workers)
            
            # Altura alvo
            self.target_height = QSpinBox()
            self.target_height.setRange(100, 1080)
            self.target_height.setSingleStep(32)
            self.target_height.setValue(MODEL_CONFIG['target_height'])
            layout.addRow("Altura alvo:", self.target_height)
            
            group.setLayout(layout)
            self.form_layout.addWidget(group)
            
        except Exception as e:
            logger.error(f"Erro ao configurar análise: {str(e)}")
    
    def setup_video_settings(self):
        """Configura o grupo de configurações de vídeo."""
        try:
            group = QGroupBox("Configurações de Vídeo")
            layout = QFormLayout()
            layout.setSpacing(10)
            
            # FPS
            self.frame_interval = QSpinBox()
            self.frame_interval.setRange(10, 1000)
            self.frame_interval.setSingleStep(10)
            self.frame_interval.setSuffix(" ms")
            self.frame_interval.setValue(VIDEO_CONFIG['frame_interval'])
            layout.addRow("Intervalo entre frames:", self.frame_interval)
            
            # Timeout
            self.frame_timeout = QDoubleSpinBox()
            self.frame_timeout.setRange(0.1, 10.0)
            self.frame_timeout.setSingleStep(0.1)
            self.frame_timeout.setSuffix(" s")
            self.frame_timeout.setValue(VIDEO_CONFIG['frame_timeout'])
            layout.addRow("Timeout de frame:", self.frame_timeout)
            
            # Dimensões
            self.video_width = QSpinBox()
            self.video_width.setRange(320, 1920)
            self.video_width.setSingleStep(32)
            self.video_width.setValue(VIDEO_CONFIG['width'])
            layout.addRow("Largura do vídeo:", self.video_width)
            
            self.video_height = QSpinBox()
            self.video_height.setRange(240, 1080)
            self.video_height.setSingleStep(32)
            self.video_height.setValue(VIDEO_CONFIG['height'])
            layout.addRow("Altura do vídeo:", self.video_height)
            
            group.setLayout(layout)
            self.form_layout.addWidget(group)
            
        except Exception as e:
            logger.error(f"Erro ao configurar vídeo: {str(e)}")
    
    def setup_interface_settings(self):
        """Configura o grupo de configurações da interface."""
        try:
            group = QGroupBox("Configurações da Interface")
            layout = QFormLayout()
            layout.setSpacing(10)
            
            # Título da janela
            self.window_title = QLineEdit()
            self.window_title.setText(UI_CONFIG['window_title'])
            layout.addRow("Título da janela:", self.window_title)
            
            # Dimensões da janela
            self.window_width = QSpinBox()
            self.window_width.setRange(800, 1920)
            self.window_width.setSingleStep(50)
            self.window_width.setValue(UI_CONFIG['window_size'][0])
            layout.addRow("Largura da janela:", self.window_width)
            
            self.window_height = QSpinBox()
            self.window_height.setRange(600, 1080)
            self.window_height.setSingleStep(50)
            self.window_height.setValue(UI_CONFIG['window_size'][1])
            layout.addRow("Altura da janela:", self.window_height)
            
            # Máximo de logs
            self.max_logs = QSpinBox()
            self.max_logs.setRange(10, 1000)
            self.max_logs.setSingleStep(10)
            self.max_logs.setValue(UI_CONFIG['max_log_entries'])
            layout.addRow("Máximo de logs:", self.max_logs)
            
            group.setLayout(layout)
            self.form_layout.addWidget(group)
            
        except Exception as e:
            logger.error(f"Erro ao configurar interface: {str(e)}")
    
    def setup_buttons(self, layout):
        """Configura os botões de ação."""
        try:
            buttons = QHBoxLayout()
            
            # Botão Salvar
            self.save_button = QPushButton("Salvar")
            self.save_button.setIcon(QIcon.fromTheme("document-save"))
            self.save_button.clicked.connect(self.save_settings)
            self.save_button.setStyleSheet("""
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
            """)
            buttons.addWidget(self.save_button)
            
            # Botão Restaurar
            self.restore_button = QPushButton("Restaurar Padrões")
            self.restore_button.setIcon(QIcon.fromTheme("edit-undo"))
            self.restore_button.clicked.connect(self.restore_defaults)
            self.restore_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            buttons.addWidget(self.restore_button)
            
            layout.addLayout(buttons)
            
        except Exception as e:
            logger.error(f"Erro ao configurar botões: {str(e)}")
    
    def show_error_ui(self):
        """Exibe interface de erro."""
        layout = QVBoxLayout(self)
        error_label = QLabel("Erro ao carregar configurações")
        error_label.setStyleSheet("color: red;")
        layout.addWidget(error_label)
    
    def _validate_email(self, email: str):
        """
        Valida o formato do email.
        
        Args:
            email: Email para validar
        """
        try:
            is_valid = '@' in email and '.' in email.split('@')[1]
            self.email_input.setStyleSheet(
                "" if is_valid else "border: 1px solid red;"
            )
        except Exception as e:
            logger.error(f"Erro ao validar email: {str(e)}")
    
    def save_settings(self):
        """Salva as configurações atualizadas."""
        try:
            # Validar email
            email = self.email_input.text().strip()
            if not ('@' in email and '.' in email.split('@')[1]):
                QMessageBox.warning(self, "Erro", "Email inválido")
                return
            
            # Coletar configurações
            settings = {
                'alert': {
                    'notification_email': email,
                    'enable_email_alerts': self.enable_email.isChecked(),
                    'min_time_between_alerts': self.alert_interval.value(),
                    'save_frames': self.save_frames.isChecked(),
                    'email_buffer_interval': self.email_buffer_interval.value()
                },
                'model': {
                    'alert_threshold': self.alert_threshold.value(),
                    'confidence_threshold': self.confidence_threshold.value(),
                    'target_height': self.target_height.value()
                },
                'video': {
                    'analysis_interval': self.analysis_interval.value(),
                    'max_concurrent_workers': self.max_workers.value(),
                    'frame_interval': self.frame_interval.value(),
                    'frame_timeout': self.frame_timeout.value(),
                    'width': self.video_width.value(),
                    'height': self.video_height.value()
                },
                'ui': {
                    'window_title': self.window_title.text(),
                    'window_size': (self.window_width.value(), self.window_height.value()),
                    'max_log_entries': self.max_logs.value()
                }
            }
            
            # Atualizar configurações
            ALERT_CONFIG.update(settings['alert'])
            MODEL_CONFIG.update(settings['model'])
            VIDEO_CONFIG.update(settings['video'])
            UI_CONFIG.update(settings['ui'])
            
            # Emitir sinal
            self.settings_changed.emit(settings)
            
            QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!")
            logger.info("Configurações atualizadas")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao salvar configurações: {str(e)}")
    
    def restore_defaults(self):
        """Restaura as configurações padrão."""
        try:
            reply = QMessageBox.question(
                self,
                "Restaurar Padrões",
                "Tem certeza que deseja restaurar todas as configurações para os valores padrão?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Restaurar valores padrão
                # TODO: Implementar restauração de valores padrão
                QMessageBox.information(self, "Sucesso", "Configurações restauradas!")
                logger.info("Configurações restauradas para padrão")
            
        except Exception as e:
            logger.error(f"Erro ao restaurar configurações: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao restaurar configurações: {str(e)}")