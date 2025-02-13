# Narrativa de Apresentação do VisionGuard

Boa noite a todos! Hoje vou apresentar o VisionGuard, nosso sistema de vigilância inteligente que desenvolvemos para detectar e alertar sobre situações de risco em tempo real. Antes de mergulharmos nos detalhes técnicos, gostaria de dar uma visão geral de como organizamos este projeto.

[Mostrar estrutura de diretórios em `src/`]

O VisionGuard foi construído de forma modular, com cada componente tendo uma responsabilidade bem definida. No coração do sistema, temos nossa pasta `src/training`, onde mantemos todo o código relacionado ao treinamento do modelo YOLOv8, incluindo o gerenciamento de datasets e métricas de performance. Este é o fundamento do nosso sistema de detecção.

Em `src/core`, implementamos os componentes principais da aplicação: nosso detector de objetos otimizado, o gerenciador de alertas e o sistema de notificações. Estes componentes trabalham em conjunto com os utilitários de processamento de vídeo para fornecer uma solução robusta e eficiente.

A interface do usuário, localizada em `src/ui`, foi desenvolvida pensando na experiência do operador. Implementamos uma janela principal intuitiva, com visualização de câmeras em tempo real e um painel de alertas que mantém o operador sempre informado sobre eventos importantes.

É importante ressaltar que todo o poder do VisionGuard vem de seu modelo YOLOv8 altamente treinado. Embora ainda estejamos em processo de treinamento do modelo específico para nossa aplicação, o sistema foi projetado para evoluir continuamente. A pasta `src/training` contém toda a infraestrutura necessária para:
- Gerenciar datasets de treinamento
- Executar ciclos de treinamento
- Validar a performance do modelo
- Medir métricas de precisão

Esta capacidade de evolução é crucial porque nos permite:
1. Adaptar o modelo para novos cenários
2. Melhorar a precisão das detecções
3. Reduzir falsos positivos
4. Adicionar novas classes de objetos para detecção

O processo de treinamento é uma parte vital do sistema que será implementada em breve, permitindo que o VisionGuard se torne cada vez mais preciso e eficiente em suas detecções.

[Mostrar: src/main.py, linhas 7-22]
Quando iniciamos o sistema, o primeiro código executado está em `src/main.py`. Aqui, inicializamos nossa aplicação Qt e criamos a janela principal. Veja como é simples e direto:

```python
def main():
    try:
        # Inicializar aplicação Qt
        app = QApplication(sys.argv)
        
        # Criar e exibir janela principal
        window = SecurityCameraApp()
        window.show()
```

A partir deste ponto, começa uma jornada fascinante de processamento de dados. Quando um frame é capturado, seja de uma câmera ao vivo ou de um arquivo de vídeo, ele passa por um pipeline sofisticado de processamento.

[Mostrar: src/core/video_utils.py, linhas 14-42]
Primeiro, realizamos uma validação rigorosa do frame:

```python
def validate_frame(frame: np.ndarray) -> bool:
    if frame is None:
        return False
    
    if not isinstance(frame, np.ndarray):
        return False
```

Esta validação é crucial porque garante que estamos trabalhando com dados consistentes. O frame precisa ser uma matriz numpy tridimensional, com as dimensões corretas e os três canais de cor necessários.

[Mostrar: src/core/video_utils.py, linhas 44-81]
Após a validação, realizamos um pré-processamento cuidadoso. O redimensionamento do frame é particularmente importante, pois mantém a proporção original da imagem enquanto otimiza o uso de recursos:

```python
if keep_aspect_ratio:
    # Manter proporção
    target_width = int(width * (target_height / height))
```

[Mostrar: src/core/detector.py, linhas 71-84]
O frame preparado é então enviado para nosso detector YOLOv8, que é o coração do sistema. A inicialização do detector é um processo cuidadoso que garante performance máxima:

```python
def _load_model(self):
    """Carrega o modelo com configurações otimizadas."""
    try:
        with safe_globals(SAFE_CLASSES):
            # Forçar carregamento sem weights_only
            original_load = torch.load
            torch.load = lambda f, *args, **kwargs: original_load(f, weights_only=False, *args, **kwargs)
            
            try:
                self.model = YOLO(self.model_path)
                self.classes = self.model.names
```

[Mostrar: src/core/detector.py, linhas 110-123]
O modelo passa por um processo de "warmup" que é crucial para performance consistente:

```python
def _warmup_model(self):
    """Realiza warmup do modelo com uma imagem em branco."""
    try:
        dummy_image = np.zeros((self.target_height, self.target_height, 3), dtype=np.uint8)
        with torch.no_grad():
            for _ in range(3):
                self.model(dummy_image)
```

Este warmup garante que o modelo esteja otimizado desde o primeiro frame real, pois as primeiras inferências em modelos PyTorch tendem a ser mais lentas devido à compilação JIT e alocação de memória.

[Mostrar: src/core/detector.py, linhas 124-149]
O processo de detecção em si é fascinante. Quando um frame chega ao detector, ele passa por várias etapas:

```python
async def detect(self, image: np.ndarray, conf_threshold: Optional[float] = None) -> DetectionResult:
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

1. **Preparação para Inferência**:
   - Definição do threshold de confiança
   - Limpeza proativa da memória GPU
   - Configuração do tamanho da imagem

2. **Inferência Assíncrona**:
   - A inferência roda em uma thread separada via `asyncio.to_thread`
   - Usamos `torch.no_grad()` para otimizar memória
   - O modelo YOLOv8 processa o frame completo em uma única passagem

[Mostrar: src/core/detector.py, linhas 150-185]
3. **Processamento dos Resultados**:
```python
# Processar resultados
boxes_np = results.boxes.data.cpu().numpy()
del results  # Liberar memória

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

Cada detecção contém:
- Coordenadas do bounding box (x1, y1, x2, y2)
- Nível de confiança da detecção
- Classe do objeto detectado
- Timestamp preciso

O YOLOv8 é especialmente eficiente porque:
1. Processa a imagem inteira em uma única passada
2. Detecta múltiplos objetos simultaneamente
3. Aprende características em diferentes escalas
4. Balanceia precisão e velocidade

[Mostrar: src/core/detector.py, linhas 187-242]
Para visualização, cada detecção é desenhada no frame:

```python
def draw_detections(self, image: np.ndarray, detections: List[Detection]) -> np.ndarray:
    img_draw = image.copy()
    
    for det in detections:
        try:
            x1, y1, x2, y2 = map(int, det.bbox)
            label = f"{det.class_name} {det.confidence:.2f}"
            
            # Desenhar bbox com espessura maior
            cv2.rectangle(img_draw, (x1, y1), (x2, y2), (0, 255, 255), 3)
```

[Mostrar: src/core/detector.py, linhas 252-261]
O sistema mantém estatísticas detalhadas sobre o detector:
```python
def get_model_info(self) -> Dict:
    return {
        "path": str(self.model_path),
        "classes": self.classes,
        "type": self.model.task,
        "total_detections": self.total_detections,
        "confidence_threshold": self.confidence_threshold,
        "target_height": self.target_height
    }
```

[Mostrar: src/core/alert_manager.py, linhas 124-167]
Um dos aspectos mais interessantes do sistema é como lidamos com os alertas. Quando o detector identifica algo relevante, um processo sofisticado de geração e gerenciamento de alertas é iniciado. Vamos examinar como isso funciona em detalhes.

Primeiro, o sistema gera um identificador único para o alerta baseado no timestamp atual:

```python
alert_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
```

[Mostrar: src/core/alert_manager.py, linhas 156-166]
Em seguida, criamos uma estrutura de dados rica que contém todas as informações relevantes sobre a detecção:

```python
alert_data = {
    "alert_id": alert_id,
    "timestamp": result.timestamp.isoformat(),
    "video_time": video_time,
    "detections": [det.to_dict() for det in high_confidence_detections],
    "confidence_threshold": self.min_confidence,
    "alert_triggered": 1,
    "analysis_time": 0.0,
    "frame_number": 0
}
```

Esta estrutura é crucial porque ela não apenas registra o que foi detectado, mas também mantém o contexto completo do alerta - quando aconteceu, qual era o nível de confiança, em que momento do vídeo ocorreu, e assim por diante.

[Mostrar: src/core/alert_manager.py, linhas 168-208]
O sistema então persiste esses dados de forma organizada. Utilizamos uma estrutura de diretórios bem definida:
- `/data`: Armazena os arquivos JSON com os metadados dos alertas
- `/images`: Mantém as imagens capturadas no momento da detecção
- `/archive`: Guarda alertas antigos quando atingimos o limite de armazenamento

Quando salvamos um alerta, garantimos a integridade dos dados através de várias verificações:

```python
json_path = self.alert_dir / 'data' / f"{alert_id}.json"
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(alert_data, f, indent=2, ensure_ascii=False)

# Verificar se os dados foram salvos corretamente
if json_path.exists():
    with open(json_path, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
```

Se o alerta incluir uma imagem, processamos ela de forma especial:

```python
if frame is not None and ALERT_CONFIG['save_frames']:
    frame_with_detections = self.detector.draw_detections(frame, high_confidence_detections)
    image_path = images_dir / f"{alert_id}.jpg"
    success = cv2.imwrite(str(image_path), frame_with_detections)
```

A imagem salva inclui as marcações visuais das detecções, o que é extremamente útil para análise posterior.

[Mostrar: src/core/alert_manager.py, linhas 91-123]
O sistema também implementa um mecanismo inteligente de rotação de alertas. Quando atingimos o limite máximo configurado:

```python
if self.total_alerts > self.max_alerts:
    await asyncio.to_thread(self._rotate_alerts)
```

Os alertas mais antigos são movidos automaticamente para o diretório de arquivo, mantendo tanto os metadados quanto as imagens organizados.

[Mostrar: src/ui/alert_view.py, linhas 81-127]
Na interface do usuário, estes alertas ganham vida através do componente AlertView. Cada alerta é apresentado em um widget interativo que mostra as informações mais relevantes:

```python
def add_alert(self, alert_data: Dict[str, Any]):
    # Criar item e widget
    item, widget = create_alert_list_item(alert_data)
    
    if isinstance(widget, AlertWidget):
        # Conectar sinal do widget para abrir dialog
        widget.alert_clicked.connect(self._show_alert_dialog)
```

Quando um operador clica em um alerta, um diálogo detalhado é apresentado, mostrando:
- A imagem capturada com as detecções marcadas
- Todos os metadados relevantes
- Opções para interagir com o alerta

Este sistema de alertas não é apenas um registro passivo - ele é uma ferramenta interativa que permite aos operadores:
- Revisar detecções passadas
- Analisar padrões de eventos
- Validar a precisão do sistema
- Exportar dados para análise posterior

E tudo isso é feito de forma assíncrona, garantindo que o sistema principal continue respondendo mesmo durante operações intensivas de I/O como salvamento de imagens ou rotação de alertas.

[Mostrar: src/ui/main_window.py, linhas 316-326]
Durante todo esse processo, mantemos métricas detalhadas de performance. Monitoramos a taxa de frames por segundo, o número de detecções, workers ativos e uso de memória. Estas métricas são constantemente atualizadas na interface:

```python
self.status_bar.showMessage(
    f"FPS: {fps:.1f} | Detecções: {detections} | "
    f"Workers: {len(self.analysis_manager.active_workers)}"
)
```

[Mostrar: src/ui/main_window.py, linhas 230-243]
O sistema também é extremamente resiliente. Implementamos recuperação automática para diversos cenários, como perda de conexão com a câmera ou falhas de rede. Por exemplo, quando precisamos desconectar uma fonte de vídeo:

```python
def disconnect_camera(self):
    try:
        self.frame_timer.stop()
        self.camera_manager.release()
        self.video_tab.enable_controls(False)
```

Todo este conjunto de funcionalidades trabalha em harmonia para criar um sistema de vigilância verdadeiramente inteligente. O VisionGuard não é apenas um detector de objetos - é uma solução completa que combina processamento em tempo real, gerenciamento eficiente de recursos e um sistema robusto de notificações, tudo isso com uma interface intuitiva que facilita o trabalho do operador.
