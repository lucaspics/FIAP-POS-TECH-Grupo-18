# Referências para Apresentação

Este documento mapeia os trechos de código e conceitos mencionados na apresentação com seus respectivos arquivos e números de linha.

## Estrutura do Projeto
- Estrutura de diretórios: `src/`
  - Training: `src/training/`
  - Core: `src/core/`
  - UI: `src/ui/`
  - Config: `src/config/`
  - Workers: `src/workers/`

## Inicialização do Sistema
- Ponto de entrada: `src/main.py` (linhas 7-22)
  ```python
  def main():
      try:
          app = QApplication(sys.argv)
          window = SecurityCameraApp()
          window.show()
  ```

## Processamento de Frames
1. **Validação de Frame**
   - Arquivo: `src/core/video_utils.py` (linhas 14-42)
   - Função: `validate_frame()`

2. **Redimensionamento**
   - Arquivo: `src/core/video_utils.py` (linhas 44-81)
   - Função: `resize_frame()`

## Sistema de Detecção
1. **Inicialização do Detector**
   - Arquivo: `src/core/detector.py` (linhas 71-84)
   - Classe: `ObjectDetector`
   - Método: `__init__()`

2. **Carregamento do Modelo**
   - Arquivo: `src/core/detector.py` (linhas 86-108)
   - Método: `_load_model()`

3. **Warmup do Modelo**
   - Arquivo: `src/core/detector.py` (linhas 110-123)
   - Método: `_warmup_model()`

4. **Detecção Assíncrona**
   - Arquivo: `src/core/detector.py` (linhas 124-185)
   - Método: `detect()`

5. **Visualização de Detecções**
   - Arquivo: `src/core/detector.py` (linhas 187-242)
   - Método: `draw_detections()`

## Sistema de Alertas
1. **Geração de Alertas**
   - Arquivo: `src/core/alert_manager.py` (linhas 124-167)
   - Método: `process_detection()`

2. **Estrutura de Dados do Alerta**
   - Arquivo: `src/core/alert_manager.py` (linhas 156-166)
   - Definição da estrutura `alert_data`

3. **Persistência de Alertas**
   - Arquivo: `src/core/alert_manager.py` (linhas 168-208)
   - Salvamento de JSON e imagens

4. **Rotação de Alertas**
   - Arquivo: `src/core/alert_manager.py` (linhas 91-123)
   - Método: `_rotate_alerts()`

## Interface do Usuário
1. **Visualização de Alertas**
   - Arquivo: `src/ui/alert_view.py` (linhas 81-127)
   - Método: `add_alert()`

2. **Diálogo de Alertas**
   - Arquivo: `src/ui/alert_dialog.py`
   - Classe: `AlertDialog`

## Sistema de Notificações
1. **Worker de Email**
   - Arquivo: `src/core/email_sender.py` (linhas 21-87)
   - Classe: `EmailWorker`

2. **Envio de Alertas**
   - Arquivo: `src/core/email_sender.py` (linhas 142-186)
   - Método: `send_alert()`

## Métricas e Monitoramento
1. **Atualização de Métricas**
   - Arquivo: `src/ui/main_window.py` (linhas 316-326)
   - Método: `update_metrics()`

2. **Estatísticas do Detector**
   - Arquivo: `src/core/detector.py` (linhas 252-261)
   - Método: `get_model_info()`

## Recuperação de Falhas
1. **Desconexão de Câmera**
   - Arquivo: `src/ui/main_window.py` (linhas 230-243)
   - Método: `disconnect_camera()`

2. **Limpeza de Recursos**
   - Arquivo: `src/ui/main_window.py` (linhas 363-372)
   - Método: `closeEvent()`