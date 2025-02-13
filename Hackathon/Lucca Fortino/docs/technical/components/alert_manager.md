# AlertManager (src/core/alert_manager.py)

## Visão Geral
Sistema responsável pelo gerenciamento de alertas, incluindo armazenamento, rotação e notificações. Implementa um sistema robusto de persistência de dados e notificações por email.

## Funcionalidades Principais

### 1. Gerenciamento de Alertas
- Processamento de detecções
- Armazenamento de imagens e metadados
- Sistema de rotação de alertas antigos
- Controle de intervalo entre alertas

### 2. Estrutura de Diretórios
```
alerts/
├── data/      # Dados JSON dos alertas ativos
├── images/    # Imagens dos alertas ativos
└── archive/   # Alertas e imagens arquivados
```

## Componentes Principais

### Inicialização
```python
def __init__(self, detector: ObjectDetector, min_confidence: float = 0.25, max_alerts: int = 1000)
```
- Configuração de diretórios
- Inicialização do EmailSender
- Carregamento de alertas existentes
- Configuração de limites e thresholds

### Processamento de Alertas
```python
async def process_detection(self, result: DetectionResult, frame: Optional[cv2.Mat], video_time: int) -> bool
```
- Validação de detecções por confiança
- Controle de intervalo entre alertas
- Salvamento de imagens e metadados
- Integração com sistema de email

## Sistema de Armazenamento

### Estrutura de Dados
```python
alert_data = {
    "alert_id": str,          # ID único do alerta
    "timestamp": str,         # Timestamp ISO
    "video_time": int,        # Tempo do vídeo em ms
    "detections": List[Dict], # Lista de detecções
    "confidence_threshold": float,
    "has_image": bool,        # Indica se há imagem
    "image_path": str         # Caminho da imagem
}
```

### Rotação de Alertas
- Sistema automático de arquivamento
- Manutenção do limite máximo de alertas
- Preservação de dados históricos
- Gerenciamento de espaço em disco

## Sistema de Notificações

### Email
- Envio assíncrono de alertas
- Suporte a anexos de imagem
- Configuração flexível de destinatários
- Throttling automático

### Métricas e Estatísticas
```python
stats = {
    "total_alerts": int,
    "current_alerts": int,
    "archived_alerts": int,
    "last_alert": str,
    "disk_usage_mb": float,
    "email_enabled": bool
}
```

## Otimizações

### Performance
- Processamento assíncrono
- Cache de metadados
- Compressão de imagens
- Limpeza automática de recursos

### Armazenamento
- Sistema de rotação automática
- Gerenciamento de espaço em disco
- Arquivamento inteligente
- Backup de metadados

## Integração com Sistema

### Entrada
- Resultados de detecção
- Frames de vídeo
- Configurações de alerta
- Thresholds de confiança

### Saída
- Status de processamento
- Notificações por email
- Métricas e estatísticas
- Histórico de alertas

## Configurações Principais
```python
ALERT_CONFIG = {
    'enable_email_alerts': bool,
    'notification_email': str,
    'min_time_between_alerts': int,
    'save_frames': bool
}
```

## Considerações de Uso

### Inicialização
- Requer detector configurado
- Diretórios de armazenamento
- Configurações de email
- Thresholds de alerta

### Manutenção
- Rotação regular de alertas
- Monitoramento de espaço
- Backup de dados
- Verificação de logs

## Dependências
- OpenCV para processamento de imagem
- Sistema de email assíncrono
- Sistema de arquivos
- Logger configurável

## Boas Práticas
- Monitorar uso de disco
- Configurar thresholds apropriados
- Implementar backup regular
- Verificar logs de erro