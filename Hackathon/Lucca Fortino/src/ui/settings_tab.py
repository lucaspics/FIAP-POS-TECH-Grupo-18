from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from config.logging_config import logger
from config.app_config import DEFAULT_EMAIL, DEFAULT_ANALYSIS_INTERVAL

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
        
        # Email
        self.email_label = QLabel("Email para alertas:")
        self.email_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.layout.addWidget(self.email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Digite o email para alertas")
        self.email_input.setText(DEFAULT_EMAIL)
        self.layout.addWidget(self.email_input)
        
        # Intervalo de Análise
        self.interval_label = QLabel("Intervalo de análise de frames:")
        self.interval_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.layout.addWidget(self.interval_label)
        
        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText("Intervalo de análise de frames (em frames)")
        self.interval_input.setText(str(DEFAULT_ANALYSIS_INTERVAL))
        self.layout.addWidget(self.interval_input)
        
        # Botão Salvar
        self.save_button = QPushButton("Salvar Configurações")
        self.save_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")
        self.save_button.clicked.connect(self.save_settings)
        self.layout.addWidget(self.save_button)
        
    def save_settings(self):
        """Salva as configurações atualizadas."""
        try:
            # Validar e salvar intervalo de análise
            new_interval = int(self.interval_input.text())
            if new_interval > 0:
                if self.parent:
                    self.parent.analysis_interval = new_interval
                self.interval_input.setStyleSheet("")
                logger.info(f"Intervalo de análise atualizado para: {new_interval}")
            else:
                raise ValueError("Intervalo deve ser maior que 0")
                
        except ValueError as e:
            logger.error(f"Erro ao salvar configurações: {str(e)}")
            self.interval_input.setStyleSheet("border: 1px solid red;")
            return
        
        # Salvar email
        new_email = self.email_input.text().strip()
        if new_email:
            logger.info(f"Email atualizado para: {new_email}")
        
        # Reiniciar contador de frames se necessário
        if self.parent:
            self.parent.current_frame_count = 0
            logger.info("Contador de frames reiniciado")