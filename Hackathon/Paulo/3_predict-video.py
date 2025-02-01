import torch
import torch.nn as nn
from torchvision import models, transforms
import cv2
import time
from PIL import Image
import os
import time
from email_alert import enviar_alerta  # Importa a função de envio de e-mails

# Criar pasta para armazenar os frames detectados
if not os.path.exists("frames_detectados"):
    os.makedirs("frames_detectados")

# Variável para armazenar o tempo do último e-mail enviado
ultimo_alerta = 0  # Inicializa como 0

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

# Transformação das imagens para entrada no modelo
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
])

# Função para processar um frame e fazer a predição
def predict_frame(frame, model, class_names):
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # Converter OpenCV (BGR) para PIL (RGB)
    image = transform(image).unsqueeze(0).to(device)  # Aplicar transformações e adicionar dimensão batch

    with torch.no_grad():
        output = model(image)
        _, predicted = torch.max(output, 1)  # Classe com maior probabilidade
        class_name = class_names[predicted.item()]

    return class_name

# Processamento do vídeo
def process_video(video_path, model, class_names):
    global ultimo_alerta
    cap = cv2.VideoCapture(video_path)  # Abrir o vídeo

    if not cap.isOpened():
        print("Erro ao abrir o vídeo.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)  # Obter FPS do vídeo
    frame_count = 0  # Contador de frames

    print("Analisando vídeo...")

    while True:
        ret, frame = cap.read()  # Capturar frame
        if not ret:
            break  # Se não houver mais frames, sair do loop

        frame_count += 1
        timestamp = frame_count / fps  # Calcular tempo no vídeo (segundos)

        # Fazer predição para o frame atual
        class_name = predict_frame(frame, model, class_names)

        # Se um objeto cortante for detectado, imprimir o tempo do vídeo
        if class_name == "objetos_cortantes":
            tempo_atual = time.time()

            # Verifica se passaram pelo menos 30 segundos desde o último alerta
            if tempo_atual - ultimo_alerta >= 30:
                print(f"\nTempo Atual do Vídeo: {tempo_atual}, Último Alerta: {ultimo_alerta}, Diferença: {tempo_atual - ultimo_alerta}")
                print(f"\n⚠️ Objeto cortante detectado em {timestamp:.2f} segundos")

                # Salvar o frame detectado
                frame_path = f"frames_detectados/frame_{int(timestamp)}s.jpg"
                cv2.imwrite(frame_path, frame)
                print(f"📷 Frame salvo em {frame_path}")

                # Enviar alerta com frame anexado
                enviar_alerta(timestamp, frame_path)

                # Atualizar o tempo do último alerta enviado
                ultimo_alerta = tempo_atual            


        # Opcional: Exibir o vídeo com uma caixa de texto
        cv2.putText(frame, f"Classe: {class_name}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Video", frame)

        # Pressionar 'q' para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Processamento do vídeo concluído.")

# Execução principal
if __name__ == "__main__":
    video_path = "videos/video_teste_01.mp4"
    class_names = ["objetos_cortantes", "sem_objetos_cortantes"]

    # Carregar modelo treinado
    model = load_model("model/modelo_resnet18.pth", num_classes=len(class_names))
    
    process_video(video_path, model, class_names)
