import subprocess
import sys
import time
import os
import signal
from pathlib import Path
import logging
import pkg_resources
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VisionGuardRunner:
    def __init__(self):
        self.api_process = None
        self.frontend_process = None
        self.processes = []
        self.api_ready = False

    def check_dependencies(self):
        """Verifica se todas as dependências estão instaladas."""
        logger.info("Verificando dependências...")
        required = {
            'uvicorn', 'fastapi', 'ultralytics', 'opencv-python',
            'pyqt5', 'qasync', 'aiohttp'
        }
        installed = {pkg.key for pkg in pkg_resources.working_set}
        missing = required - installed
        
        if missing:
            logger.error(f"Dependências faltando: {missing}")
            logger.error("Por favor, execute: pip install -r requirements.txt")
            return False
        return True

    def start_api(self):
        """Inicia o servidor API."""
        try:
            logger.info("Iniciando API...")
            # Usar python -m uvicorn em vez do comando direto
            self.api_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "src.api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.processes.append(self.api_process)
            
            # Aguardar até que a API esteja pronta
            while not self.api_ready:
                output = self.api_process.stderr.readline()
                if "Uvicorn running on" in output:
                    self.api_ready = True
                    logger.info("API iniciada com sucesso em http://0.0.0.0:8000")
                    break
                elif "Error" in output or "ERROR" in output:
                    if "Address already in use" in output:
                        logger.error("Porta 8000 já está em uso. Encerrando...")
                        self.cleanup()
                        sys.exit(1)
                    else:
                        logger.error(f"Erro ao iniciar API: {output.strip()}")
                        self.cleanup()
                        sys.exit(1)
                time.sleep(0.1)
            
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
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.processes.append(self.frontend_process)
            
            # Aguardar um pouco para verificar se o processo iniciou corretamente
            time.sleep(2)
            
            # Verificar se o processo ainda está rodando
            if self.frontend_process.poll() is not None:
                # Processo já terminou, verificar se houve erro
                error_output = self.frontend_process.stderr.read()
                if error_output:
                    logger.error(f"Erro ao iniciar Frontend:\n{error_output}")
                    raise Exception(f"Frontend falhou ao iniciar: {error_output}")
                output = self.frontend_process.stdout.read()
                if output:
                    logger.info(f"Saída do Frontend:\n{output}")
            
            logger.info("Frontend iniciado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar Frontend: {str(e)}")
            self.cleanup()
            sys.exit(1)

    def cleanup(self):
        """Limpa todos os processos ao encerrar."""
        logger.info("Encerrando processos...")
        for process in self.processes:
            if process:
                try:
                    if sys.platform == 'win32':
                        process.kill()
                    else:
                        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
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

    def process_output(self, output, process_name):
        """Processa e filtra a saída dos processos."""
        if not output:
            return
            
        # Filtrar mensagens de log comuns do Uvicorn
        if any(msg in output for msg in [
            "Will watch for changes",
            "Uvicorn running on",
            "StatReload"
        ]):
            return
            
        # Detectar erros reais
        if "error" in output.lower() or "exception" in output.lower():
            logger.error(f"{process_name}: {output.strip()}")
        else:
            logger.info(f"{process_name}: {output.strip()}")

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

            # Monitorar processos
            while True:
                # Verificar se algum processo terminou
                if any(p.poll() is not None for p in self.processes):
                    logger.error("Um dos processos terminou inesperadamente")
                    break

                # Processar saídas
                for p in self.processes:
                    if p.stdout:
                        output = p.stdout.readline()
                        if output:
                            self.process_output(output, "API" if p == self.api_process else "Frontend")
                    if p.stderr:
                        error = p.stderr.readline()
                        if error:
                            self.process_output(error, "API" if p == self.api_process else "Frontend")

                time.sleep(0.1)

        except KeyboardInterrupt:
            logger.info("Encerrando sistema...")
        finally:
            self.cleanup()

if __name__ == "__main__":
    runner = VisionGuardRunner()
    runner.run()