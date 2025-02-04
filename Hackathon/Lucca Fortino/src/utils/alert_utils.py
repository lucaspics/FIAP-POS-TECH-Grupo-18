import os
import cv2
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QListWidgetItem
from PyQt5.QtGui import QPixmap
from config.logging_config import logger
from config.app_config import LOG_DIRS

class AlertManager:
    """Gerenciador de alertas da aplicação."""
    
    @staticmethod
    def save_alert_frame(frame, current_time_ms):
        """
        Salva um frame de alerta.
        
        Args:
            frame: Frame OpenCV para salvar
            current_time_ms: Tempo atual do vídeo em milissegundos
            
        Returns:
            str: Caminho do arquivo salvo
        """
        # Garantir que o diretório existe
        os.makedirs(LOG_DIRS["base"], exist_ok=True)
        
        # Criar nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        alert_frame_path = os.path.join(LOG_DIRS["base"], f"alert-{timestamp}.png")
        
        # Salvar frame
        cv2.imwrite(alert_frame_path, frame)
        logger.info(f"Frame de alerta salvo em: {alert_frame_path}")
        
        return alert_frame_path

    @staticmethod
    def create_alert_widget(alert_frame_path, current_time_ms):
        """
        Cria um widget para exibir o alerta na interface.
        
        Args:
            alert_frame_path: Caminho do arquivo do frame de alerta
            current_time_ms: Tempo do vídeo em milissegundos
            
        Returns:
            tuple: (QListWidgetItem, QWidget) para adicionar à lista de alertas
        """
        # Criar widget e layout
        item_widget = QWidget()
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(0, 0, 0, 0)
        
        # Adicionar thumbnail
        thumb_pixmap = QPixmap(alert_frame_path).scaled(100, 75)
        thumb_label = QLabel()
        thumb_label.setPixmap(thumb_pixmap)
        item_layout.addWidget(thumb_label)
        
        # Adicionar texto
        text_label = QLabel(f"Tempo: {current_time_ms}ms\nAlerta detectado")
        item_layout.addWidget(text_label)
        
        # Configurar widget
        item_widget.setLayout(item_layout)
        
        # Criar item da lista
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        list_item.setData(0, current_time_ms)  # Armazenar tempo para navegação
        
        return list_item, item_widget

    @staticmethod
    def process_detection_alert(result, frame=None):
        """
        Processa um alerta baseado no resultado da detecção.
        
        Args:
            result: Dicionário com resultado da análise
            frame: Frame opcional associado ao alerta
            
        Returns:
            bool: True se um alerta foi detectado, False caso contrário
        """
        try:
            alert_value = int(result.get('alert_triggered', 0))
            
            if alert_value == 1:
                logger.warning(">>> ALERTA DETECTADO! Disparando notificação...")
                return True
            
            return False
            
        except (ValueError, TypeError) as e:
            logger.error(f"Erro ao processar alert_triggered: {str(e)}")
            return False