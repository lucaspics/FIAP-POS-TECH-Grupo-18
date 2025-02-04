import cv2
import time
import requests
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from config.logging_config import logger
from config.app_config import (
    API_URL, API_TIMEOUT, DEFAULT_CONFIDENCE_THRESHOLD,
    MAX_RETRIES, RETRY_DELAY
)

# Sessão HTTP compartilhada para todos os workers
_session = requests.Session()
_session.headers.update({'Connection': 'keep-alive'})

class AnalysisWorker(QThread):
    """Worker thread para processar análises de frames."""
    analysis_complete = pyqtSignal(dict)  # Sinal emitido quando a análise é concluída
    analysis_error = pyqtSignal(str)      # Sinal emitido em caso de erro
    
    def __init__(self, frame_rgb, frame_number=None):
        super().__init__()
        self.frame_rgb = frame_rgb.copy()
        self.frame_number = frame_number
        
    def analyze(self):
        """Realiza a análise do frame."""
        try:
            # Converter frame para JPEG em memória
            _, img_bytes = cv2.imencode('.jpg', cv2.cvtColor(self.frame_rgb, cv2.COLOR_RGB2BGR))
            img_bytes = img_bytes.tobytes()
            
            # Configurar parâmetros da requisição
            params = {
                'confidence': DEFAULT_CONFIDENCE_THRESHOLD,
                'return_image': True  # API irá salvar a imagem se necessário
            }
            
            # Usar timeouts mais adequados
            timeout = (
                min(API_TIMEOUT.get('total', 30), 20),  # 20 segundos total
                min(API_TIMEOUT.get('connect', 5), 5)   # 5 segundos para conectar
            )
            
            for attempt in range(MAX_RETRIES):
                try:
                    files = {
                        'frame': ('frame.jpg', img_bytes, 'image/jpeg')
                    }
                    
                    response = _session.post(
                        API_URL,
                        files=files,
                        params=params,
                        timeout=timeout,
                        verify=False
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Erro na API: {response.status_code}")
                    
                    result = response.json()
                    if not result or 'detections' not in result:
                        raise Exception("Resposta inválida da API")
                    
                    return result
                    
                except (requests.Timeout, requests.ConnectionError) as e:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY * (attempt + 1))  # Backoff exponencial
                        continue
                    raise Exception(f"Erro após {MAX_RETRIES} tentativas: {str(e)}")
                    
                except Exception as e:
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    raise
                    
        except Exception as e:
            self._handle_error(e)
            return None

    def _handle_error(self, error):
        """Trata erros ocorridos durante a análise."""
        error_msg = str(error) if str(error).strip() else "Erro desconhecido"
        frame_info = f"frame {self.frame_number}" if self.frame_number is not None else "frame desconhecido"
        full_error = f"Erro na análise do {frame_info}: {error_msg}"
        logger.error(full_error)
        self.analysis_error.emit(full_error)

    def run(self):
        """Executa a análise em uma thread separada."""
        try:
            result = self.analyze()
            if result:
                self.analysis_complete.emit(result)
            else:
                self.analysis_error.emit("Análise não retornou resultados")
        except Exception as e:
            error_msg = f"Erro durante análise do frame {self.frame_number}: {str(e)}"
            logger.error(error_msg)
            self.analysis_error.emit(error_msg)