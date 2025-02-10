# Plano de Migração para Arquitetura Assíncrona com Python Multiprocessing

## 1. Visão Geral do Sistema Atual

### Problemas Identificados
- Processamento síncrono causando congestionamento
- Timeouts frequentes na API
- Acúmulo de frames para análise
- Falta de controle de fluxo

### Componentes Atuais
- UI (VideoTab): Captura e exibe frames
- AnalysisWorker: Processa frames individualmente
- API: Endpoint síncrono para detecção
- AlertManager: Gerencia notificações

## 2. Nova Arquitetura Proposta

### 2.1 Componentes Principais

#### Producer (UI)
- Modificar VideoTab para usar Queue.Queue para buffer de frames
- Implementar buffer circular limitado
- Adicionar controle de fluxo baseado em tamanho da fila
- Manter interface atual com usuário

#### Filas (multiprocessing.Queue)
- frames_queue: Frames para processamento
- results_queue: Resultados das análises
- alerts_queue: Notificações de alertas

#### Workers (ProcessPoolExecutor)
- Pool de processos para processamento paralelo
- Cada processo executa uma instância do detector
- Balanceamento automático de carga
- Recuperação de falhas integrada

#### Result Handler (ThreadPoolExecutor)
- Thread dedicada para processar resultados
- Atualização da UI via signals do Qt
- Integração com sistema de alertas existente

### 2.2 Fluxo de Dados

1. Captura de Frame
   - UI captura frame do vídeo
   - Aplica redimensionamento
   - Verifica espaço no buffer
   - Adiciona à frames_queue

2. Processamento
   - Worker obtém frame da fila
   - Processa usando modelo existente
   - Adiciona resultado à results_queue
   - Gerencia memória automaticamente

3. Resultados
   - Result Handler processa results_queue
   - Emite signals para atualizar UI
   - Gera alertas se necessário
   - Atualiza logs e estatísticas

## 3. Plano de Implementação

### Fase 1: Estrutura Base
1. Criar Classes Base
```python
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from multiprocessing import Queue, Value, Lock
from queue import Queue as ThreadQueue
import numpy as np

class FrameProcessor:
    def __init__(self, max_workers=4):
        self.frames_queue = Queue(maxsize=30)  # 1 segundo de buffer em 30fps
        self.results_queue = Queue()
        self.alerts_queue = Queue()
        self.running = Value('b', True)
        self.worker_pool = ProcessPoolExecutor(max_workers=max_workers)
        self.result_handler = ThreadPoolExecutor(max_workers=1)
        
    def start(self):
        self.result_handler.submit(self._handle_results)
        for _ in range(self.worker_pool._max_workers):
            self.worker_pool.submit(self._process_frames)
            
    def stop(self):
        self.running.value = False
        self.worker_pool.shutdown()
        self.result_handler.shutdown()
```

2. Implementar Controle de Fluxo
```python
class FrameBuffer:
    def __init__(self, maxsize=30):
        self.queue = ThreadQueue(maxsize=maxsize)
        self.lock = Lock()
        
    def put(self, frame):
        if self.queue.full():
            self.queue.get()  # Remove frame mais antigo
        self.queue.put(frame)
        
    def get(self):
        return self.queue.get() if not self.queue.empty() else None
```

### Fase 2: Adaptação do VideoTab
1. Modificar Captura de Frames
```python
class VideoTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.frame_processor = FrameProcessor()
        self.frame_buffer = FrameBuffer()
        
    def process_frame(self, frame):
        if frame is not None:
            self.frame_buffer.put(frame)
            if not self.frame_processor.frames_queue.full():
                self.frame_processor.frames_queue.put(frame)
```

2. Implementar Handler de Resultados
```python
    def handle_detection_result(self, result):
        if result['alert_triggered']:
            self.add_alert(result)
        self.update_display(result)
```

### Fase 3: Workers
1. Implementar Processamento
```python
def process_frame(frame, model):
    try:
        results = model.detect(frame)
        return {
            'timestamp': time.time(),
            'detections': results,
            'alert_triggered': check_alert_conditions(results)
        }
    except Exception as e:
        return {'error': str(e)}
```

2. Gerenciar Pool
```python
def _process_frames(self):
    while self.running.value:
        try:
            frame = self.frames_queue.get(timeout=1)
            result = process_frame(frame, self.model)
            self.results_queue.put(result)
        except Empty:
            continue
        except Exception as e:
            logger.error(f"Erro no processamento: {e}")
```

### Fase 4: Result Handler
1. Implementar Processamento de Resultados
```python
def _handle_results(self):
    while self.running.value:
        try:
            result = self.results_queue.get(timeout=1)
            if 'error' in result:
                self.handle_error(result['error'])
            else:
                self.handle_detection_result(result)
        except Empty:
            continue
```

2. Integrar com AlertManager
```python
def handle_detection_result(self, result):
    if result['alert_triggered']:
        self.alerts_queue.put(result)
        self.alert_manager.process_alert(result)
```

## 4. Benefícios

1. Performance
   - Processamento paralelo eficiente
   - Sem dependências externas
   - Melhor utilização de CPU

2. Confiabilidade
   - Recuperação automática de erros
   - Sem perda de frames importantes
   - Gerenciamento de memória automático

3. Simplicidade
   - Código mais limpo e mantível
   - Debugging mais simples
   - Fácil de expandir

## 5. Métricas de Sucesso

1. Performance
   - Processamento estável em 30fps
   - Latência máxima de 100ms
   - Uso eficiente de CPU

2. Recursos
   - Memória controlada
   - CPU balanceada entre cores
   - Sem vazamentos de recursos

3. Confiabilidade
   - Zero perda de frames críticos
   - Recuperação instantânea de erros
   - UI responsiva

## 6. Próximos Passos

1. Implementar classes base
2. Adaptar VideoTab
3. Implementar workers
4. Integrar result handler
5. Testar e otimizar

## 7. Vantagens desta Abordagem

1. Simplicidade
   - Usa apenas biblioteca padrão Python
   - Sem necessidade de serviços externos
   - Fácil de debugar e manter

2. Performance
   - Aproveita todos os cores da CPU
   - Gerenciamento automático de memória
   - Baixa latência

3. Confiabilidade
   - Menos pontos de falha
   - Recuperação automática
   - Mais fácil de monitorar