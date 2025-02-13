# Interface do Usuário (src/ui/)

## Visão Geral
Interface gráfica construída com PyQt5, implementando um design modular e responsivo para monitoramento em tempo real, análise de vídeo e gerenciamento de alertas.

## Componentes Principais

### SecurityCameraApp (main_window.py)
Janela principal da aplicação que integra todos os componentes.

#### Estrutura da Interface
```
MainWindow
├── Central Widget
│   ├── Main Area (2/3 width)
│   │   ├── Video Tab
│   │   ├── Settings Tab
│   │   └── About Tab
│   └── Alert Area (1/3 width)
│       └── Alert View
└── Status Bar
```

### Gerenciadores

#### CameraManager
- Controle de fonte de vídeo
- Suporte a câmeras e arquivos
- Gerenciamento de conexão
- Controle de playback

#### AnalysisManager
- Processamento de frames
- Gerenciamento de workers
- Controle de análise
- Métricas de performance

## Funcionalidades Principais

### 1. Controle de Vídeo
```python
def connect_camera(self)
def disconnect_camera(self)
def toggle_play_pause(self)
def update_frame(self)
```
- Conexão com múltiplas fontes
- Controles de playback
- Redimensionamento automático
- Preview em tempo real

### 2. Sistema de Análise
- Processamento assíncrono
- Detecção em tempo real
- Métricas de performance
- Logging de resultados

### 3. Gerenciamento de Alertas
- Visualização em tempo real
- Histórico de alertas
- Navegação temporal
- Detalhes de detecções

## Interface de Usuário

### Tabs

#### 1. Video Tab
- Display de vídeo
- Controles de playback
- Logs de análise
- Métricas em tempo real

#### 2. Settings Tab
- Configurações do modelo
- Parâmetros de vídeo
- Configurações de alerta
- Preferências de interface

#### 3. About Tab
- Informações do projeto
- Créditos
- Documentação
- Links úteis

### Alert View
- Lista de alertas
- Detalhes de detecções
- Navegação temporal
- Gerenciamento de alertas

## Sistema de Eventos

### Timers
```python
# Frame Timer
self.frame_timer = QTimer(self)
self.frame_timer.timeout.connect(self.update_frame)

# Status Timer
self.status_timer = QTimer(self)
self.status_timer.timeout.connect(self.update_status)
```

### Signals/Slots
- analysis_complete
- analysis_error
- metrics_update
- jump_to_time
- alert_deleted

## Otimizações

### Performance
- Atualização eficiente de frames
- Processamento assíncrono
- Cache de interface
- Throttling de eventos

### Interface
- Layout responsivo
- Controles intuitivos
- Feedback visual
- Status em tempo real

## Configurações

### UI_CONFIG
```python
UI_CONFIG = {
    'window_title': str,
    'window_size': tuple,
    'update_interval': int
}
```

### VIDEO_CONFIG
```python
VIDEO_CONFIG = {
    'frame_interval': int,
    'target_height': int
}
```

## Tratamento de Erros

### Níveis de Erro
- Erros críticos (inicialização)
- Erros de conexão
- Erros de processamento
- Erros de interface

### Feedback
- Mensagens de status
- Diálogos de erro
- Logs detalhados
- Recuperação automática

## Métricas e Monitoramento

### Performance
- FPS de vídeo
- Tempo de análise
- Uso de workers
- Taxa de detecção

### Status
- Estado da conexão
- Frames processados
- Total de detecções
- Alertas gerados

## Considerações de Uso

### Inicialização
- Verificar dependências
- Inicializar gerenciadores
- Configurar interface
- Conectar sinais

### Manutenção
- Monitorar performance
- Verificar conexões
- Gerenciar recursos
- Atualizar configurações

## Dependências
- PyQt5
- OpenCV
- NumPy
- Logging system

## Boas Práticas
- Separação de responsabilidades
- Tratamento de erros robusto
- Feedback constante ao usuário
- Limpeza adequada de recursos