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