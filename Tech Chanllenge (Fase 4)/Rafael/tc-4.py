import os
import cv2
import face_recognition
from deepface import DeepFace
import mediapipe as mp
import matplotlib.pyplot as plt
from collections import Counter

# Desativa algumas otimizações para compatibilidade com CPU, aumentando a precisão no uso do DeepFace
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# Define o caminho do vídeo que será analisado
VIDEO_PATH = "video-tc4.mp4"
# Define o intervalo de frames a serem analisados para melhorar a performance
FRAMES_TO_ANALYZE = 30

# Inicializa o detector de pose do MediaPipe para detecção de atividades corporais
mp_pose = mp.solutions.pose
pose_detector = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

# Função para detectar rostos no frame atual
def detect_faces(frame):
    # Converte a imagem para RGB, pois face_recognition espera imagens nesse formato
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Detecta a localização dos rostos na imagem
    face_locations = face_recognition.face_locations(rgb_frame)
    return face_locations

# Função para análise de emoções em cada rosto detectado com suavização para maior precisão
def analyze_emotions(frame, face_locations, emotion_history):
    emotions = []  # Lista para armazenar as emoções detectadas
    for (top, right, bottom, left) in face_locations:
        # Recorta a área do rosto para análise
        face = frame[top:bottom, left:right]
        # Análise de emoção usando o DeepFace
        result = DeepFace.analyze(face, actions=['emotion'], enforce_detection=False)
        dominant_emotion = result[0]['dominant_emotion']  # Emoção dominante detectada

        # Adiciona a emoção ao histórico
        emotion_history.append(dominant_emotion)

        # Mantém um histórico recente e obtém a emoção mais frequente para suavizar o resultado
        if len(emotion_history) > 5:  # Ajustável para mais ou menos suavização
            recent_emotions = emotion_history[-5:]
            dominant_emotion = Counter(recent_emotions).most_common(1)[0][0]

        emotions.append(dominant_emotion)  # Adiciona a emoção suavizada à lista de emoções
    return emotions

# Função para detecção de atividades corporais no frame atual
def detect_activities(frame):
    results = []
    # Converte a imagem para RGB, pois o MediaPipe espera esse formato
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Processa o frame para detectar poses corporais
    pose_results = pose_detector.process(frame_rgb)

    # Verifica se há landmarks corporais visíveis
    if pose_results.pose_landmarks:
        for lm in pose_results.pose_landmarks.landmark:
            # Verifica se algum ponto corporal visível tem movimento suficiente
            if lm.visibility > 0.5 and abs(lm.x - lm.y) > 0.05:
                results.append('Movimento detectado')
                break
    else:
        results.append('Nenhuma atividade detectada')
    return results

# Função principal que analisa o vídeo
def analyze_video(video_path):
    # Abre o vídeo para leitura
    video_capture = cv2.VideoCapture(video_path)
    total_frames = 0  # Contador de frames totais
    anomaly_count = 0  # Contador de anomalias de atividade
    activities = []  # Lista para armazenar as atividades detectadas
    all_emotions = []  # Lista para armazenar todas as emoções detectadas
    emotion_history = []  # Histórico de emoções para suavização

    while True:
        # Lê um frame do vídeo
        ret, frame = video_capture.read()
        if not ret:  # Interrompe se não houver mais frames
            break

        total_frames += 1  # Incrementa o contador de frames

        # Realiza a análise apenas nos frames especificados para economizar recursos
        if total_frames % FRAMES_TO_ANALYZE == 0:
            # Detecta rostos e emoções no frame atual
            face_locations = detect_faces(frame)
            emotions = analyze_emotions(frame, face_locations, emotion_history)
            # Detecta atividades corporais no frame atual
            activities_detected = detect_activities(frame)

            # Armazena as atividades e emoções detectadas
            activities.extend(activities_detected)
            all_emotions.extend(emotions)

            # Detecta anomalias na sequência de atividades
            if len(activities) > 1 and activities[-1] != activities[-2]:
                anomaly_count += 1

            print(f"Frame: {total_frames}, Atividades: {activities_detected}, Emoções: {emotions}")

    # Fecha o vídeo após o processamento
    video_capture.release()

    # Cria um resumo da análise de atividades contando cada atividade detectada
    activity_summary = Counter(activities)

    # Cria um resumo da análise de emoções contando cada emoção detectada
    emotion_summary = {emotion: all_emotions.count(emotion) for emotion in set(all_emotions)}

    # Compila um relatório final com os dados da análise
    report = {
        "Total de frames analisados": total_frames,
        "Número de anomalias detectadas": anomaly_count,
        "Resumo das atividades": dict(activity_summary),  # Converte para dicionário para exibição
        "Resumo das emoções": emotion_summary,
    }

    return report


# Função para gerar gráficos baseados no relatório final
def generate_report_visualization(report):
    # Configura os dados para o gráfico de emoções
    emotion_names = list(report["Resumo das emoções"].keys())
    emotion_counts = list(report["Resumo das emoções"].values())

    plt.figure(figsize=(10, 5))

    # Gráfico de barras para o resumo das emoções
    plt.subplot(1, 2, 1)
    plt.bar(emotion_names, emotion_counts, color='skyblue')
    plt.title("Resumo das Emoções Detectadas")
    plt.xlabel("Emoções")
    plt.ylabel("Frequência")

    # Gráfico de barras para o resumo das atividades e anomalias
    plt.subplot(1, 2, 2)
    plt.bar(["Atividades Detectadas", "Anomalias Detectadas"],
            [len(report["Resumo das atividades"]), report["Número de anomalias detectadas"]],
            color=['green', 'red'])
    plt.title("Resumo das Atividades e Anomalias")
    plt.ylabel("Quantidade")

    plt.tight_layout()
    plt.show()

# Executa a análise de vídeo e visualização dos resultados
if __name__ == "__main__":
    # Executa a análise no vídeo especificado
    report = analyze_video(VIDEO_PATH)

    # Exibe o relatório final
    print("Relatório de Análise:")
    print(f"Total de frames analisados: {report['Total de frames analisados']}")
    print(f"Número de anomalias detectadas: {report['Número de anomalias detectadas']}")
    print("Resumo das atividades:", report['Resumo das atividades'])
    print("Resumo das emoções:", report['Resumo das emoções'])

    # Gera os gráficos baseados nos resultados do relatório
    generate_report_visualization(report)
