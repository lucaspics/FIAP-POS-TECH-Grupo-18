"""
Configurações gerais da aplicação
"""

# Configurações de vídeo
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
DEFAULT_FPS = 30  # ~33ms por frame
FRAME_INTERVAL = 30  # Intervalo em milissegundos

# Configurações de análise
DEFAULT_ANALYSIS_INTERVAL = 15  # Frames entre cada análise
DEFAULT_CONFIDENCE_THRESHOLD = 0.15

# Configurações de API
API_URL = "http://localhost:8000/detect"
API_TIMEOUT = {
    "total": 10,        # 10 segundos total
    "connect": 2,       # 2 segundos para conectar
    "sock_connect": 2,  # 2 segundos para conectar socket
    "sock_read": 5      # 5 segundos para ler dados
}

# Configurações de email
DEFAULT_EMAIL = "fiap.iadev.2023.team18@gmail.com"

# Configurações de retry
MAX_RETRIES = 3
RETRY_DELAY = 0.2  # segundos

# Configurações de diretórios
LOG_DIRS = {
    "base": "logs",
    "frames": "logs/frames",
    "results": "logs/results",
    "errors": "logs/errors"
}

# Configurações de interface
OVERLAY_PATH = "src/assets/images/cam_overlay.png"