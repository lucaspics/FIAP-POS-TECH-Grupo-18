"""
Interface de visualização de alertas.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QPushButton,
    QLabel,
    QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import os
from config.logging_config import get_logger
from core.alert_utils import AlertWidget, create_alert_list_item
from config.app_config import UI_CONFIG, LOG_DIRS
from .alert_dialog import AlertDialog

logger = get_logger('alert_view')

class AlertView(QWidget):
    """Widget para visualização de alertas."""
    
    # Sinais
    alert_selected = pyqtSignal(str)  # ID do alerta selecionado
    jump_to_time = pyqtSignal(int)    # Tempo em ms para pular
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        Inicializa a visualização de alertas.
        
        Args:
            parent: Widget pai opcional
        """
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Inicializa a interface do usuário."""
        try:
            # Layout principal
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            
            # Lista de alertas
            self.alerts_list = QListWidget()
            self.alerts_list.setFrameStyle(QFrame.NoFrame)
            self.alerts_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            layout.addWidget(self.alerts_list)
            
            # Estado inicial
            self.current_alert_id = None
            
            # Estilo
            self.setStyleSheet("""
                QListWidget {
                    background-color: #f5f5f5;
                    border: none;
                }
                QPushButton {
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            
        except Exception as e:
            logger.error(f"Erro ao inicializar UI: {str(e)}")
            # Criar UI mínima em caso de erro
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("Erro ao carregar interface de alertas"))
    
    def add_alert(self, alert_data: Dict[str, Any]):
        """
        Adiciona um novo alerta à lista.
        
        Args:
            alert_data: Dados do alerta
        """
        try:
            logger.info(f"Adicionando alerta com dados: {alert_data}")
            
            # Verificar se tem ID
            alert_id = alert_data.get('alert_id')
            if not alert_id:
                logger.error("Alerta não possui ID")
                return
            
            # Verificar existência da imagem
            image_path = str(Path(LOG_DIRS['alerts']) / 'images' / f"{alert_id}.jpg")
            alert_data['has_image'] = os.path.exists(image_path)
            alert_data['image_path'] = image_path if alert_data['has_image'] else None
            
            logger.info(f"Status da imagem - Existe: {alert_data['has_image']}, Caminho: {image_path}")
                
            # Criar item e widget
            item, widget = create_alert_list_item(alert_data)
            
            if isinstance(widget, AlertWidget):  # Verifica se não é um widget de erro
                # Conectar sinal do widget para abrir dialog
                widget.alert_clicked.connect(self._show_alert_dialog)
                
                # Adicionar à lista
                self.alerts_list.addItem(item)
                self.alerts_list.setItemWidget(item, widget)
                
                logger.info(f"Alerta adicionado com sucesso: {alert_id}")
            else:
                logger.error("Falha ao criar widget do alerta")
            
            # Limitar número de itens
            while self.alerts_list.count() > UI_CONFIG['max_log_entries']:
                self.alerts_list.takeItem(0)
            
            logger.debug(f"Alerta adicionado: {alert_data.get('alert_id')}")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar alerta: {str(e)}")
    
    def _show_alert_dialog(self, alert_id: str):
        """
        Exibe o dialog com detalhes do alerta.
        
        Args:
            alert_id: ID do alerta
        """
        try:
            # Encontrar dados do alerta
            for i in range(self.alerts_list.count()):
                item = self.alerts_list.item(i)
                alert_data = item.data(Qt.UserRole)
                if alert_data.get('alert_id') == alert_id:
                    # Verificar existência da imagem novamente
                    image_path = str(Path(LOG_DIRS['alerts']) / 'images' / f"{alert_id}.jpg")
                    alert_data['has_image'] = os.path.exists(image_path)
                    alert_data['image_path'] = image_path if alert_data['has_image'] else None
                    
                    logger.info(f"Mostrando dialog para alerta {alert_id}")
                    logger.info(f"Dados do alerta: {alert_data}")
                    logger.info(f"Status da imagem - Existe: {alert_data['has_image']}, Caminho: {image_path}")
                    
                    # Criar e exibir dialog
                    dialog = AlertDialog(alert_data, self)
                    dialog.exec_()
                    break
                    
        except Exception as e:
            logger.error(f"Erro ao mostrar dialog: {str(e)}")
    
    def clear_all(self):
        """Limpa todos os alertas."""
        try:
            self.alerts_list.clear()
            self.current_alert_id = None
            logger.info("Todos os alertas foram limpos")
        except Exception as e:
            logger.error(f"Erro ao limpar alertas: {str(e)}")