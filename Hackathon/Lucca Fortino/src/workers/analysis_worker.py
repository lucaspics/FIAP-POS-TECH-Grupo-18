import os
import cv2
import time
import json
import asyncio
import aiohttp
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from config.logging_config import logger
from config.app_config import (
    API_URL, API_TIMEOUT, DEFAULT_CONFIDENCE_THRESHOLD,
    MAX_RETRIES, RETRY_DELAY, LOG_DIRS
)

class AnalysisWorker(QThread):
    """Worker thread para processar análises de frames."""
    analysis_complete = pyqtSignal(dict)  # Sinal emitido quando a análise é concluída
    analysis_error = pyqtSignal(str)      # Sinal emitido em caso de erro
    
    def __init__(self, frame_rgb, frame_number=None):
        super().__init__()
        self.frame_rgb = frame_rgb.copy()  # Fazer uma cópia do frame para evitar problemas de memória
        self.frame_number = frame_number
        self._is_running = True
        
        logger.info(f"\n=== Iniciando Worker para Frame {frame_number} ===")
        
    def convert_value(self, value):
        """Converte valores para o formato adequado para o FormData."""
        if value is None:
            return ''
        if isinstance(value, bool):
            return str(value).lower()
        return value

    async def analyze(self):
        """Realiza a análise do frame de forma assíncrona."""
        try:
            frame_info = f"frame {self.frame_number}" if self.frame_number is not None else "frame desconhecido"
            logger.info(f"\n=== Iniciando análise de {frame_info} ===")
            
            # Garantir que os diretórios existem
            for dir_path in LOG_DIRS.values():
                os.makedirs(dir_path, exist_ok=True)
            
            # Gerar nome único para o frame
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            frame_path = os.path.join(LOG_DIRS["frames"], f"frame_{timestamp}.jpg")
            
            # Salvar frame original
            cv2.imwrite(frame_path, cv2.cvtColor(self.frame_rgb, cv2.COLOR_RGB2BGR))
            logger.info(f"Frame salvo em: {frame_path}")
            
            if not os.path.exists(frame_path):
                raise Exception("Erro ao salvar imagem do frame")
            
            # Preparar dados para upload
            with open(frame_path, 'rb') as f:
                img_bytes = f.read()
            
            # Configurar parâmetros da requisição
            params = {
                'confidence': self.convert_value(DEFAULT_CONFIDENCE_THRESHOLD),
                'return_image': self.convert_value(False)
            }
            
            # Configurar conexão HTTP
            connector = aiohttp.TCPConnector(
                force_close=False,
                enable_cleanup_closed=True,
                limit=0,
                ttl_dns_cache=300,
                keepalive_timeout=60,
                ssl=False
            )
            
            timeout = aiohttp.ClientTimeout(**API_TIMEOUT)
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={'Connection': 'keep-alive'},
                raise_for_status=True
            ) as session:
                for attempt in range(MAX_RETRIES):
                    try:
                        form = aiohttp.FormData()
                        form.add_field(
                            name='frame',
                            value=img_bytes,
                            filename='frame.jpg',
                            content_type='image/jpeg'
                        )
                        
                        async with session.post(API_URL, data=form, params=params) as response:
                            if response.status != 200:
                                error_text = await response.text()
                                raise Exception(f"Erro na API: {response.status} - {error_text}")
                            
                            result = await response.json()
                            
                            if not result or 'detections' not in result:
                                raise Exception("Resposta inválida da API")
                            
                            # Processar detecções
                            self._process_detections(result, frame_path, timestamp)
                            return result
                            
                    except aiohttp.ClientError as e:
                        if attempt < MAX_RETRIES - 1:
                            await asyncio.sleep(RETRY_DELAY)
                            continue
                        raise
                        
        except Exception as e:
            self._handle_error(e, frame_path if 'frame_path' in locals() else None)
            return None

    def _process_detections(self, result, frame_path, timestamp):
        """Processa as detecções recebidas da API."""
        detections = result.get('detections', [])
        if detections:
            # Criar nome do arquivo baseado no resultado
            detection_info = "_".join([
                f"{det.get('class_name', 'unknown')}{det.get('confidence', 0.0):.2f}"
                for det in detections[:3]
            ])
            
            # Salvar resultado
            frame_number = self.frame_number if self.frame_number is not None else 0
            result_path = os.path.join(
                LOG_DIRS["results"],
                f"detection_{timestamp}_frame{frame_number}_{detection_info}.jpg"
            )
            
            # Copiar frame e salvar metadados
            import shutil
            shutil.copy2(frame_path, result_path)
            
            # Salvar JSON com metadados
            result_json = f"{result_path}.json"
            result_data = {
                "frame_number": frame_number,
                "timestamp": timestamp,
                "detections": detections,
                "original_frame": frame_path,
                "alert_triggered": result.get('alert_triggered', 0)
            }
            with open(result_json, 'w') as f:
                json.dump(result_data, f, indent=2)

    def _handle_error(self, error, frame_path):
        """Trata erros ocorridos durante a análise."""
        error_msg = str(error) if str(error).strip() else "Erro desconhecido"
        frame_info = f"frame {self.frame_number}" if self.frame_number is not None else "frame desconhecido"
        full_error = f"Erro na análise do {frame_info}: {error_msg}"
        
        logger.error(full_error)
        logger.error("Stack trace:", exc_info=True)
        self.analysis_error.emit(full_error)
        
        # Mover frame com erro para pasta de erros
        if frame_path and os.path.exists(frame_path):
            try:
                error_path = os.path.join(
                    LOG_DIRS["errors"],
                    f"error_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_frame{self.frame_number}.jpg"
                )
                os.rename(frame_path, error_path)
                logger.info(f"Frame com erro movido para: {error_path}")
            except Exception as move_error:
                logger.error(f"Erro ao mover frame com erro: {str(move_error)}")

    def run(self):
        """Executa a análise em uma thread separada."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                start_time = time.time()
                result = loop.run_until_complete(self.analyze())
                total_time = time.time() - start_time
                
                if result:
                    self.analysis_complete.emit(result)
                    logger.info(f"Frame {self.frame_number} - Análise completada em {total_time:.2f}s")
                else:
                    logger.warning(f"Frame {self.frame_number} - Análise retornou None")
                    self.analysis_error.emit("Análise não retornou resultados")
                
            except Exception as e:
                error_msg = f"Erro durante análise do frame {self.frame_number}: {str(e)}"
                logger.error(error_msg)
                logger.error("Stack trace completo:", exc_info=True)
                self.analysis_error.emit(error_msg)
                
        except Exception as e:
            error_msg = f"Erro ao configurar análise: {str(e)}"
            logger.error(error_msg)
            self.analysis_error.emit(error_msg)
            
        finally:
            try:
                for task in asyncio.all_tasks(loop):
                    task.cancel()
                loop.stop()
                loop.close()
            except Exception as e:
                logger.error(f"Erro ao limpar recursos: {str(e)}")
            
            self.analysis_in_progress = False