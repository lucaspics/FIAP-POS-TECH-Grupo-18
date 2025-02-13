# AnalysisWorker (src/workers/analysis_worker.py)

## Visão Geral
Worker thread responsável pelo processamento assíncrono de frames de vídeo. Implementa um sistema de análise não-bloqueante que mantém a interface responsiva durante o processamento pesado.

## Características Principais

### Processamento Assíncrono
- Executa em thread separada (QThread)
- Event loop assíncrono dedicado
- Gerenciamento automático de recursos

### Sistema de Sinais
```python
# Sinais principais
analysis_complete = pyqtSignal(dict)  # Resultado da análise
analysis_error = pyqtSignal(str)      # Notificação de erros
metrics_update = pyqtSignal(dict)     # Métricas de performance
```

## Componentes Compartilhados

### Instâncias Estáticas
```python
_detector: Optional[ObjectDetector] = None
_alert_manager: Optional[AlertManager] = None
_event_loop: Optional[asyncio.AbstractEventLoop] = None
```

### Inicialização
```python
@classmethod
def initialize(cls, model_path: str, alert_dir: str)
```
- Inicializa detector e alert manager
- Configuração única para todos os workers
- Gerenciamento de recursos compartilhados

## Pipeline de Processamento

### 1. Preparação do Frame
- Cópia do frame para processamento seguro
- Conversão de formato (RGB para BGR)
- Redimensionamento conforme configuração

### 2. Análise
```python
async def analyze(self) -> Optional[Dict[str, Any]]
```
- Processamento assíncrono do frame
- Integração com detector
- Geração de alertas quando necessário
- Coleta de métricas

### 3. Gerenciamento de Resultados
- Emissão de sinais com resultados
- Tratamento de erros
- Atualização de métricas
- Notificação de alertas

## Otimizações

### Performance
- Processamento em thread separada
- Event loop assíncrono
- Cache de recursos compartilhados
- Limpeza proativa de memória

### Recursos
- Gerenciamento automático de threads
- Limpeza de recursos no encerramento
- Controle de ciclo de vida dos componentes
- Tratamento de exceções

## Métricas Coletadas

### Performance
```python
metrics = {
    'frame_number': self.frame_number,
    'analysis_time': analysis_time,
    'fps': 1.0 / analysis_time,
    'detection_count': detection_count,
    'video_time': self.video_time,
    'timestamp': datetime.now().isoformat()
}
```

## Integração com Sistema

### Entrada
- Frames RGB
- Número do frame
- Tempo do vídeo

### Saída
- Resultados de detecção
- Alertas gerados
- Métricas de performance
- Notificações de erro

## Considerações de Uso

### Inicialização
- Requer chamada ao método initialize() antes do uso
- Configuração através de MODEL_CONFIG e VIDEO_CONFIG
- Verificação de recursos disponíveis

### Limpeza
```python
@classmethod
def cleanup(cls)
```
- Liberação de recursos compartilhados
- Fechamento de event loops
- Limpeza de memória

## Dependências
- PyQt5 para threading e sinais
- OpenCV para processamento de imagem
- asyncio para operações assíncronas
- Detector e AlertManager do core

## Boas Práticas
- Sempre inicializar antes do uso
- Tratar sinais de erro apropriadamente
- Monitorar métricas de performance
- Limpar recursos após o uso