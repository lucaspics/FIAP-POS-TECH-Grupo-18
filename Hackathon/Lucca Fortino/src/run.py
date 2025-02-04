import subprocess
import sys
import time
import os
import signal
import socket
from pathlib import Path
import logging
import pkg_resources

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_port_in_use(port):
    """Verifica se uma porta está em uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

class VisionGuardRunner:
    def __init__(self):
        self.api_process = None
        self.frontend_process = None
        self.processes = []
        self.api_port = 8000
        self.startup_timeout = 30  # segundos

    def check_dependencies(self):
        """Verifica se todas as dependências estão instaladas."""
        logger.info("Verificando dependências...")
        required = {
            'uvicorn', 'fastapi', 'ultralytics', 'opencv-python',
            'pyqt5', 'requests', 'python-multipart'
        }
        installed = {pkg.key for pkg in pkg_resources.working_set}
        missing = required - installed
        
        if missing:
            logger.error(f"Dependências faltando: {missing}")
            logger.error("Por favor, execute: pip install -r requirements.txt")
            return False
        return True

    def wait_for_api(self, timeout):
        """Aguarda a API ficar disponível."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.api_process.poll() is not None:
                raise RuntimeError("API falhou ao iniciar")
            
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(('localhost', self.api_port))
                    logger.info("API está respondendo")
                    return True
            except (ConnectionRefusedError, socket.error):
                time.sleep(1)
        
        raise TimeoutError("Timeout aguardando API inicializar")

    def start_api(self):
        """Inicia o servidor API."""
        try:
            if is_port_in_use(self.api_port):
                raise RuntimeError(f"Porta {self.api_port} já está em uso")

            logger.info("Iniciando API...")
            self.api_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", str(self.api_port)],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            self.processes.append(self.api_process)
            
            # Aguarda API inicializar com timeout
            self.wait_for_api(self.startup_timeout)
            
        except Exception as e:
            logger.error(f"Erro ao iniciar API: {str(e)}")
            self.cleanup()
            sys.exit(1)

    def start_frontend(self):
        """Inicia a interface gráfica."""
        try:
            logger.info("Iniciando Frontend...")
            self.frontend_process = subprocess.Popen(
                [sys.executable, "src/main.py"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            self.processes.append(self.frontend_process)
            
            # Verifica se o processo iniciou corretamente
            time.sleep(2)
            if self.frontend_process.poll() is not None:
                raise RuntimeError("Frontend falhou ao iniciar")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar Frontend: {str(e)}")
            self.cleanup()
            sys.exit(1)

    def cleanup(self):
        """Limpa todos os processos ao encerrar."""
        logger.info("Encerrando processos...")
        for process in self.processes:
            if process and process.poll() is None:
                try:
                    if sys.platform == 'win32':
                        process.send_signal(signal.CTRL_BREAK_EVENT)
                        time.sleep(1)
                        if process.poll() is None:
                            process.kill()
                    else:
                        process.terminate()
                        time.sleep(1)
                        if process.poll() is None:
                            process.kill()
                except Exception as e:
                    logger.error(f"Erro ao encerrar processo: {str(e)}")

    def verify_files(self):
        """Verifica se todos os arquivos necessários existem."""
        required_files = [
            "src/api/main.py",
            "src/api/detector.py",
            "src/api/alert_manager.py",
            "src/api/config.py",
            "src/main.py",
            "requirements.txt"
        ]
        
        missing_files = []
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"Arquivos faltando: {missing_files}")
            return False
        return True

    def check_processes_health(self):
        """Verifica a saúde dos processos em execução."""
        if self.api_process and self.api_process.poll() is not None:
            logger.error("API não está mais respondendo")
            return False
        
        if self.frontend_process and self.frontend_process.poll() is not None:
            logger.error("Frontend não está mais respondendo")
            return False
        
        return True

    def run(self):
        """Inicia todo o sistema."""
        try:
            print("""
╔══════════════════════════════════════╗
║          VisionGuard System          ║
║    Detecção de Objetos Cortantes    ║
╚══════════════════════════════════════╝
            """)

            # Verificações iniciais
            if not self.verify_files():
                logger.error("Arquivos necessários não encontrados")
                return

            if not self.check_dependencies():
                return

            # Criar diretórios necessários
            for dir_path in ["logs", "models", "data"]:
                Path(dir_path).mkdir(exist_ok=True)

            # Iniciar componentes
            self.start_api()
            self.start_frontend()

            logger.info("Sistema VisionGuard iniciado com sucesso!")
            logger.info("Pressione Ctrl+C para encerrar...")

            # Loop principal com verificação de saúde
            while True:
                if not self.check_processes_health():
                    break
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Encerramento solicitado pelo usuário...")
        except Exception as e:
            logger.error(f"Erro inesperado: {str(e)}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    runner = VisionGuardRunner()
    runner.run()