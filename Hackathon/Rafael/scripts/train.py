from ultralytics import YOLO

def train_model():
    # Carregar o modelo YOLOv8
    model = YOLO("C:/Users/rafae/PycharmProjects/fiaphackaton/pythonProject2/models/yolov8n.pt")  # Modelo pré-treinad


    # Treinar o modelo com o dataset
    model.train(
        data="C:/Users/rafae/PycharmProjects/fiaphackaton/pythonProject2/datasets/cortante/data.yaml",  # Caminho do arquivo data.yaml
        epochs=50,  # Número de épocas de treinamento
        batch=16,  # Tamanho do lote
        imgsz=640,  # Tamanho das imagens
        project="models",  # Pasta para salvar os modelos
        name="cortante",  # Nome do projeto de treinamento
        #resume = True,  # Importante: resume o treinamento anterior
        pretrained = True  # Indica que estamos usando um modelo pré-treinado
    )

if __name__ == "__main__":
    train_model()