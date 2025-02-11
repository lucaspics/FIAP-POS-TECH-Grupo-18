from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QSpinBox, QFormLayout, QGroupBox
)
from PyQt5.QtGui import QFont, QDoubleValidator
from PyQt5.QtCore import Qt
from config.logging_config import logger
from config.app_config import (
    ALERT_CONFIG,
    VIDEO_CONFIG,
    MODEL_CONFIG
)

class SettingsTab(QWidget):
    """Aba de configurações da aplicação."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface da aba de configurações."""
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        
        # Título
        self.settings_title = QLabel("Configurações do Sistema")
        self.settings_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.layout.addWidget(self.settings_title)
        
        # Configurações de Alerta
        self.setup_alert_settings()
        
        # Configurações de Análise
        self.setup_analysis_settings()
        
        # Botão Salvar
        self.save_button = QPushButton("Salvar Configurações")
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)

    def setup_alert_settings(self):
        """Configura o grupo de configurações de alerta."""
        alert_group = QGroupBox("Configurações de Alerta")
        alert_layout = QFormLayout()
        
        # Email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Digite o email para alertas")
        self.email_input.setText(ALERT_CONFIG['notification_email'])
        alert_layout.addRow("Email para alertas:", self.email_input)
        
        # Habilitar alertas por email
        self.enable_email = QCheckBox("Habilitar alertas por email")
        self.enable_email.setChecked(ALERT_CONFIG['enable_email_alerts'])
        alert_layout.addRow("", self.enable_email)
        
        # Threshold de alerta
        self.alert_threshold = QLineEdit()
        self.alert_threshold.setValidator(QDoubleValidator(0.0, 1.0, 2))
        self.alert_threshold.setText(str(MODEL_CONFIG['alert_threshold']))
        alert_layout.addRow("Threshold de alerta:", self.alert_threshold)
        
        alert_group.setLayout(alert_layout)
        self.layout.addWidget(alert_group)

    def setup_analysis_settings(self):
        """Configura o grupo de configurações de análise."""
        analysis_group = QGroupBox("Configurações de Análise")
        analysis_layout = QFormLayout()
        
        # Intervalo de análise
        self.interval_input = QSpinBox()
        self.interval_input.setRange(1, 30)
        self.interval_input.setValue(VIDEO_CONFIG['analysis_interval'])
        analysis_layout.addRow("Intervalo de análise (frames):", self.interval_input)
        
        # Threshold de confiança
        self.confidence_threshold = QLineEdit()
        self.confidence_threshold.setValidator(QDoubleValidator(0.0, 1.0, 2))
        self.confidence_threshold.setText(str(MODEL_CONFIG['confidence_threshold']))
        analysis_layout.addRow("Threshold de confiança:", self.confidence_threshold)
        
        analysis_group.setLayout(analysis_layout)
        self.layout.addWidget(analysis_group)
        
    def save_settings(self):
        """Salva as configurações atualizadas."""
        try:
            # Validar e salvar intervalo de análise
            new_interval = self.interval_input.value()
            if new_interval > 0:
                if self.parent:
                    self.parent.analysis_interval = new_interval
                VIDEO_CONFIG['analysis_interval'] = new_interval
                logger.info(f"Intervalo de análise atualizado para: {new_interval}")
            
            # Validar e salvar email
            new_email = self.email_input.text().strip()
            if '@' in new_email:
                ALERT_CONFIG['notification_email'] = new_email
                logger.info(f"Email atualizado para: {new_email}")
            else:
                self.email_input.setStyleSheet("border: 1px solid red;")
                return
                
            # Salvar estado dos alertas por email
            ALERT_CONFIG['enable_email_alerts'] = self.enable_email.isChecked()
            
            # Salvar thresholds
            try:
                new_alert_threshold = float(self.alert_threshold.text())
                if 0 <= new_alert_threshold <= 1:
                    MODEL_CONFIG['alert_threshold'] = new_alert_threshold
                else:
                    raise ValueError("Alert threshold deve estar entre 0 e 1")
                    
                new_confidence = float(self.confidence_threshold.text())
                if 0 <= new_confidence <= 1:
                    MODEL_CONFIG['confidence_threshold'] = new_confidence
                else:
                    raise ValueError("Confidence threshold deve estar entre 0 e 1")
                    
            except ValueError as e:
                logger.error(f"Erro ao salvar thresholds: {str(e)}")
                self.alert_threshold.setStyleSheet("border: 1px solid red;")
                self.confidence_threshold.setStyleSheet("border: 1px solid red;")
                return
            
            # Limpar estilos de erro
            self.email_input.setStyleSheet("")
            self.alert_threshold.setStyleSheet("")
            self.confidence_threshold.setStyleSheet("")
            
            # Reiniciar contador de frames se necessário
            if self.parent:
                self.parent.current_frame_count = 0
                logger.info("Contador de frames reiniciado")
                
            logger.info("Configurações salvas com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {str(e)}")