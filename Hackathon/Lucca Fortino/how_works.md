# Sistema de Câmera de Segurança com Detecção de Objetos

## Visão Geral
Este é um sistema de monitoramento de câmera de segurança que utiliza inteligência artificial (YOLOv8) para detectar objetos em tempo real. O sistema é construído em Python, utilizando PyQt5 para a interface gráfica e OpenCV para processamento de vídeo.

## Divisão de Responsabilidades

### 1. Camada de Interface (UI Layer)
- **main_window.py**
  - Responsável apenas pela gestão da janela principal e coordenação entre componentes
  - Não contém lógica de negócio, apenas orquestração de eventos
  - Gerencia o ciclo de vida dos componentes visuais

- **video_tab.py**
  - Focado exclusivamente na exibição e controle de vídeo
  - Gerencia controles de reprodução
  - Mantém estado visual do player

- **settings_tab.py**
  - Isolado para configurações do sistema
  - Não interfere com lógica de processamento
  - Persiste preferências do usuário

### 2. Camada de Processamento (Processing Layer)
- **detector.py**
  - Encapsula toda lógica de detecção
  - Gerencia recursos de GPU/CPU
  - Implementa otimizações de performance
  - Não conhece detalhes da UI

- **analysis_worker.py**
  - Responsável pelo processamento assíncrono
  - Isola operações pesadas da thread principal
  - Gerencia fila de processamento
  - Comunica resultados via sinais

### 3. Camada de Dados (Data Layer)
- **alert_manager.py**
  - Gerencia persistência de alertas
  - Implementa lógica de filtragem
  - Mantém histórico de detecções

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

### Fluxo Assíncrono
1. Frame capturado na thread principal
2. Enviado para fila de processamento
3. Processado por workers disponíveis
4. Resultados retornados via sinais
5. UI atualizada sem bloqueio

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

### Prevenção de Falsos Positivos

1. **Filtros Temporais**
   - Análise de sequência de frames
   - Confirmação de detecções persistentes
   - Eliminação de detecções isoladas

2. **Filtros Espaciais**
   - Verificação de consistência de posição
   - Análise de tamanho dos objetos
   - Validação de proporções

3. **Filtros de Confiança**
   - Threshold adaptativo
   - Histórico de detecções
   - Média móvel de confiança

### Sistema de Logging
1. **Logs de Detecção**
   - Registro detalhado de cada detecção
   - Métricas de confiança
   - Timestamps precisos

2. **Logs de Sistema**
   - Performance do processamento
   - Uso de recursos
   - Erros e exceções

3. **Logs de Alertas**
   - Histórico de notificações
   - Ações do usuário
   - Resoluções de alertas

## Características Técnicas

### Performance
- Processamento paralelo de frames
- Otimização de memória GPU
- Cache de detecções
- Warmup do modelo

### Confiabilidade
- Recuperação automática de falhas
- Backup de dados críticos
- Validação de resultados
- Limpeza de recursos

### Escalabilidade
- Arquitetura modular
- Configuração flexível
- Suporte a múltiplos dispositivos
- Extensibilidade via plugins

## Requisitos do Sistema
- Python 3.x
- PyQt5
- OpenCV
- YOLOv8
- CUDA (opcional, para aceleração GPU)