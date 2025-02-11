# Plano de Refatoração do Sistema VisionGuard

## Objetivo
Remover a camada HTTP entre o frontend e o detector para melhorar a performance e reduzir o overhead de comunicação.

## Mudanças Necessárias

### 1. Reestruturação do Detector
- Mover a classe `ObjectDetector` para um módulo compartilhado
- Remover dependências HTTP do detector
- Adaptar o detector para trabalhar diretamente com arrays numpy
- Manter a funcionalidade assíncrona usando asyncio

### 2. Modificação do AnalysisWorker
- Remover toda a lógica de HTTP requests
- Instanciar o detector diretamente no worker
- Usar comunicação direta com o detector via métodos Python
- Manter a interface de eventos PyQt (signals) inalterada

### 3. Remoção da API
- Remover completamente a camada FastAPI
- Migrar configurações relevantes da API para o módulo de configuração principal
- Adaptar o sistema de logs para trabalhar sem a API
- Mover a lógica de alertas para um módulo independente

### 4. Ajustes no Frontend
- Remover código relacionado à API
- Atualizar configurações para não depender mais da API
- Adaptar o sistema de monitoramento de saúde
- Manter a mesma interface do usuário

### 5. Atualização do Sistema de Inicialização
- Remover código de inicialização da API do run.bat e run.py
- Simplificar o processo de inicialização
- Atualizar verificações de dependências

## Sequência de Implementação

1. **Fase 1: Preparação**
   - Criar branches de backup
   - Documentar APIs e interfaces atuais
   - Criar testes para garantir funcionalidade

2. **Fase 2: Refatoração do Core**
   - Refatorar ObjectDetector
   - Criar novo sistema de comunicação direta
   - Implementar novo sistema de logs

3. **Fase 3: Migração do Frontend**
   - Atualizar AnalysisWorker
   - Adaptar interface gráfica
   - Implementar novo sistema de alertas

4. **Fase 4: Limpeza**
   - Remover código legado
   - Atualizar documentação
   - Remover dependências não utilizadas

5. **Fase 5: Testes e Validação**
   - Testar performance
   - Validar funcionalidades
   - Verificar gestão de memória

## Impacto nas Dependências

### Dependências a Remover:
- fastapi
- uvicorn
- requests
- python-multipart

### Dependências a Manter:
- opencv-python
- numpy
- PyQt5
- ultralytics
- torch

## Considerações de Performance

1. **Benefícios Esperados:**
   - Redução de latência
   - Menor uso de memória
   - Processamento mais eficiente
   - Menos overhead de serialização

2. **Pontos de Atenção:**
   - Gerenciamento de memória
   - Sincronização entre threads
   - Tratamento de erros
   - Estado compartilhado

## Próximos Passos

1. Revisão do plano pela equipe
2. Criação de ambiente de testes
3. Implementação fase a fase
4. Validação contínua
5. Documentação das mudanças

## Riscos e Mitigações

### Riscos:
1. Perda de funcionalidade durante a migração
2. Problemas de performance inesperados
3. Conflitos de dependência
4. Bugs em produção

### Mitigações:
1. Testes extensivos
2. Implementação gradual
3. Monitoramento de performance
4. Plano de rollback