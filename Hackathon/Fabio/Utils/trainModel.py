from ultralytics import YOLO

# Carregar o modelo YOLOv8 pré-treinado
model = YOLO('yolov8n.pt')  # Escolha entre yolov8n.pt, yolov8s.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt

# Treinar o modelo com o dataset personalizado
model.train(data='datasets/datasets/data.yaml', epochs=50, imgsz=640)

# Avaliar o modelo
metrics = model.val()
print(metrics)