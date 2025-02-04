import sys
import asyncio
import logging
from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop, QApplication as QAsyncApplication
from ui.main_window import SecurityCameraApp
from config.logging_config import logger

def main():
    """Função principal da aplicação."""
    try:
        # Inicializar aplicação Qt assíncrona
        app = QAsyncApplication(sys.argv)
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        # Criar e exibir janela principal
        window = SecurityCameraApp()
        window.show()
        
        # Executar loop de eventos
        with loop:
            loop.run_forever()
            
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
