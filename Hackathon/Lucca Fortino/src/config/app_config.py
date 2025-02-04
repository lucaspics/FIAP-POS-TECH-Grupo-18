"""
Configurações gerais da aplicação
"""

# Configurações de vídeo
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
DEFAULT_FPS = 30  # ~33ms por frame
FRAME_INTERVAL = 30  # Intervalo em milissegundos

# Configurações de análise
DEFAULT_ANALYSIS_INTERVAL = 15  # Reduzido para 0.5s em 30fps
DEFAULT_CONFIDENCE_THRESHOLD = 0.15

# Configurações de API
API_URL = "http://localhost:8000/detect"
API_TIMEOUT = {
    "total": 20,     # 20 segundos total
    "connect": 5     # 5 segundos para conectar
}

# Configurações de email
DEFAULT_EMAIL = "fiap.iadev.2023.team18@gmail.com"

# Configurações de retry
MAX_RETRIES = 2  # Reduzido para evitar acúmulo de workers
RETRY_DELAY = 1.0  # segundos

# Configurações de diretórios
LOG_DIRS = {
    "base": "logs",
    "frames": "logs/frames",
    "results": "logs/results",
    "errors": "logs/errors"
}

# Configurações de interface
OVERLAY_PATH = "src/assets/images/cam_overlay.png"

# Configurações de alerta
MIN_TIME_BETWEEN_ALERTS = 5000  # Milissegundos (5 segundos)

# Configurações de níveis de confiança
CONFIDENCE_LEVELS = {
    "HIGH": 0.75,    # 75%
    "MEDIUM": 0.50,  # 50%
    "LOW": 0.15      # 15%
}

# Configurações de confirmações necessárias
REQUIRED_DETECTIONS = {
    "HIGH": 1,    # Imediato
    "MEDIUM": 3,  # 3 detecções
    "LOW": 5      # 5 detecções
}

# Janelas de tempo para confirmações (em segundos)
DETECTION_WINDOWS = {
    "HIGH": 0,    # Imediato
    "MEDIUM": 5,  # 5 segundos
    "LOW": 10     # 10 segundos
}

# Configurações de buffer de imagens
MAX_BUFFER_IMAGES = 5  # Número máximo de imagens a serem enviadas no email