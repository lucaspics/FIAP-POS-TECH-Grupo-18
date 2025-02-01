import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt

# Transformações para normalização e aumento de dados (data augmentation)
transform = transforms.Compose([
    transforms.Resize((224, 224)),  # Redimensiona para 224x224
    transforms.RandomHorizontalFlip(),  # Espelhamento aleatório
    transforms.ToTensor(),  # Converte para tensor
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])  # Normalização
])

# Carregar os datasets
train_dataset = datasets.ImageFolder('dataset/train', transform=transform)
val_dataset = datasets.ImageFolder('dataset/val', transform=transform)

# Criar os DataLoaders
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)


# Verificar as classes
print(f"Classes treinamento encontradas: {train_dataset.classes}")


# Carregar modelo pré-treinado
model = models.resnet18(pretrained=True)

# Ajustar a última camada para o número de classes do dataset
num_classes = len(train_dataset.classes)
model.fc = nn.Linear(model.fc.in_features, num_classes)

# Mover para GPU se disponível
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

print(model)  # Para verificar a arquitetura ajustada

criterion = nn.CrossEntropyLoss()  # Para classificação multi-classe
optimizer = optim.Adam(model.parameters(), lr=0.001)  # Otimizador Adam

# Número de épocas
epochs = 10  

# Loop de treinamento
for epoch in range(epochs):
    model.train()  # Modo de treino
    running_loss = 0.0

    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()  # Zerar os gradientes
        outputs = model(images)  # Forward
        loss = criterion(outputs, labels)  # Calcula perda
        loss.backward()  # Backpropagation
        optimizer.step()  # Atualiza pesos

        running_loss += loss.item()
    
    print(f"Época {epoch+1}/{epochs}, Loss: {running_loss/len(train_loader):.4f}")

# Salvar o modelo treinado
torch.save(model.state_dict(), "modelo_resnet18.pth")
print("Modelo salvo!")
print("=====================================================================\n")

# Avaliação do modelo
model.eval()  # Modo de avaliação
correct = 0
total = 0

with torch.no_grad():
    for images, labels in val_loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        _, predicted = torch.max(outputs, 1)  # Pega a classe com maior probabilidade
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

print(f"Acurácia no conjunto de validação: {100 * correct / total:.2f}%")
print("=====================================================================\n")