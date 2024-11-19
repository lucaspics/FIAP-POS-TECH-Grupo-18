import os
import cv2
from deepface import DeepFace
import mediapipe as mp
import matplotlib.pyplot as plt

# Define o caminho do vídeo que será analisado
VIDEO_PATH = "video-tc4.mp4"

# Define o caminho do vídeo de saída
OUTPUT_VIDEO_PATH = "output_video.mp4"

# Define o intervalo de frames a serem analisados para melhorar a performance
FRAMES_INTERVAL_TO_ANALYZE = 15

# Inicializa o detector de pose do MediaPipe para detecção de atividades corporais
mp_pose = mp.solutions.pose
pose_detector = mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5)


# Função para análise de emoções em cada rosto detectado
def analyze_emotions(frame):
    emotions = []
    faces_coords = []

    # Busca por faces e emoções

    # Inicia a busca utilizando o modelo "mtcnn", que é mais preciso na detecção de emoções e possue a melhor relação "tempo de processamento vs desempenho"
    results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False, detector_backend='mtcnn')

    # Caso nenhum rosto seja encontrado, efetua a busca novamente utilizando o modelo "retinaface", que é mais eficiente na busca de rostos em diferentes ângulos, porém é menos performático
    if len(results) == 1 and results[0]['face_confidence'] == 0:
        results = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False, detector_backend='retinaface')

    for result in results:

        face_confidence = result['face_confidence']
        face_props = result['region']
        emotions_scr = result['emotion']
        total_score = round(sum([emotions_scr[emotion] for emotion in emotions_scr]), 0)
        dominant_emotion = []
        if face_confidence >= 0.95:
            for emotion in emotions_scr:
                score = int(emotions_scr[emotion])
                score_p = int(score / total_score * 100)

                # Registra a emoção caso a mesma possua uma confiabilidade de no minimo 20%
                if score_p >= 20:
                    dominant_emotion.append([emotion, score_p])

        if len(dominant_emotion) > 0:

            # Caso haja mais de uma emoção detectada com fidelidade acima de 20%, a expressão é considerada como anômala
            if len(dominant_emotion) > 1:
                dominant_emotion = "anomaly"

            # Caso apenas uma emoção tenha sido detectada, valida se a fidelidade da mesma é de no minimo 60%
            elif len(dominant_emotion) == 1:
                dominant_emotion = dominant_emotion[0][0] if dominant_emotion[0][1] >= 90 else "neutral"

            # Adiciona as coordenadas da face encontrada à lista de faces
            face_coord = (face_props["x"], face_props["y"], face_props["w"], face_props["h"])
            faces_coords.append(face_coord)

            # Adiciona a emoção à lista de emoções
            emotions.append(dominant_emotion)

    return emotions, faces_coords


# Função para detecção de atividades corporais no frame atual
def detect_activities(frame):
    results = []

    # Converte a imagem para RGB, pois o MediaPipe espera esse formato
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Processa o frame para detectar poses corporais
    pose_results = pose_detector.process(frame_rgb)

    # Verifica se há landmarks corporais visíveis
    if pose_results.pose_landmarks:

        import math

        def calcular_distancia(ponto1, ponto2):
            return math.sqrt((ponto2.x - ponto1.x) ** 2 + (ponto2.y - ponto1.y) ** 2)

        landmarks = pose_results.pose_landmarks.landmark

        # Cabeça
        nariz = landmarks[mp_pose.PoseLandmark.NOSE.value]
        boca_esq = landmarks[mp_pose.PoseLandmark.MOUTH_LEFT.value]
        boca_dir = landmarks[mp_pose.PoseLandmark.MOUTH_RIGHT.value]
        orelha_esq = landmarks[mp_pose.PoseLandmark.LEFT_EAR.value]
        orelha_dir = landmarks[mp_pose.PoseLandmark.RIGHT_EAR.value]
        olho_esq = landmarks[mp_pose.PoseLandmark.LEFT_EYE.value]
        olho_dir = landmarks[mp_pose.PoseLandmark.RIGHT_EYE.value]
        olho_interno_esq = landmarks[mp_pose.PoseLandmark.LEFT_EYE_INNER.value]
        olho_externo_esq = landmarks[mp_pose.PoseLandmark.LEFT_EYE_OUTER.value]
        olho_interno_dir = landmarks[mp_pose.PoseLandmark.RIGHT_EYE_INNER.value]
        olho_externo_dir = landmarks[mp_pose.PoseLandmark.RIGHT_EYE_OUTER.value]

        # Membros superiores
        pulso_esq = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
        pulso_dir = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
        indicador_esq = landmarks[mp_pose.PoseLandmark.LEFT_INDEX.value]
        indicador_dir = landmarks[mp_pose.PoseLandmark.RIGHT_INDEX.value]
        cotovelo_esq = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
        cotovelo_dir = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
        dedinho_esq = landmarks[mp_pose.PoseLandmark.LEFT_PINKY.value]
        dedinho_dir = landmarks[mp_pose.PoseLandmark.RIGHT_PINKY.value]
        ombro_esq = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        ombro_dir = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        polegar_esq = landmarks[mp_pose.PoseLandmark.LEFT_THUMB.value]
        polegar_dir = landmarks[mp_pose.PoseLandmark.RIGHT_THUMB.value]

        # Quadril
        quadril_esq = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        quadril_dir = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]

        # Membros inferiores
        joelho_esq = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
        joelho_dir = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
        tornozelo_esq = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        tornozelo_dir = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        dedo_pe_indicador_esq = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value]
        dedo_pe_indicador_dir = landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value]
        calcanhar_esq = landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value]
        calcanhar_dir = landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value]

        # Levantando os braços: os pulsos estão acima da nariz
        if pulso_esq.y < olho_esq.y < ombro_esq.y or pulso_dir.y < olho_dir.y < ombro_dir.y:
            results.append("Arms raised")

        # Mão proxima ao rosto: pulsos proximos aos olhos
        if (
                (calcular_distancia(pulso_esq, nariz) < 0.2 and pulso_esq.visibility > 0.4)
                or (calcular_distancia(pulso_dir, nariz) < 0.2 and pulso_dir.visibility > 0.4)
                or (calcular_distancia(indicador_esq, nariz) < 0.2 and indicador_esq.visibility > 0.4)
                or (calcular_distancia(indicador_dir, nariz) < 0.2 and indicador_dir.visibility > 0.4)
        ):
            results.append("Hand to face")

        # Braço curvado: pulso na mesma altura do cotovelo, e abaixo do nariz
        if (
                (abs(pulso_esq.y - cotovelo_esq.y) < 10 and nariz.y < pulso_esq.y and pulso_esq.visibility > 0.4)
                or (abs(pulso_dir.y - cotovelo_dir.y) < 20 and nariz.y < pulso_dir.y and pulso_dir.visibility > 0.4)
        ):
            results.append("Bent arm")

        # Caso mais de um movimento divergente tenha sido detectado ao mesmo tempo, classifica como anômalo
        if len(results) > 2:
            results = ["Anomalous Movement"]

    return results


# Função principal que analisa o vídeo
def analyze_video(video_path):
    print("\n Loading video...")

    # Abre o vídeo para leitura
    video_capture = cv2.VideoCapture(video_path)
    total_frames = 0  # Contador de frames totais
    total_frames_analisados = 0  # Contador de frames analisados
    anomaly_count = 0  # Contador de anomalias de atividade
    all_activities = []  # Lista para armazenar as atividades detectadas
    all_emotions = []  # Lista para armazenar todas as emoções detectadas

    # Configura o gravador de vídeo
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    frame_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(video_capture.get(cv2.CAP_PROP_FPS))
    video_writer = cv2.VideoWriter(OUTPUT_VIDEO_PATH, fourcc, fps, (frame_width, frame_height))

    print(f"\n Analisando dados frames...")
    print("\n")

    frames_to_duplicate = 10  # Quantidade de vezes que cada frame será duplicado
    y_offset_initial = frame_height - 50  # Posição inicial para texto de atividades

    while True:
        # Lê um frame do vídeo
        ret, frame = video_capture.read()
        if not ret:  # Interrompe se não houver mais frames
            break

        total_frames += 1  # Incrementa o contador de frames

        # Realiza a análise apenas nos frames especificados para economizar recursos
        if total_frames % FRAMES_INTERVAL_TO_ANALYZE == 0:

            total_frames_analisados += 1

            # Detecta rostos e emoções no frame atual
            emotions, faces_coords = analyze_emotions(frame)

            # Detecta atividades corporais no frame atual
            activities_detected = detect_activities(frame)

            # Armazena as atividades e emoções detectadas
            all_activities.extend(activities_detected)
            all_emotions.extend(emotions)

            # Desenha um retângulo em cada rosto detectado no frame e exibe a emoção correspondente
            for (x, y, w, h), emotion in zip(faces_coords, emotions):
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                text = f"Emotion: {emotion}"
                cv2.putText(frame, text, (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Exibe as atividades detectadas no canto inferior
            y_offset = y_offset_initial
            for activity in activities_detected:
                text = f"Activity: {activity}"
                cv2.putText(frame, text, (30, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
                y_offset -= 20

            # Duplica o frame para prolongar sua duração no vídeo gerado
            for _ in range(frames_to_duplicate):
                video_writer.write(frame)

            # Redimensiona a janela antes de exibir o frame
            # window_width, window_height = 720, 405
            window_width, window_height = 1280, 720 #original size
            cv2.namedWindow('Current Frame', cv2.WINDOW_NORMAL)
            cv2.resizeWindow('Current Frame', window_width, window_height)
            cv2.imshow('Current Frame', frame)

            print(f" Frame: {total_frames}, Activity: {activities_detected}, Emotions: {emotions}")

            # Exibe imagem referente ao frame analisado
            cv2.imshow('Current Frame', frame)

            print(
                f" Frame: {total_frames}, Activity: {activities_detected}, Emotions: {emotions}, Faces Detected: {len(faces_coords)}")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Fecha o vídeo após o processamento
    video_capture.release()

    video_writer.release()

    # Cria um resumo da análise de atividades contando cada atividade detectada
    activity_summary = {activity: all_activities.count(activity) for activity in set(all_activities)}

    # Cria um resumo da análise de emoções contando cada emoção detectada
    emotion_summary = {emotion: all_emotions.count(emotion) for emotion in set(all_emotions)}

    # Compila um relatório final com os dados da análise
    report = {
        "Total de frames percorridos": total_frames,
        "Interválo de analise": f"{FRAMES_INTERVAL_TO_ANALYZE} frames",
        "Total de frames analisados": total_frames_analisados,
        "Número de anomalias detectadas": anomaly_count,
        "Resumo das atividades": dict(activity_summary),  # Converte para dicionário para exibição
        "Resumo das emoções": emotion_summary,
    }

    return report


# Executa a análise de vídeo e visualização dos resultados
if __name__ == "__main__":

    # Verifica se existe um arquivo no caminho informado
    if not os.path.exists(VIDEO_PATH):
        raise Exception(
            f"Nenhum arquivo foi encontrado no caminho informado. Verifique a informação e tente novamente. ({VIDEO_PATH})")

    # Verifica se existe um arquivo no caminho informado
    if str(VIDEO_PATH)[-3:] not in ("mp4"):
        raise Exception(f"O arquivo a ser analisado precisa ser um video (.mp4)")

    # Executa a análise no vídeo especificado
    report = analyze_video(VIDEO_PATH)

    # Exibe o relatório final
    print("\n Relatório de Análise:")
    print(f" Total de frames analisados: {report['Total de frames analisados']}")
    print(f" Número de anomalias detectadas: {report['Número de anomalias detectadas']}")
    print(" Resumo das atividades:", report['Resumo das atividades'])
    print(" Resumo das emoções:", report['Resumo das emoções'])

    # Gera os gráficos baseados nos resultados do relatório
    plt.figure(figsize=(14, 6))

    # Gráfico de barras para o resumo das emoções
    emotion_names = list(report["Resumo das emoções"].keys())
    emotion_counts = list(report["Resumo das emoções"].values())
    plt.subplot(1, 2, 1)
    plt.bar(emotion_names, emotion_counts, color='skyblue')
    plt.title("Resumo das Emoções Detectadas")
    plt.xlabel("Emoções")
    plt.ylabel("Frequência")

    # Gráfico de barras para o resumo das atividades e anomalias
    activity_names = list(report["Resumo das atividades"].keys())
    activity_counts = list(report["Resumo das atividades"].values())
    plt.subplot(1, 2, 2)
    plt.bar(activity_names, activity_counts, color='green')
    plt.title("Resumo das Atividades detectadas")
    plt.ylabel("Quantidade")

    plt.tight_layout()
    plt.show()
