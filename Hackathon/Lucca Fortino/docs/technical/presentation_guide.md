# Guia de Apresentação do Sistema VisionGuard

## 1. Inicialização do Sistema
O sistema inicia através do arquivo `src/main.py`, que configura a aplicação Qt e inicializa a janela principal.

**Arquivos e linhas relevantes:**
- `src/main.py` (linhas 7-22): Função principal que inicializa a aplicação
- `src/ui/main_window.py` (linhas 42-69): Inicialização dos gerenciadores principais
  - Inicialização do CameraManager
  - Inicialização do AnalysisManager com modelo de detecção
  - Configuração da interface gráfica

## 2. Captura e Processamento de Frames
O sistema suporta tanto câmeras ao vivo quanto arquivos de vídeo.

**Arquivos e linhas relevantes:**
- `src/ui/main_window.py`:
  - Linhas 165-229: Conexão com fontes de vídeo
  - Linhas 257-294: Processamento de frames
  - Configuração de timers para atualização contínua

**Fluxo de processamento:**
1. Captura do frame da fonte de vídeo
2. Redimensionamento para altura alvo
3. Atualização da interface
4. Envio para análise

## 3. Sistema de Detecção
O detector utiliza YOLOv8 otimizado para processamento local.

**Arquivos e linhas relevantes:**
- `src/core/detector.py`:
  - Linhas 68-84: Inicialização do detector
  - Linhas 124-185: Método de detecção assíncrono
  - Linhas 187-242: Visualização das detecções

**Características principais:**
- Carregamento otimizado do modelo
- Processamento assíncrono
- Gerenciamento automático de memória CUDA
- Sistema de warmup para melhor performance inicial

## 4. Gerenciamento de Alertas
Sistema robusto para gerenciamento e persistência de alertas.

**Arquivos e linhas relevantes:**
- `src/core/alert_manager.py`:
  - Linhas 124-258: Processamento de detecções e geração de alertas
  - Linhas 289-357: Gerenciamento de alertas recentes
  - Linhas 91-123: Sistema de rotação de alertas

**Funcionalidades:**
- Armazenamento de alertas com imagens
- Sistema de rotação automática
- Gerenciamento de diretórios
- Arquivamento automático

## 5. Notificações por Email
Sistema assíncrono de notificações por email com worker dedicado.

**Arquivos e linhas relevantes:**
- `src/core/email_sender.py`:
  - Linhas 21-87: Worker dedicado para envio em background
  - Linhas 142-186: Envio assíncrono de alertas
  - Linhas 235-324: Geração do corpo do email em HTML

**Características:**
- Worker em thread separada
- Fila assíncrona de emails
- Templates HTML responsivos
- Suporte a múltiplas imagens
- Sistema de retry automático

## Pontos de Demonstração

1. **Inicialização:**
   - Mostrar carregamento do modelo
   - Verificar inicialização dos gerenciadores

2. **Captura:**
   - Demonstrar conexão com câmera
   - Mostrar carregamento de vídeo
   - Exibir controles de playback

3. **Detecção:**
   - Mostrar detecções em tempo real
   - Exibir métricas de performance
   - Demonstrar ajuste de confiança

4. **Alertas:**
   - Mostrar geração de alertas
   - Exibir sistema de arquivamento
   - Demonstrar visualização de histórico

5. **Notificações:**
   - Configurar email de teste
   - Mostrar email recebido
   - Exibir template responsivo

## Métricas e Logs

Para acompanhamento durante a apresentação:
- FPS atual
- Número de detecções
- Workers ativos
- Uso de memória
- Tempo de processamento
- Taxa de alertas

## Recuperação de Erros

Demonstrar recuperação em cenários como:
- Perda de conexão com câmera
- Erro de processamento
- Falha de rede para emails
- Problemas de permissão de arquivos