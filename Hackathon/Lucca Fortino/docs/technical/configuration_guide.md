# Guia de Configuração e Troubleshooting do VisionGuard

## 1. Configuração Inicial

### 1.1 Variáveis de Ambiente (.env)
```env
# Configurações de Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app

# Configurações do Sistema
DEBUG_MODE=False
LOG_LEVEL=INFO
```

### 1.2 Configuração do Modelo
```python
MODEL_CONFIG = {
    'path': 'models/best.pt',
    'confidence_threshold': 0.25,  # Ajuste conforme necessidade
    'alert_threshold': 0.5,       # Threshold para alertas
    'target_height': 320          # Altura para processamento
}
```

### 1.3 Configuração de Vídeo
```python
VIDEO_CONFIG = {
    'frame_interval': 30,         # Ajuste para performance
    'analysis_interval': 5,       # Balance precisão/performance
    'max_concurrent_workers': 2,  # Baseado no hardware
    'frame_timeout': 5.0         # Tolerância para atrasos
}
```

## 2. Resolução de Problemas

### 2.1 Problemas Comuns e Soluções

#### Performance Baixa
1. **Sintomas**
   - FPS baixo
   - Alta latência
   - UI travando

2. **Soluções**
   - Reduzir resolution (VIDEO_CONFIG['width'/'height'])
   - Aumentar analysis_interval
   - Verificar uso de GPU
   - Limpar cache de frames

#### Falsos Positivos
1. **Sintomas**
   - Alertas incorretos frequentes
   - Detecções instáveis

2. **Soluções**
   - Aumentar confidence_threshold
   - Ajustar alert_threshold
   - Verificar iluminação
   - Atualizar modelo

#### Problemas de Memória
1. **Sintomas**
   - OutOfMemory errors
   - Crashes aleatórios
   - Performance degradando

2. **Soluções**
   - Reduzir max_concurrent_workers
   - Limpar buffers periodicamente
   - Verificar memory leaks
   - Ajustar batch size

### 2.2 Logs e Diagnóstico

#### Estrutura de Logs
```
logs/
├── alerts/     # Alertas e detecções
├── errors/     # Erros do sistema
├── metrics/    # Métricas de performance
└── results/    # Resultados de análise
```

#### Níveis de Log
```python
# logging_config.py
LOG_LEVELS = {
    'DEBUG': 10,    # Desenvolvimento
    'INFO': 20,     # Produção normal
    'WARNING': 30,  # Avisos
    'ERROR': 40,    # Erros recuperáveis
    'CRITICAL': 50  # Erros críticos
}
```

## 3. Manutenção

### 3.1 Backup e Recuperação

#### Backup Automático
```bash
# Executar periodicamente
python tools/backup_project.py

# Estrutura de backup
backups/
├── models/
├── configs/
└── logs/
```

#### Recuperação
1. Restaurar modelo
2. Verificar configurações
3. Validar ambiente
4. Testar sistema

### 3.2 Atualização do Sistema

#### Procedimento de Update
1. Backup dos dados
2. Atualizar código
3. Validar configurações
4. Testar funcionalidades
5. Monitorar logs

## 4. Monitoramento

### 4.1 Métricas Importantes

#### Performance
- FPS médio
- Tempo de processamento
- Uso de memória
- Latência de detecção

#### Qualidade
- Taxa de detecção
- Falsos positivos
- Precisão do modelo
- Tempo de resposta

### 4.2 Alertas do Sistema

#### Níveis de Alerta
1. **Info**
   - Operações normais
   - Métricas de rotina

2. **Warning**
   - Performance degradada
   - Recursos limitados

3. **Error**
   - Falhas de processamento
   - Problemas de conexão

4. **Critical**
   - Crashes do sistema
   - Falhas de hardware

## 5. Otimização

### 5.1 Ajuste Fino

#### Performance
```python
# Configurações para alta performance
VIDEO_CONFIG = {
    'frame_interval': 20,        # Mais frames
    'analysis_interval': 3,      # Mais análises
    'max_concurrent_workers': 3  # Mais processamento
}

# Configurações para economia de recursos
VIDEO_CONFIG = {
    'frame_interval': 40,        # Menos frames
    'analysis_interval': 8,      # Menos análises
    'max_concurrent_workers': 1  # Menos processamento
}
```

#### Precisão
```python
# Configurações para alta precisão
MODEL_CONFIG = {
    'confidence_threshold': 0.35,
    'alert_threshold': 0.6,
    'target_height': 480
}

# Configurações para menos falsos positivos
MODEL_CONFIG = {
    'confidence_threshold': 0.45,
    'alert_threshold': 0.7,
    'target_height': 320
}
```

## 6. Desenvolvimento

### 6.1 Ambiente de Desenvolvimento

#### Setup
1. Criar ambiente virtual
2. Instalar dependências
3. Configurar variáveis
4. Iniciar em modo debug

#### Debug
```python
# Ativar modo debug
DEBUG_MODE = True
LOG_LEVEL = 'DEBUG'

# Monitorar métricas
metrics = {
    'fps': [],
    'memory_usage': [],
    'detection_times': []
}
```

### 6.2 Testes

#### Testes Automatizados
1. Testes unitários
2. Testes de integração
3. Testes de performance
4. Testes de stress

#### Validação
1. Verificar precisão
2. Medir performance
3. Testar limites
4. Validar alertas