import sys
import cv2
import os
import aiohttp
import logging
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QListWidget, QListWidgetItem, QLineEdit, QTabWidget, QTextEdit
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import QTimer, Qt
from datetime import datetime
from qasync import QEventLoop, QApplication as QAsyncApplication

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/frontend.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

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
        logger.info("Configurações de conexão:")
        logger.info("- Timeout total: 60 segundos")
        logger.info("- Timeout de conexão: 10 segundos")
        logger.info("- Timeout de leitura: 30 segundos")
        logger.info("- Keep-alive ativado (timeout: 60s)")
        logger.info("- Reutilização de conexões ativada")
        logger.info("- SSL desativado para localhost")

    def convert_value(self, value):
        """Converte valores para o formato adequado para o FormData."""
        if value is None:
            return ''
        if isinstance(value, bool):
            return str(value).lower()  # 'true' ou 'false'
        return value
    async def analyze(self):
        """Realiza a análise do frame de forma assíncrona."""
        try:
            frame_info = f"frame {self.frame_number}" if self.frame_number is not None else "frame desconhecido"
            logger.info(f"\n=== Iniciando análise de {frame_info} ===")
            
            # Garantir que os diretórios existem
            os.makedirs("logs/frames", exist_ok=True)
            os.makedirs("logs/results", exist_ok=True)
            
            # Gerar nome único para o frame
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            frame_path = f"logs/frames/frame_{timestamp}.jpg"
            
            # Salvar frame original (RGB)
            cv2.imwrite(frame_path, cv2.cvtColor(self.frame_rgb, cv2.COLOR_RGB2BGR))
            logger.info(f"Frame salvo em: {frame_path}")
            
            # Verificar se a imagem foi salva corretamente
            if not os.path.exists(frame_path):
                raise Exception("Erro ao salvar imagem do frame")
            
            # Ler o arquivo em bytes
            with open(frame_path, 'rb') as f:
                img_bytes = f.read()
            
            # Preparar dados para upload
            form = aiohttp.FormData()
            form.add_field(
                name='frame',
                value=img_bytes,
                filename='frame.jpg',
                content_type='image/jpeg'
            )
            
            # Configurar parâmetros da requisição com threshold mais baixo
            params = {
                'confidence': self.convert_value(0.15),  # Reduzir threshold para aumentar sensibilidade
                'return_image': self.convert_value(False)  # Desabilitar retorno de imagem para reduzir tempo de resposta
            }
            logger.info(f"Enviando requisição com confidence: {params['confidence']}")
            
            # Fazer requisição para a API com configurações otimizadas
            connector = aiohttp.TCPConnector(
                force_close=False,  # Permitir reutilização de conexões
                enable_cleanup_closed=True,
                limit=0,  # Sem limite de conexões simultâneas
                ttl_dns_cache=300,
                keepalive_timeout=60,  # 60 segundos de keepalive
                ssl=False  # Desabilitar SSL para localhost
            )
            
            logger.info(f"Frame {self.frame_number} - Iniciando conexão com a API...")
            start_request = time.time()
            
            # Configurar timeouts mais curtos (sem retorno de imagem)
            timeout = aiohttp.ClientTimeout(
                total=10,        # 10 segundos total
                connect=2,       # 2 segundos para conectar
                sock_connect=2,  # 2 segundos para conectar socket
                sock_read=5      # 5 segundos para ler dados
            )
            
            async with aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={'Connection': 'keep-alive'},  # Usar keep-alive
                raise_for_status=True  # Lançar exceção para status != 2xx
            ) as session:
                logger.info(f"Frame {self.frame_number} - Enviando requisição...")
                logger.info(f"Tamanho da imagem: {len(img_bytes)} bytes")
                logger.info(f"Parâmetros: {params}")
                
                max_retries = 3  # Reduzido para 3 tentativas
                retry_delay = 0.2  # Reduzido para 0.2 segundos
                
                for attempt in range(max_retries):
                    try:
                        # Criar novo FormData para cada tentativa
                        logger.info(f"Frame {self.frame_number} - Tentativa {attempt + 1}/{max_retries}")
                        logger.info(f"Frame {self.frame_number} - Criando novo FormData (Tentativa {attempt + 1})")
                        logger.info(f"Frame {self.frame_number} - Tempo decorrido: {time.time() - start_request:.2f}s")
                        
                        form = aiohttp.FormData()
                        form.add_field(
                            name='frame',
                            value=img_bytes,
                            filename='frame.jpg',
                            content_type='image/jpeg'
                        )
                        
                        logger.info(f"Frame {self.frame_number} - Enviando requisição POST")
                        logger.info(f"Frame {self.frame_number} - URL: http://localhost:8000/detect")
                        logger.info(f"Frame {self.frame_number} - Parâmetros: {params}")
                        
                        async with session.post(
                            'http://localhost:8000/detect',
                            data=form,
                            params=params
                        ) as response:
                            request_time = time.time() - start_request
                            logger.info(f"Frame {self.frame_number} - Resposta recebida em {request_time:.2f}s")
                            logger.info(f"Status: {response.status}")
                            
                            if response.status != 200:
                                error_text = await response.text()
                                raise Exception(f"Erro na API: {response.status} - {error_text}")
                            
                            result = await response.json()
                            logger.info(f"Frame {self.frame_number} - JSON decodificado com sucesso")
                            
                            if not result or 'detections' not in result:
                                raise Exception("Resposta inválida da API")
                            
                            logger.info(f"Frame {self.frame_number} - Detecções recebidas: {len(result.get('detections', []))}")
                            return result
                            
                    except aiohttp.ClientError as e:
                        logger.error(f"Frame {self.frame_number} - Tentativa {attempt + 1}/{max_retries} falhou: {str(e)}")
                        if attempt < max_retries - 1:
                            logger.info(f"Frame {self.frame_number} - Aguardando {retry_delay}s antes de tentar novamente...")
                            await asyncio.sleep(retry_delay)
                            continue
                        raise
                    except Exception as e:
                        logger.error(f"Frame {self.frame_number} - Erro ao processar resposta: {str(e)}")
                        raise
                    
                # Processar detecções após receber resposta
                detections = result.get('detections', [])
                if detections:
                    logger.info(f"Encontradas {len(detections)} detecções")
                    
                    # Criar nome do arquivo baseado no resultado
                    detection_info = "_".join([
                        f"{det.get('class_name', 'unknown')}"
                        f"{det.get('confidence', 0.0):.2f}"
                        for det in detections[:3]  # Limitar a 3 detecções no nome
                    ])
                    
                    # Criar nome do arquivo de resultado
                    frame_number = self.frame_number if self.frame_number is not None else 0
                    result_path = f"logs/results/detection_{timestamp}_frame{frame_number}_{detection_info}.jpg"
                    
                    # Copiar o frame para o diretório de resultados
                    import shutil
                    shutil.copy2(frame_path, result_path)
                    logger.info(f"Frame copiado para: {result_path}")
                    
                    # Salvar resultado em JSON
                    result_json = f"{result_path}.json"
                    result_data = {
                        "frame_number": frame_number,
                        "timestamp": timestamp,
                        "detections": detections,
                        "original_frame": frame_path,
                        "alert_triggered": result.get('alert_triggered', 0)  # Incluir alert_triggered
                    }
                    with open(result_json, 'w') as f:
                        json.dump(result_data, f, indent=2)
                    logger.info(f"Resultado salvo em: {result_json}")
                    
                    # Log do alert_triggered
                    alert_value = result.get('alert_triggered', 0)
                    logger.info(f"Alert triggered value: {alert_value}")
                    
                else:
                    logger.info("Nenhuma detecção encontrada")
                    # Mover frame sem detecções para um diretório separado
                    no_detection_path = f"logs/frames/no_detection_{timestamp}.jpg"
                    os.rename(frame_path, no_detection_path)
                    logger.info(f"Frame sem detecção movido para: {no_detection_path}")
                
                return result
                    
        except Exception as e:
            # Garantir que temos uma mensagem de erro clara
            error_msg = str(e) if str(e).strip() else "Erro desconhecido"
            frame_info = f"frame {self.frame_number}" if self.frame_number is not None else "frame desconhecido"
            full_error = f"Erro na análise do {frame_info}: {error_msg}"
            
            logger.error(full_error)
            logger.error("Stack trace:", exc_info=True)  # Adicionar stack trace para debug
            self.analysis_error.emit(full_error)
            
            # Mover arquivo para pasta de erros em vez de deletar
            if 'frame_path' in locals() and os.path.exists(frame_path):
                try:
                    error_dir = "logs/errors"
                    os.makedirs(error_dir, exist_ok=True)
                    error_path = f"{error_dir}/error_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_frame{self.frame_number}.jpg"
                    os.rename(frame_path, error_path)
                    logger.info(f"Frame com erro movido para: {error_path}")
                except Exception as move_error:
                    logger.error(f"Erro ao mover frame com erro: {str(move_error)}")
            
            return None
            
    def run(self):
        """Executa a análise em uma thread separada."""
        try:
            # Criar e configurar um novo loop para esta thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Executar análise sem timeout para debug
            try:
                logger.info(f"Frame {self.frame_number} - Iniciando análise sem timeout...")
                start_time = time.time()
                
                # Executar a análise
                result = loop.run_until_complete(self.analyze())
                
                # Calcular tempo total
                total_time = time.time() - start_time
                logger.info(f"Frame {self.frame_number} - Análise concluída em {total_time:.2f}s")
                
                if result:
                    self.analysis_complete.emit(result)
                    logger.info(f"Frame {self.frame_number} - Análise completada com sucesso")
                    logger.info(f"Detecções encontradas: {len(result.get('detections', []))}")
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
                # Limpar todas as tarefas pendentes
                for task in asyncio.all_tasks(loop):
                    task.cancel()
                
                # Fechar o loop
                loop.stop()
                loop.close()
            except Exception as e:
                logger.error(f"Erro ao limpar recursos: {str(e)}")
            
            # Garantir que analysis_in_progress seja atualizado
            self.analysis_in_progress = False

class SecurityCameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Câmera de Segurança")
        self.setGeometry(100, 100, 1000, 600)
        
        # Tamanho padrão do vídeo
        self.video_width = 640
        self.video_height = 480

        # Variáveis de controle
        self.analysis_interval = 15  # Aumentado para 60 frames (~2 segundos em 30 FPS)
        self.current_frame_count = 0
        self.analysis_in_progress = False  # Controle para evitar análises simultâneas
        self.worker = None  # Referência para o worker atual

        # Layout principal
        self.main_layout = QHBoxLayout()  # Layout horizontal para incluir vídeo e logs
        self.setLayout(self.main_layout)

        # Adiciona um TabWidget para abas
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Aba de vídeo
        self.video_tab = QWidget()
        self.tabs.addTab(self.video_tab, "Vídeo")
        self.video_layout = QHBoxLayout()  # Alterado para HBoxLayout para mover logs para a direita
        self.video_tab.setLayout(self.video_layout)

        # Layout esquerdo (vídeo e controles)
        self.left_layout = QVBoxLayout()
        self.video_layout.addLayout(self.left_layout)

        # Título da seção de vídeo
        self.video_title = QLabel("Monitoramento de Vídeo")
        self.video_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.left_layout.addWidget(self.video_title)

        # Widgets de vídeo
        self.video_label = QLabel("Feed da câmera aparecerá aqui")
        self.video_label.setFixedSize(self.video_width, self.video_height)
        self.video_label.setStyleSheet("background-color: black;")
        self.left_layout.addWidget(self.video_label)

        # Overlay acima do vídeo
        self.overlay_label = QLabel(self.video_label)
        self.overlay_label.setFixedSize(self.video_width, self.video_height)
        self.overlay_label.setAlignment(Qt.AlignCenter)
        self.overlay_label.setStyleSheet("background: transparent;")  # Garantir transparência

        # Carrega a imagem do overlay
        overlay_path = "src/assets/images/cam_overlay.png"
        if os.path.exists(overlay_path):
            self.overlay_pixmap = QPixmap(overlay_path).scaled(
                self.video_width, self.video_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.overlay_label.setPixmap(self.overlay_pixmap)
        else:
            logger.warning(f"Overlay não encontrado: {overlay_path}")

        self.time_label = QLabel("Tempo: 0s")
        self.left_layout.addWidget(self.time_label)

        self.connect_button = QPushButton("Conectar à Câmera")
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        self.connect_button.clicked.connect(self.connect_camera)
        self.left_layout.addWidget(self.connect_button)

        # Controles de tempo
        self.controls_layout = QHBoxLayout()

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.setEnabled(False)
        self.play_pause_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 14px;")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.controls_layout.addWidget(self.play_pause_button)

        self.rewind_button = QPushButton("Retroceder 5s")
        self.rewind_button.setEnabled(False)
        self.rewind_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")
        self.rewind_button.clicked.connect(self.rewind_video)
        self.controls_layout.addWidget(self.rewind_button)

        self.forward_button = QPushButton("Avançar 5s")
        self.forward_button.setEnabled(False)
        self.forward_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")
        self.forward_button.clicked.connect(self.forward_video)
        self.controls_layout.addWidget(self.forward_button)

        self.left_layout.addLayout(self.controls_layout)

        self.alert_button = QPushButton("Disparar Alerta")
        self.alert_button.setEnabled(False)
        self.alert_button.setStyleSheet("background-color: #e7e7e7; color: black; font-size: 14px;")
        self.alert_button.clicked.connect(self.trigger_alert)
        self.left_layout.addWidget(self.alert_button)

        # Layout direito para logs
        self.right_layout = QVBoxLayout()
        self.video_layout.addLayout(self.right_layout)
        
        # Label para título dos logs
        self.logs_title = QLabel("Logs de Análise")
        self.logs_title.setFont(QFont("Arial", 12, QFont.Bold))
        self.right_layout.addWidget(self.logs_title)
        
        # Área de texto para logs de análise
        self.analysis_logs = QTextEdit()
        self.analysis_logs.setReadOnly(True)
        self.analysis_logs.setFixedWidth(300)
        self.analysis_logs.setFixedHeight(200)
        self.analysis_logs.setStyleSheet("background-color: #f0f0f0;")
        self.right_layout.addWidget(self.analysis_logs)
        
        # Painel de Logs Visuais (Alertas)
        self.alerts_title = QLabel("Alertas Detectados")
        self.alerts_title.setFont(QFont("Arial", 12, QFont.Bold))
        self.right_layout.addWidget(self.alerts_title)
        
        self.logs_list = QListWidget()
        self.logs_list.setFixedWidth(300)
        self.logs_list.itemClicked.connect(self.jump_to_alert)
        self.right_layout.addWidget(self.logs_list)

        # Aba de Configurações
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Configurações")
        self.settings_layout = QVBoxLayout()
        self.settings_layout.setAlignment(Qt.AlignTop)  # Alinha os itens no topo
        self.settings_tab.setLayout(self.settings_layout)

        # Título da seção de configurações
        self.settings_title = QLabel("Configurações do Sistema")
        self.settings_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.settings_layout.addWidget(self.settings_title)

        # Campo de Email
        self.email_label = QLabel("Email para alertas:")
        self.email_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.settings_layout.addWidget(self.email_label)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Digite o email para alertas")
        self.email_input.setText("fiap.iadev.2023.team18@gmail.com")
        self.settings_layout.addWidget(self.email_input)

        # Campo de Intervalo de Análise
        self.interval_label = QLabel("Intervalo de análise de frames:")
        self.interval_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.settings_layout.addWidget(self.interval_label)
        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText("Intervalo de análise de frames (em frames)")
        self.interval_input.setText(str(self.analysis_interval))  # Define o valor padrão inicial
        self.settings_layout.addWidget(self.interval_input)

        # Botão para salvar configurações
        self.save_button = QPushButton("Salvar Configurações")
        self.save_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")
        self.save_button.clicked.connect(self.save_settings)
        self.settings_layout.addWidget(self.save_button)

        # Variáveis de controle
        self.video_path = None
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.is_playing = False

    def connect_camera(self):
        options = QFileDialog.Options()
        self.video_path, _ = QFileDialog.getOpenFileName(
            self, "Selecione o vídeo", "", "Arquivos de Vídeo (*.mp4 *.avi *.mov)", options=options
        )
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            if self.cap.isOpened():
                # Ativa os controles
                self.play_pause_button.setEnabled(True)
                self.rewind_button.setEnabled(True)
                self.forward_button.setEnabled(True)
                self.alert_button.setEnabled(True)

                # Desativa o botão de conectar
                self.connect_button.setEnabled(False)

                logger.info(f"Vídeo carregado: {self.video_path}")
                self.toggle_play_pause()  # Inicia automaticamente em modo Play
            else:
                logger.error("Erro ao carregar o vídeo.")

    def toggle_play_pause(self):
        if self.is_playing:
            self.timer.stop()
            self.play_pause_button.setText("Play")
        else:
            self.timer.start(30)  # Atualiza o frame a cada 30ms (~33 FPS)
            self.play_pause_button.setText("Pause")
        self.is_playing = not self.is_playing

    def rewind_video(self):
        if not self.cap:
            return
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        target_frame = max(0, current_frame - 150)  # 5 segundos (30 FPS * 5)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    def forward_video(self):
        if not self.cap:
            return
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        target_frame = min(total_frames - 1, current_frame + 150)  # 5 segundos (30 FPS * 5)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            logger.info("Fim do vídeo.")
            self.timer.stop()
            self.is_playing = False
            self.play_pause_button.setText("Play")
            return

        # Redimensiona o frame para o tamanho padrão
        frame = cv2.resize(frame, (self.video_width, self.video_height))

        # Converte o frame para QImage
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        step = channel * width
        qimg = QImage(frame_rgb.data, width, height, step, QImage.Format_RGB888)

        # Exibe o frame no QLabel
        self.video_label.setPixmap(QPixmap.fromImage(qimg))

        # Atualiza o tempo no label
        current_time = int(self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
        self.time_label.setText(f"Tempo: {current_time}s")

        # Incrementa o contador de frames
        self.current_frame_count += 1

        # Verifica se é hora de analisar o frame e se não há análise em andamento
        if self.current_frame_count % self.analysis_interval == 0 and not self.analysis_in_progress:
            # Limpar worker anterior se existir
            if self.worker:
                try:
                    self.worker.disconnect()
                    self.worker.deleteLater()
                except Exception as e:
                    logger.error(f"Erro ao limpar worker anterior: {str(e)}")
                self.worker = None
            
            logger.info(f"Frame {self.current_frame_count} - Iniciando análise...")
            self.analysis_logs.append(f"Frame {self.current_frame_count} - Iniciando análise...")
            
            try:
                # Cria e configura o worker
                self.analysis_in_progress = True
                self.worker = AnalysisWorker(frame_rgb.copy(), self.current_frame_count)
                self.worker.analysis_complete.connect(self.handle_analysis_result)
                self.worker.analysis_error.connect(self.handle_analysis_error)
                self.worker.finished.connect(self._on_analysis_finished)
                self.worker.start()
            except Exception as e:
                logger.error(f"Erro ao criar worker: {str(e)}")
                self.analysis_in_progress = False

    def handle_analysis_result(self, result):
        """Processa o resultado da análise."""
        try:
            logger.info("=== Análise do Frame ===")
            logger.info(f"Timestamp: {result.get('timestamp')}")
            logger.info(f"Detecções encontradas: {len(result.get('detections', []))}")
            
            self.analysis_logs.append("=== Análise do Frame ===")
            self.analysis_logs.append(f"Timestamp: {result.get('timestamp')}")
            self.analysis_logs.append(f"Detecções encontradas: {len(result.get('detections', []))}")
            
            for det in result.get('detections', []):
                det_info = f"- Classe: {det.get('class_name', det.get('class', 'unknown'))}, Confiança: {float(det['confidence']):.2f}"
                logger.info(det_info)
                self.analysis_logs.append(det_info)
            
            # Log detalhado do resultado da análise
            alert_value = result.get('alert_triggered', 0)
            logger.info("\n=== Processando Alert Triggered ===")
            logger.info(f"Alert value recebido: {alert_value}")
            logger.info(f"Tipo do alert value: {type(alert_value)}")
            
            # Garantir que alert_value seja int
            try:
                alert_value = int(alert_value)
                logger.info(f"Alert value convertido: {alert_value}")
                
                if alert_value == 1:
                    logger.warning(">>> ALERTA DETECTADO! Disparando notificação...")
                    self.analysis_logs.append(">>> ALERTA DETECTADO!")
                    
                    # Obter o frame atual para o alerta
                    _, frame = self.cap.read()
                    if frame is not None:
                        self.trigger_alert(frame=frame)
                        logger.info("Alerta disparado com sucesso")
                    else:
                        logger.error("Não foi possível capturar o frame para o alerta")
                else:
                    logger.info("Nenhum alerta necessário para este frame")
                    
            except (ValueError, TypeError) as e:
                logger.error(f"Erro ao processar alert_triggered: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Erro ao processar resultado: {str(e)}")
            self.analysis_logs.append(f"Erro ao processar resultado: {str(e)}")
            
    def _on_analysis_finished(self):
        """Chamado quando a análise é finalizada (com sucesso ou erro)."""
        logger.info(f"Análise do frame {self.current_frame_count} finalizada")
        self.analysis_in_progress = False
        if self.worker:
            self.worker.deleteLater()
            self.worker = None

    def handle_analysis_error(self, error_msg):
        """Trata erros na análise."""
        logger.error(f"Erro na análise do frame {self.current_frame_count}: {error_msg}")
        self.analysis_logs.append(f"ERRO no frame {self.current_frame_count}: {error_msg}")

    def trigger_alert(self, frame=None):
        """
        Dispara um alerta com o frame atual.
        Args:
            frame: Frame opcional. Se não fornecido, tenta capturar um novo frame.
        """
        logger.info("\n=== Disparando Alerta ===")
        if not self.cap or not self.cap.isOpened():
            logger.error("Erro: Nenhum vídeo conectado.")
            return

        if frame is None:
            # Se não recebeu um frame, tenta capturar o atual
            current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            logger.info(f"Posição atual do vídeo: frame {current_pos}")
            
            # Voltar um frame para garantir que pegamos o frame correto
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos - 1)
            ret, frame = self.cap.read()
            
            if not ret:
                logger.error("Não foi possível capturar o frame.")
                return
        else:
            logger.info("Usando frame fornecido para o alerta")

        # Tempo do vídeo em milissegundos
        current_time = int(self.cap.get(cv2.CAP_PROP_POS_MSEC))
        alert_time = datetime.now().strftime("%H:%M:%S")
        
        # Verifica se a pasta de logs existe, caso contrário, cria
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Define o caminho do arquivo de alerta
        alert_frame_path = os.path.join(log_dir, datetime.now().strftime("alert-%Y-%m-%d-%H-%M-%S.png"))

        cv2.imwrite(alert_frame_path, frame)

        # Adiciona o log visual
        item_widget = QWidget()
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(0, 0, 0, 0)

        thumb_pixmap = QPixmap(alert_frame_path).scaled(100, 75)
        thumb_label = QLabel()
        thumb_label.setPixmap(thumb_pixmap)
        item_layout.addWidget(thumb_label)

        text_label = QLabel(f"Tempo: {current_time}ms\nAlerta detectado")
        item_layout.addWidget(text_label)

        item_widget.setLayout(item_layout)
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        list_item.setData(0, current_time)  # Associa o tempo ao item

        self.logs_list.addItem(list_item)
        self.logs_list.setItemWidget(list_item, item_widget)

        # Não precisa enviar email aqui pois a API já envia
        logger.info("Alerta registrado - o email será enviado pela API")
        self.analysis_logs.append("Alerta registrado - o email será enviado pela API")

    def jump_to_alert(self, item):
        """Salta para 1 segundo antes do alerta."""
        if not self.cap:
            return

        alert_time = item.data(0)  # Recupera o tempo associado ao item
        target_time = max(0, alert_time - 1000)  # 1 segundo antes
        self.cap.set(cv2.CAP_PROP_POS_MSEC, target_time)

        # Atualiza manualmente o frame para garantir que o vídeo mostre o estado correto
        ret, frame = self.cap.read()
        if ret:
            # Redimensiona e exibe o frame
            frame = cv2.resize(frame, (self.video_width, self.video_height))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame.shape
            step = channel * width
            qimg = QImage(frame.data, width, height, step, QImage.Format_RGB888)

            # Exibe o frame no QLabel
            self.video_label.setPixmap(QPixmap.fromImage(qimg))

            # Certifica-se de que o overlay ainda está visível
            self.overlay_label.raise_()

    def save_settings(self):
        # Salva o intervalo de análise
        try:
            self.analysis_interval = int(self.interval_input.text())
            self.interval_input.setStyleSheet("")
        except ValueError:
            logger.error("Erro: Intervalo de análise inválido.")
            self.interval_input.setStyleSheet("border: 1px solid red;")

        # Reinicia o contador de frames para aplicar o novo intervalo
        self.current_frame_count = 0

if __name__ == "__main__":
    try:
        app = QAsyncApplication(sys.argv)
        loop = QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        window = SecurityCameraApp()
        window.show()
        
        with loop:
            loop.run_forever()
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {str(e)}")
        sys.exit(1)
