# Roteiro de Apresentação do VisionGuard

Boa noite a todos! Hoje vou apresentar o VisionGuard, nosso sistema de vigilância inteligente desenvolvido para detectar e alertar sobre situações de risco em tempo real.

## Estrutura do Projeto

Antes de entrarmos nos detalhes técnicos, é importante entender como o projeto está organizado. O VisionGuard é dividido em várias partes principais:

1. **Sistema de Treinamento** (`src/training/`)
   - Gerenciamento de datasets
   - Treinamento do modelo YOLOv8
   - Validação e métricas de performance

2. **Aplicação Principal** (`src/core/`)
   - Detector de objetos
   - Gerenciador de alertas
   - Sistema de notificações
   - Utilitários de processamento de vídeo

3. **Interface do Usuário** (`src/ui/`)
   - Janela principal
   - Visualização de câmeras
   - Painel de alertas
   - Configurações do sistema

4. **Configuração e Utilitários** (`src/config/` e `src/utils/`)
   - Configurações da aplicação
   - Logging
   - Ferramentas de desenvolvimento

5. **Processamento Assíncrono** (`src/workers/`)
   - Workers de análise
   - Processamento em background
   - Gerenciamento de recursos

Esta estrutura modular nos permite:
- Manter o código organizado e manutenível
- Facilitar o desenvolvimento em paralelo
- Isolar funcionalidades específicas
- Melhorar a testabilidade do sistema

## Arquitetura e Funcionamento

O VisionGuard utiliza uma arquitetura modular baseada em Python e Qt. Vamos examinar como o sistema é inicializado:

[Mostrar: src/main.py, linhas 7-22]
```python
def main():
    """Função principal da aplicação."""
    try:
        # Inicializar aplicação Qt
        app = QApplication(sys.argv)
        
        # Criar e exibir janela principal
        window = SecurityCameraApp()
        window.show()
```

A inicialização envolve vários componentes críticos:

[Mostrar: src/ui/main_window.py, linhas 42-69]
```python
def __init__(self):
    """Inicializa a aplicação."""
    super().__init__()
    self.init_managers()
    self.setup_ui()
    self.setup_connections()
    self.setup_timers()
```

O processo de inicialização:
1. Carrega configurações do sistema
2. Inicializa gerenciadores principais
3. Configura a interface gráfica
4. Estabelece conexões entre componentes
5. Configura timers para atualização contínua

## Pipeline de Processamento Detalhado

Vamos mergulhar profundamente em cada etapa do processamento, entendendo como o sistema trabalha desde a captura do frame até o envio da notificação.

### 1. Captura e Validação do Frame

[Mostrar: src/ui/main_window.py, linhas 257-291]
```python
def update_frame(self):
    """Atualiza o frame atual."""
    try:
        if self.camera_manager.is_camera:
            ret, frame = self.camera_manager.read_frame()
        else:
            ret, frame = self.camera_manager.cap.read()
```

O processo inicia com a captura do frame, que pode vir de duas fontes:
- **Câmera ao vivo**: Usando OpenCV (cv2.VideoCapture) para captura em tempo real
- **Arquivo de vídeo**: Leitura sequencial dos frames armazenados

Cada frame capturado passa por um processo rigoroso de validação:

[Mostrar: src/core/video_utils.py, linhas 14-42]
```python
def validate_frame(frame: np.ndarray) -> bool:
    """Valida se um frame é válido para processamento."""
    if frame is None:
        return False
        
    try:
        if not isinstance(frame, np.ndarray):
            return False
            
        if len(frame.shape) != 3:
            return False
            
        height, width, channels = frame.shape
        if height <= 0 or width <= 0 or channels != 3:
            return False
```

Esta validação garante que:
1. O frame existe e não é nulo
2. É uma matriz numpy tridimensional (altura x largura x canais)
3. Tem dimensões válidas
4. Possui os 3 canais de cor necessários (BGR)

### 2. Pré-processamento do Frame

Após a validação, o frame passa por um processo de preparação:

[Mostrar: src/core/video_utils.py, linhas 44-81]
```python
def resize_frame(frame: np.ndarray, 
                target_height: Optional[int] = None,
                keep_aspect_ratio: bool = True) -> Optional[np.ndarray]:
    """Redimensiona um frame."""
    try:
        if target_height is None:
            target_height = VIDEO_CONFIG['height']
            
        height, width = frame.shape[:2]
        
        if keep_aspect_ratio:
            # Manter proporção
            target_width = int(width * (target_height / height))
        else:
            # Usar largura do VIDEO_CONFIG
            target_width = VIDEO_CONFIG['width']
```

O redimensionamento é crucial pois:
1. Padroniza o tamanho dos frames para o detector
2. Mantém a proporção original da imagem (aspect ratio)
3. Reduz a carga de processamento
4. Otimiza o uso de memória
5. Garante performance consistente

### 3. Processamento pelo Detector

O frame preparado é então enviado para o detector YOLOv8, que opera de forma assíncrona:

[Mostrar: src/core/detector.py, linhas 124-149]
```python
async def detect(self, image: np.ndarray, conf_threshold: Optional[float] = None) -> DetectionResult:
    """Realiza detecção de objetos em uma imagem."""
    try:
        # Usar threshold das configurações se não especificado
        threshold = conf_threshold if conf_threshold is not None else self.confidence_threshold

        # Limpar memória CUDA se disponível
        if hasattr(torch, 'cuda'):
            torch.cuda.empty_cache()

        # Executar inferência de forma assíncrona
        def inference_job():
            with torch.no_grad():
                return self.model(image, conf=threshold, imgsz=image.shape[:2])[0]

        results = await asyncio.to_thread(inference_job)
```

O processo de detecção é otimizado em vários níveis:
1. **Gerenciamento de Memória**:
   - Limpeza automática da memória CUDA
   - Uso de `torch.no_grad()` para reduzir consumo de memória
   - Liberação proativa de recursos

2. **Processamento Assíncrono**:
   - Uso de `asyncio.to_thread` para não bloquear a interface
   - Permite processamento paralelo de múltiplos frames
   - Mantém a responsividade do sistema

3. **Configuração Dinâmica**:
   - Threshold de confiança ajustável
   - Dimensões de entrada adaptativas
   - Otimizações específicas para GPU/CPU

### 4. Processamento dos Resultados

Os resultados brutos do detector são processados e estruturados:

[Mostrar: src/core/detector.py, linhas 150-185]
```python
# Processar resultados
boxes_np = results.boxes.data.cpu().numpy()
del results  # Liberar memória

if hasattr(torch, 'cuda'):
    torch.cuda.empty_cache()

# Processar detecções
detections = []
for box in boxes_np:
    try:
        x1, y1, x2, y2, conf, cls = map(float, box)
        cls_id = int(cls)
        
        detection = Detection(
            class_name=str(self.classes[cls_id]),
            confidence=float(conf),
            bbox=[float(x1), float(y1), float(x2), float(y2)]
        )
        detections.append(detection)
```

O processamento envolve:
1. **Conversão de Dados**:
   - Transferência de tensores da GPU para CPU
   - Conversão para numpy arrays
   - Normalização de coordenadas

2. **Estruturação**:
   - Criação de objetos Detection
   - Mapeamento de classes
   - Cálculo de coordenadas normalizadas

3. **Otimização de Memória**:
   - Liberação imediata de tensores
   - Limpeza de cache CUDA
   - Gerenciamento de recursos

### 5. Geração e Persistência de Alertas

Quando detecções relevantes são identificadas, o sistema de alertas é acionado:

[Mostrar: src/core/alert_manager.py, linhas 124-167]
```python
async def process_detection(self, result: DetectionResult, frame: Optional[cv2.Mat] = None, video_time: int = 0) -> bool:
    """Processa um resultado de detecção e gera alertas se necessário."""
    try:
        # Verificar se há detecções com confiança suficiente
        high_confidence_detections = [
            det for det in result.detections 
            if det.confidence >= self.min_confidence
        ]
```

O processo de alerta é composto por várias etapas:

1. **Filtragem de Detecções**:
   - Aplicação de threshold de confiança
   - Verificação de intervalo entre alertas
   - Validação de critérios específicos

2. **Geração de Metadados**:
   - Identificador único baseado em timestamp
   - Informações temporais precisas
   - Dados de contexto do vídeo

3. **Persistência de Dados**:
   ```python
   # Salvar dados do alerta
   json_path = self.alert_dir / 'data' / f"{alert_id}.json"
   with open(json_path, 'w', encoding='utf-8') as f:
       json.dump(alert_data, f, indent=2, ensure_ascii=False)
   ```
   - Estruturação em JSON

4. **Armazenamento de Imagens**:
   ```python
   if frame is not None and ALERT_CONFIG['save_frames']:
       frame_with_detections = self.detector.draw_detections(frame, high_confidence_detections)
       image_path = images_dir / f"{alert_id}.jpg"
       success = cv2.imwrite(str(image_path), frame_with_detections)
   ```
   - Desenho de bounding boxes
   - Compressão otimizada
   - Organização em diretórios

### 6. Sistema de Notificações

O sistema de notificações utiliza um worker dedicado para processamento assíncrono:

[Mostrar: src/core/email_sender.py, linhas 142-186]
```python
async def send_alert(self,
                    recipient_email: str,
                    detections: List[Dict],
                    frame: Optional[cv2.Mat] = None,
                    video_time: int = 0) -> bool:
    """Envia um alerta por email de forma assíncrona."""
    try:
        # Criar mensagem
        msg = self._create_message(
            recipient_email,
            detections,
            [frame] if frame is not None else [],
            [video_time] if frame is not None else []
        )
        
        # Adicionar à fila do worker
        await self.worker.queue.put({
            'message': msg
        })
```

O processo de notificação é gerenciado em camadas:

1. **Preparação da Mensagem**:
   - Formatação HTML responsiva
   - Processamento de imagens
   - Estruturação de dados

2. **Gerenciamento de Fila**:
   - Fila assíncrona com asyncio.Queue
   - Priorização de mensagens
   - Controle de fluxo

3. **Worker Dedicado**:
   ```python
   def _run_worker(self):
       """Loop principal do worker."""
       loop = asyncio.new_event_loop()
       asyncio.set_event_loop(loop)
       
       while self.running:
           try:
               # Processar emails da fila
               while not self.queue.empty():
                   email_data = loop.run_until_complete(self.queue.get())
                   self._send_email(email_data)
                   self.queue.task_done()
   ```
   - Loop assíncrono dedicado
   - Gerenciamento de conexões SMTP
   - Retry automático em falhas

## Conclusão

O VisionGuard representa um avanço significativo em sistemas de vigilância inteligente, combinando:
- Detecção precisa em tempo real
- Gerenciamento eficiente de recursos
- Sistema robusto de notificações
- Interface intuitiva

Estamos à disposição para perguntas e podemos fazer demonstrações específicas de qualquer funcionalidade que desejarem ver em mais detalhes.