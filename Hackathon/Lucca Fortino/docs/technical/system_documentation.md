# VisionGuard - Documentação Técnica

## Visão Geral do Sistema

O VisionGuard é um sistema avançado de monitoramento de segurança que utiliza inteligência artificial (YOLOv8) para detectar objetos cortantes em tempo real. O sistema é construído em Python, utilizando PyQt5 para interface gráfica e OpenCV para processamento de vídeo.

## Arquitetura do Sistema

### 1. Estrutura de Diretórios

```
├── art/                  # Recursos gráficos (overlays, etc)
├── cameras/             # Vídeos de exemplo para teste
├── data/               # Dados de treinamento e validação
├── docs/              # Documentação técnica e do usuário
├── logs/              # Logs do sistema
├── models/            # Modelos treinados e backups
├── src/               # Código fonte
│   ├── config/        # Configurações do sistema
│   │   ├── app_config.py       # Configurações centrais da aplicação
│   │   └── logging_config.py   # Configurações de logging
│   │
│   ├── core/          # Núcleo do sistema
│   │   ├── alert_manager.py    # Gerenciamento de alertas
│   │   ├── alert_utils.py      # Utilitários para alertas
│   │   ├── detector.py         # Detector YOLOv8
│   │   ├── email_sender.py     # Envio de emails
│   │   └── video_utils.py      # Utilitários de vídeo
│   │
│   ├── processing/    # Processamento de imagem (reservado)
│   │
│   ├── training/      # Módulos de treinamento
│   │   ├── config/             # Configs de treinamento
│   │   ├── dataset_manager.py  # Gestão de datasets
│   │   └── model_trainer.py    # Treinamento do modelo
│   │
│   ├── ui/           # Interface do usuário
│   │   ├── alert_dialog.py     # Diálogo de alertas
│   │   ├── alert_view.py       # Visualização de alertas
│   │   ├── analysis_manager.py # Gerenciador de análise
│   │   ├── camera_manager.py   # Gerenciador de câmera
│   │   ├── main_window.py      # Janela principal
│   │   ├── settings_tab.py     # Aba de configurações
│   │   ├── source_dialog.py    # Diálogo de fonte de vídeo
│   │   └── video_tab.py        # Aba de vídeo
│   │
│   ├── utils/        # Utilitários gerais
│   │
│   ├── workers/      # Workers assíncronos
│   │   └── analysis_worker.py  # Worker de análise
│   │
│   └── main.py       # Ponto de entrada da aplicação
│
└── tools/             # Scripts utilitários
```

### 2. Responsabilidades dos Módulos

#### 2.1 Config (src/config/)
- **app_config.py**
  - Configurações centralizadas do sistema
  - Validação de parâmetros
  - Gerenciamento de diretórios
  - Configurações de modelo, vídeo e alertas

- **logging_config.py**
  - Configuração do sistema de logs
  - Formatação de mensagens
  - Rotação de arquivos de log

#### 2.2 Core (src/core/)
- **alert_manager.py**
  - Gerenciamento do ciclo de vida dos alertas
  - Persistência de dados
  - Filtragem de alertas

- **alert_utils.py**
  - Funções auxiliares para processamento de alertas
  - Formatação de mensagens
  - Validações

- **detector.py**
  - Interface com YOLOv8
  - Processamento de frames
  - Otimizações de inferência

- **email_sender.py**
  - Envio assíncrono de emails
  - Formatação de mensagens
  - Buffer de notificações

- **video_utils.py**
  - Processamento de vídeo
  - Manipulação de frames
  - Otimizações de captura

#### 2.3 Training (src/training/)
- **dataset_manager.py**
  - Preparação de datasets
  - Augmentação de dados
  - Validação de dados

- **model_trainer.py**
  - Configuração de treinamento
  - Monitoramento de métricas
  - Salvamento de checkpoints

#### 2.4 UI (src/ui/)
- **alert_dialog.py & alert_view.py**
  - Visualização de alertas
  - Interação com usuário
  - Formatação de dados

- **analysis_manager.py**
  - Coordenação de análise
  - Gerenciamento de estado
  - Comunicação com workers

- **camera_manager.py**
  - Gestão de fontes de vídeo
  - Controle de captura
  - Buffer de frames

- **main_window.py**
  - Layout principal
  - Navegação
  - Coordenação de componentes

- **settings_tab.py**
  - Interface de configuração
  - Validação de entrada
  - Persistência de preferências

- **source_dialog.py**
  - Seleção de fonte de vídeo
  - Validação de entrada
  - Preview de câmera

- **video_tab.py**
  - Visualização de vídeo
  - Controles de playback
  - Overlay de detecções

#### 2.5 Workers (src/workers/)
- **analysis_worker.py**
  - Processamento assíncrono
  - Gerenciamento de fila
  - Comunicação via sinais Qt

## Sistema de Processamento Assíncrono

### Arquitetura Multi-thread
1. **Thread Principal (UI)**
   - Mantém interface responsiva
   - Gerencia eventos do usuário
   - Coordena workers

2. **Workers de Análise**
   - Processam frames independentemente
   - Executam detecção em background
   - Evitam bloqueio da UI

3. **Sistema de Filas**
   - Gerencia múltiplos frames
   - Prioriza processamento
   - Limita uso de recursos

## Sistema Inteligente de Alertas

### Níveis de Criticidade
1. **Baixa Prioridade**
   - Detecções com confiança < 50%
   - Armazenamento temporário
   - Sem notificação imediata

2. **Média Prioridade**
   - Confiança entre 50% e 75%
   - Armazenamento por 24h
   - Notificação na interface

3. **Alta Prioridade**
   - Confiança > 75%
   - Armazenamento permanente
   - Alerta imediato
   - Captura de frame

## Configurações do Sistema

### 1. Configurações do Modelo
```python
MODEL_CONFIG = {
    'path': 'models/best.pt',
    'confidence_threshold': 0.25,
    'alert_threshold': 0.5,
    'target_height': 320
}
```

### 2. Configurações de Vídeo
```python
VIDEO_CONFIG = {
    'frame_interval': 30,
    'analysis_interval': 5,
    'max_concurrent_workers': 2,
    'frame_timeout': 5.0,
    'width': 640,
    'height': 480
}
```

### 3. Configurações de Alertas
```python
ALERT_CONFIG = {
    'min_time_between_alerts': 1000,
    'save_frames': True,
    'save_detections': True,
    'enable_email_alerts': True,
    'email_buffer_interval': 20
}
```

## Requisitos do Sistema

### Software
- Python 3.x
- PyQt5
- OpenCV
- YOLOv8
- CUDA (opcional para aceleração GPU)

### Hardware Recomendado
- CPU: 4+ cores
- RAM: 8GB+
- GPU: NVIDIA com suporte CUDA (opcional)
- Armazenamento: 500MB+ para logs