import subprocess
import sys
import time
import os
import signal
import logging
import pkg_resources
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente do .env
load_dotenv()

# Adiciona o diretório raiz ao PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VisionGuardRunner:
    """Gerenciador principal do sistema VisionGuard."""
    
    def __init__(self):
        self.frontend_process = None
        self.processes = []
        
    def check_dependencies(self):
        """Verifica se todas as dependências estão instaladas."""
        logger.info("Verificando dependências...")
        required = {
            'ultralytics', 'opencv-python',
            'pyqt5', 'numpy', 'torch',
            'secure-smtplib', 'python-dotenv'
        }
        installed = {pkg.key for pkg in pkg_resources.working_set}
        missing = required - installed
        
        if missing:
            logger.error(f"Dependências faltando: {missing}")
            logger.error("Por favor, execute: pip install -r requirements.txt")
            return False
        return True

    def start_frontend(self):
        """Inicia a interface gráfica."""
        try:
            logger.info("Iniciando Frontend...")
            env = os.environ.copy()
            env["PYTHONPATH"] = root_dir + os.pathsep + env.get("PYTHONPATH", "")
            
            self.frontend_process = subprocess.Popen(
                [sys.executable, os.path.join("src", "main.py")],
                env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            self.processes.append(self.frontend_process)
            
            # Verificar se o processo iniciou corretamente
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
            os.path.join("src", "core", "detector.py"),
            os.path.join("src", "core", "alert_manager.py"),
            os.path.join("src", "core", "__init__.py"),
            os.path.join("src", "config", "app_config.py"),
            os.path.join("src", "main.py"),
            "requirements.txt",
            ".env"  # Adicionado verificação do .env
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(os.path.join(root_dir, file)):
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"Arquivos faltando: {missing_files}")
            return False
        return True

    def check_processes_health(self):
        """Verifica a saúde dos processos em execução."""
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
║    Detecção de Objetos Cortantes     ║
╚══════════════════════════════════════╝
            """)

            # Verificações iniciais
            if not self.verify_files():
                logger.error("Arquivos necessários não encontrados")
                return

            if not self.check_dependencies():
                return

            # Verificar variáveis de ambiente
            required_env = ['SMTP_EMAIL', 'SMTP_PASSWORD']
            missing_env = [var for var in required_env if not os.getenv(var)]
            if missing_env:
                logger.error(f"Variáveis de ambiente faltando: {missing_env}")
                logger.error("Por favor, configure o arquivo .env")
                return

            # Criar diretórios necessários
            from config.app_config import LOG_DIRS
            for dir_path in LOG_DIRS.values():
                os.makedirs(dir_path, exist_ok=True)

            # Iniciar frontend
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
    import subprocess
    runner = VisionGuardRunner()
    runner.run()