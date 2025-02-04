import sys
import logging
from PyQt5.QtWidgets import QApplication
from ui.main_window import SecurityCameraApp
from config.logging_config import logger

def main():
    """Função principal da aplicação."""
    try:
        # Inicializar aplicação Qt
        app = QApplication(sys.argv)
        
        # Criar e exibir janela principal
        window = SecurityCameraApp()
        window.show()
        
        # Executar loop de eventos
        sys.exit(app.exec_())
            
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
