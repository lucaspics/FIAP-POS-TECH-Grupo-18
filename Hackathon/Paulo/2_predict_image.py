import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import sys

# Definir o dispositivo (GPU se disponível)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Recriar o modelo com a mesma estrutura usada no treinamento
def load_model(model_path, num_classes):
    model = models.resnet18(pretrained=False)  # Criar modelo sem pesos pré-treinados
    model.fc = nn.Linear(model.fc.in_features, num_classes)  # Ajustar saída
    model.load_state_dict(torch.load(model_path, map_location=device))  # Carregar pesos
    model.to(device)
    model.eval()  # Definir modo de avaliação
    return model


def predict_image(image_path, model, class_names):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])

    # Carregar e transformar a imagem
    image = Image.open(image_path)
    image = transform(image).unsqueeze(0).to(device)  # Adicionar dimensão batch

    # Fazer a predição
    with torch.no_grad():
        output = model(image)
        _, predicted = torch.max(output, 1)  # Pegamos a classe com maior probabilidade
        class_name = class_names[predicted.item()]
    
    return class_name


if __name__ == "__main__":
    class_names = ["objetos_cortantes", "sem_objetos_cortantes"]
    
    # Verificar se a imagem foi passada como argumento
    if len(sys.argv) < 2:
        print("Uso: python predict.py <caminho_da_imagem>")
        sys.exit(1)

    image_path = sys.argv[1]

    # Carregar o modelo
    model = load_model("model/modelo_resnet18.pth", num_classes=len(class_names))

    # Fazer a predição
    resultado = predict_image(image_path, model, class_names)
    print("")
    print(f"> Resultado Predição: {resultado}")
    print("")
