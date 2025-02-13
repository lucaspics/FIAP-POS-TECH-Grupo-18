# Detector (src/core/detector.py)

## Visão Geral
Componente responsável pela detecção de objetos utilizando o modelo YOLOv8. Implementa otimizações para processamento local e gerenciamento eficiente de recursos.

## Classes Principais

### ObjectDetector
Classe principal que encapsula toda a lógica de detecção.

#### Inicialização
```python
def __init__(self, model_path: Optional[str] = None):
```
- Carrega o modelo YOLOv8
- Realiza warmup para reduzir latência inicial
- Configura parâmetros de otimização (target_height, confidence_threshold)

#### Métodos Principais

##### detect()
```python
async def detect(self, image: np.ndarray, conf_threshold: Optional[float] = None) -> DetectionResult
```
- Processamento assíncrono de frames
- Otimização de memória GPU
- Limpeza automática de recursos CUDA
- Retorna detecções encontradas com confiança e coordenadas

##### draw_detections()
```python
def draw_detections(self, image: np.ndarray, detections: List[Detection]) -> np.ndarray
```
- Renderiza as detecções na imagem
- Otimizado para visualização em tempo real
- Inclui labels e bounding boxes

## Otimizações Implementadas

### 1. Gerenciamento de Memória
- Limpeza proativa de memória CUDA
- Buffer circular para frames
- Liberação automática de recursos

### 2. Performance
- Processamento assíncrono
- Warmup do modelo
- Redimensionamento inteligente de frames
- Cache de resultados

### 3. GPU
- Suporte a CUDA quando disponível
- Batch processing
- Otimização de transferências de memória

## Integração com Sistema

### Entrada
- Frames de vídeo em formato numpy array (BGR)
- Parâmetros de configuração (confidence_threshold, target_height)

### Saída
- DetectionResult contendo:
  * Lista de detecções (classe, confiança, coordenadas)
  * Timestamp
  * Métricas de performance

## Métricas e Monitoramento
- Tempo de processamento por frame
- Total de detecções
- Uptime do detector
- Informações do modelo carregado

## Considerações de Uso
- Requer inicialização prévia do modelo
- Gerenciamento automático de recursos GPU
- Thread-safe para uso em workers paralelos
- Suporte a configuração dinâmica de parâmetros

## Dependências
- ultralytics (YOLOv8)
- OpenCV
- PyTorch
- NumPy
- asyncio para processamento assíncrono