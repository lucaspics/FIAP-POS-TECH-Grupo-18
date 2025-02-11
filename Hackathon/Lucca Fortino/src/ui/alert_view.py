"""
Interface de visualização de alertas.
"""

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QLabel,
    QScrollArea,
    QFrame,
    QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
from typing import Optional, Dict, Any
from datetime import datetime
from config.logging_config import get_logger
from core.alert_utils import AlertWidget, create_alert_list_item
from config.app_config import UI_CONFIG

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
            
            # Splitter para dividir lista e detalhes
            splitter = QSplitter(Qt.Vertical)
            
            # Lista de alertas
            self.alerts_list = QListWidget()
            self.alerts_list.setFrameStyle(QFrame.NoFrame)
            self.alerts_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.alerts_list.itemClicked.connect(self._handle_alert_click)
            splitter.addWidget(self.alerts_list)
            
            # Painel de detalhes
            details_widget = QWidget()
            details_layout = QVBoxLayout(details_widget)
            
            # Cabeçalho dos detalhes
            header = QWidget()
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(10, 5, 10, 5)
            
            self.details_title = QLabel("Detalhes do Alerta")
            self.details_title.setStyleSheet("font-weight: bold;")
            header_layout.addWidget(self.details_title)
            
            # Botões de ação
            action_buttons = QWidget()
            action_layout = QHBoxLayout(action_buttons)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            self.jump_button = QPushButton(QIcon.fromTheme("media-seek-forward"), "")
            self.jump_button.setToolTip("Pular para este momento")
            self.jump_button.clicked.connect(self._handle_jump_click)
            action_layout.addWidget(self.jump_button)
            
            header_layout.addWidget(action_buttons)
            details_layout.addWidget(header)
            
            # Área de rolagem para detalhes
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameStyle(QFrame.NoFrame)
            
            self.details_content = QWidget()
            self.details_layout = QVBoxLayout(self.details_content)
            scroll.setWidget(self.details_content)
            details_layout.addWidget(scroll)
            
            splitter.addWidget(details_widget)
            
            # Configurar proporções do splitter
            splitter.setStretchFactor(0, 2)  # Lista ocupa 2/3
            splitter.setStretchFactor(1, 1)  # Detalhes ocupam 1/3
            
            layout.addWidget(splitter)
            
            # Estilo
            self.setStyleSheet("""
                QListWidget {
                    background-color: #f5f5f5;
                    border: none;
                }
                QScrollArea {
                    background-color: white;
                }
                QPushButton {
                    padding: 5px;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            
            # Estado inicial
            self.current_alert_id = None
            self.clear_details()
            
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
                
            # Criar item e widget
            item, widget = create_alert_list_item(alert_data)
            
            if isinstance(widget, AlertWidget):  # Verifica se não é um widget de erro
                # Conectar sinal do widget
                widget.alert_clicked.connect(self.alert_selected.emit)
                
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
    
    def show_alert_details(self, alert_data: Dict[str, Any]):
        """
        Exibe os detalhes de um alerta.
        
        Args:
            alert_data: Dados do alerta
        """
        try:
            # Limpar conteúdo anterior
            self.clear_details()
            
            # Atualizar ID atual
            self.current_alert_id = alert_data.get('alert_id')
            
            # Título com timestamp
            timestamp = datetime.fromisoformat(alert_data.get('timestamp', ''))
            self.details_title.setText(f"Alerta - {timestamp.strftime('%H:%M:%S')}")
            
            # Adicionar detalhes
            details = QWidget()
            details_layout = QVBoxLayout(details)
            
            # Imagem
            if alert_data.get('has_image'):
                image_label = QLabel()
                pixmap = QPixmap(alert_data.get('image_path', ''))
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        400, 300,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    image_label.setPixmap(scaled_pixmap)
                    details_layout.addWidget(image_label)
            
            # Detecções
            for det in alert_data.get('detections', []):
                det_widget = QFrame()
                det_widget.setFrameStyle(QFrame.StyledPanel)
                det_layout = QVBoxLayout(det_widget)
                
                # Classe e confiança
                conf = det.get('confidence', 0) * 100
                det_layout.addWidget(QLabel(
                    f"<b>{det.get('class_name', 'Desconhecido')}</b> ({conf:.1f}%)"
                ))
                
                # Bounding box
                bbox = det.get('bbox', [])
                if bbox:
                    det_layout.addWidget(QLabel(
                        f"Posição: ({int(bbox[0])}, {int(bbox[1])}) - "
                        f"({int(bbox[2])}, {int(bbox[3])})"
                    ))
                
                details_layout.addWidget(det_widget)
            
            # Adicionar ao scroll
            self.details_layout.addWidget(details)
            self.details_layout.addStretch()
            
            # Habilitar botão
            self.jump_button.setEnabled(True)
            
        except Exception as e:
            logger.error(f"Erro ao mostrar detalhes: {str(e)}")
            self.clear_details()
    
    def clear_details(self):
        """Limpa o painel de detalhes."""
        try:
            # Limpar layout
            while self.details_layout.count():
                item = self.details_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Resetar título
            self.details_title.setText("Detalhes do Alerta")
            
            # Desabilitar botão
            self.jump_button.setEnabled(False)
            
            self.current_alert_id = None
            
        except Exception as e:
            logger.error(f"Erro ao limpar detalhes: {str(e)}")
    
    def clear_all(self):
        """Limpa todos os alertas."""
        try:
            self.alerts_list.clear()
            self.clear_details()
            logger.info("Todos os alertas foram limpos")
        except Exception as e:
            logger.error(f"Erro ao limpar alertas: {str(e)}")
    
    def _handle_alert_click(self, item):
        """
        Manipula clique em um alerta.
        
        Args:
            item: Item clicado
        """
        try:
            alert_data = item.data(Qt.UserRole)
            if alert_data:
                self.show_alert_details(alert_data)
        except Exception as e:
            logger.error(f"Erro ao processar clique: {str(e)}")
    
    def _handle_jump_click(self):
        """Manipula clique no botão de pular."""
        try:
            if self.current_alert_id:
                # Encontrar item na lista
                for i in range(self.alerts_list.count()):
                    item = self.alerts_list.item(i)
                    data = item.data(Qt.UserRole)
                    if data.get('alert_id') == self.current_alert_id:
                        self.jump_to_time.emit(data.get('video_time', 0))
                        break
        except Exception as e:
            logger.error(f"Erro ao processar pulo: {str(e)}")
    