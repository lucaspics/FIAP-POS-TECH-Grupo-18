# Fluxo de Dados do VisionGuard

## Diagrama de Fluxo Principal

```mermaid
graph TD
    A[Camera/Video Input] --> B[CameraManager]
    B --> C[VideoTab]
    B --> D[AnalysisWorker]
    D --> E[Detector]
    E --> F[AlertManager]
    F --> G[AlertView]
    F --> H[EmailSender]
    
    subgraph UI Layer
        C
        G
    end
    
    subgraph Processing Layer
        D
        E
    end
    
    subgraph Data Layer
        F
        H
    end
```

## Fluxo de Processamento Detalhado

1. **Captura de Vídeo**
```mermaid
sequenceDiagram
    participant CM as CameraManager
    participant VT as VideoTab
    participant AW as AnalysisWorker
    
    CM->>CM: Captura Frame
    CM->>VT: Atualiza Display
    CM->>AW: Envia Frame para Análise
    Note over AW: Frame entra na fila
```

2. **Análise e Detecção**
```mermaid
sequenceDiagram
    participant AW as AnalysisWorker
    participant D as Detector
    participant AM as AlertManager
    
    AW->>D: Processa Frame
    D->>D: Executa YOLOv8
    D->>AM: Envia Detecções
    Note over AM: Aplica Filtros
```

3. **Gerenciamento de Alertas**
```mermaid
sequenceDiagram
    participant AM as AlertManager
    participant AV as AlertView
    participant ES as EmailSender
    
    AM->>AM: Valida Alerta
    AM->>AV: Atualiza Interface
    AM->>ES: Envia para Worker
    Note over ES: Processamento Assíncrono
```

## Ciclo de Vida dos Dados

```mermaid
graph LR
    A[Frame Raw] --> B[Frame Processado]
    B --> C[Detecções]
    C --> D[Alertas]
    D --> E[Notificações]
    
    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style C fill:#bfb,stroke:#333
    style D fill:#fbb,stroke:#333
    style E fill:#fff,stroke:#333
```

## Sistema de Cache e Otimização

```mermaid
graph TD
    A[Frame] --> B{Cache?}
    B -- Sim --> C[Usa Cache]
    B -- Não --> D[Processa]
    D --> E[Salva Cache]
    C --> F[Resultado]
    E --> F
```

## Fluxo de Configuração

```mermaid
graph TD
    A[app_config.py] --> B[Validação]
    B --> C{Válido?}
    C -- Sim --> D[Aplica Config]
    C -- Não --> E[Erro]
    D --> F[Inicia Sistema]
```

## Comunicação Assíncrona

```mermaid
graph LR
    A[UI Thread] --> |Sinais| B[Worker Thread]
    B --> |Slots| A
    B --> |Processamento| C[GPU/CPU]
    C --> |Resultados| B
```

## Notas de Implementação

1. **Threads e Sinais**
   - UI Thread: Não bloqueante
   - Worker Thread: Processamento pesado
   - Comunicação via Qt Signals/Slots

2. **Otimizações**
   - Cache de frames
   - Buffer circular
   - Batch processing
   - GPU acceleration

3. **Pontos de Monitoramento**
   - Performance metrics
   - Error logging
   - Resource usage
   - Detection stats