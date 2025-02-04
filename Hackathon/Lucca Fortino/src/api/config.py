from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

class Settings(BaseSettings):
    """Configurações da API VisionGuard."""
    
    # Modelo
    model_path: str = "models/best.pt"
    alert_threshold: float = 0.15  # Reduzido para corresponder ao threshold do frontend
    
    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "fiap.iadev.2023.team18@gmail.com"
    smtp_password: str = "yymr taas eeuw yptz"
    alert_email: str = "fiap.iadev.2023.team18@gmail.com"
    
    # API
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Logs
    log_level: str = "INFO"
    log_file: Optional[Path] = Path("logs/api.log")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"