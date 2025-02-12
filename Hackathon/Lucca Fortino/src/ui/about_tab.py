"""
Aba 'Desenvolvido por' da aplicação VisionGuard.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QFrame
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QFont, QCursor
from config.developers_config import DEVELOPERS

class DeveloperCard(QFrame):
    """Card que exibe informações de um desenvolvedor."""
    
    def __init__(self, developer):
        super().__init__()
        self.developer = developer
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface do card."""
        # Estilo do card
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            DeveloperCard {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
            QLabel {
                padding: 2px;
            }
            QLabel[isLink="true"] {
                color: #0066cc;
                text-decoration: underline;
            }
            QLabel[isLink="true"]:hover {
                color: #003399;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        
        # Nome
        name_label = QLabel(self.developer['name'])
        name_font = QFont()
        name_font.setBold(True)
        name_font.setPointSize(12)
        name_label.setFont(name_font)
        layout.addWidget(name_label)
        
        # RA
        ra_label = QLabel(f"RA: {self.developer['ra']}")
        layout.addWidget(ra_label)
        
        # LinkedIn
        linkedin_label = QLabel(f"LinkedIn: {self.developer['linkedin']}")
        linkedin_label.setProperty("isLink", True)
        linkedin_label.setCursor(QCursor(Qt.PointingHandCursor))
        linkedin_label.mousePressEvent = lambda _: self.open_linkedin()
        layout.addWidget(linkedin_label)
        
    def open_linkedin(self):
        """Abre o perfil do LinkedIn do desenvolvedor."""
        url = QUrl(self.developer['linkedin'])
        QDesktopServices.openUrl(url)

class AboutTab(QWidget):
    """Aba que exibe informações sobre os desenvolvedores."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Configura a interface da aba."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignTop)
        
        # Título do curso
        course_title = QLabel("FIAP - AI para devs - 2024 - 1IADT - Grupo 18")
        course_font = QFont()
        course_font.setBold(True)
        course_font.setPointSize(14)
        course_title.setFont(course_font)
        course_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(course_title)
        
        # Título desenvolvedores
        dev_title = QLabel("Desenvolvedores")
        dev_font = QFont()
        dev_font.setBold(True)
        dev_font.setPointSize(12)
        dev_title.setFont(dev_font)
        dev_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(dev_title)
        
        # Área de scroll para os cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Container para os cards
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignTop)
        
        # Adiciona um card para cada desenvolvedor
        for developer in DEVELOPERS:
            card = DeveloperCard(developer)
            container_layout.addWidget(card)
        
        scroll.setWidget(container)
        main_layout.addWidget(scroll)