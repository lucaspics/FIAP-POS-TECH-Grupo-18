import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Desativa otimizações para compatibilidade com CPU
import cv2
import face_recognition
from deepface import DeepFace
from moviepy.editor import VideoFileClip
import speech_recognition as sr
from transformers import pipeline
import numpy as np
import mediapipe as mp
import threading

# Configurações iniciais
VIDEO_PATH = "video-tc4.mp4"  # Caminho para o arquivo de vídeo
FRAMES_TO_ANALYZE = 30  # Intervalo de frames a serem analisados, processa um a cada 30 frames

# Inicializa o MediaPipe para detecção de pose corporal
mp_pose = mp.solutions.pose
pose_detector = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5)

# Função para detecção de rostos
def detect_faces(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Converte o frame para RGB
    face_locations = face_recognition.face_locations(rgb_frame)  # Detecta rostos
    return face_locations

# Função para análise de emoções em cada rosto detectado
def analyze_emotions(frame, face_locations):
    emotions = []
    for (top, right, bottom, left) in face_locations:
        face = frame[top:bottom, left:right]
        result = DeepFace.analyze(face, actions=['emotion'], enforce_detection=False)
        emotions.append(result[0]['dominant_emotion'])
    return emotions

# Função para detecção de atividades corporais (como gestos ou poses)
def detect_activities(frame):
    results = []
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Converte o frame para RGB
    pose_results = pose_detector.process(frame_rgb)  # Processa a pose

    if pose_results.pose_landmarks:
        results.append('Activity detected')
    else:
        results.append('No activity detected')
    return results

# Função para transcrição do áudio do vídeo
def transcribe_audio(video_path):
    recognizer = sr.Recognizer()
    audio_file = video_path.replace(".mp4", ".wav")
    clip = VideoFileClip(video_path)

    # Tenta salvar o áudio e continuar mesmo em caso de erro
    try:
        clip.audio.write_audiofile(audio_file)
        print("Audio saved:", audio_file)
    except Exception as e:
        print("Error saving audio:", e)
        return ""

    # Tenta carregar o áudio e fazer a transcrição, mesmo que haja erros
    try:
        with sr.AudioFile(audio_file) as source:
            print("Loading audio for transcription...")
            audio_data = recognizer.record(source)
            print("Audio loaded, transcribing...")
            text = recognizer.recognize_google(audio_data)
            print("Transcription complete.")
        return text
    except Exception as e:
        print("Error during transcription:", e)
        return ""

# Função com timeout para transcrição de áudio
def transcribe_audio_with_timeout(video_path, timeout=420):
    result = [""]  # Lista mutável para armazenar resultado

    def transcribe():
        result[0] = transcribe_audio(video_path)

    thread = threading.Thread(target=transcribe)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        print("Transcription timed out.")
        return ""
    return result[0]

# Função para criar um resumo do texto transcrito
def summarize_text(text):
    summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", revision="a4f8f3e")
    summary = summarizer(text, max_length=50, min_length=25, do_sample=False)
    return summary[0]['summary_text']

# Função segura para resumo de texto com tratamento de erros
def summarize_text_safe(text):
    try:
        return summarize_text(text)
    except Exception as e:
        print("Error during summarization:", e)
        return "Summarization failed."

# Função principal para realizar análise de vídeo
def analyze_video(video_path):
    video_capture = cv2.VideoCapture(video_path)
    total_frames = 0
    anomaly_count = 0
    activities = []
    all_emotions = []

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        total_frames += 1
        if total_frames % FRAMES_TO_ANALYZE == 0:
            face_locations = detect_faces(frame)
            emotions = analyze_emotions(frame, face_locations)
            activities_detected = detect_activities(frame)
            activities.extend(activities_detected)
            all_emotions.extend(emotions)

            if len(activities) > 1 and activities[-1] != activities[-2]:
                anomaly_count += 1

            print(f"Frame: {total_frames}, Activities: {activities_detected}, Emotions: {emotions}")

    video_capture.release()

    # Transcrição do áudio do vídeo com timeout
    transcribed_text = transcribe_audio_with_timeout(video_path)
    print("Transcribed Text:", transcribed_text)

    # Resumo do texto transcrito
    if transcribed_text.strip():
        summary = summarize_text_safe(transcribed_text)
        print("Summary:", summary)
    else:
        summary = "No transcription available."
        print("Summary:", summary)

    # Resumo das emoções detectadas
    emotion_summary = {emotion: all_emotions.count(emotion) for emotion in set(all_emotions)}

    # Cria o relatório final
    report = {
        "Total frames analyzed": total_frames,
        "Number of anomalies detected": anomaly_count,
        "Summary of activities": activities,
        "Emotion summary": emotion_summary,
        "Transcription summary": summary
    }

    return report

# Executa a função de análise e exibe o relatório
if __name__ == "__main__":
    report = analyze_video(VIDEO_PATH)
    print("Analysis Report:")
    print(f"Total frames analyzed: {report['Total frames analyzed']}")
    print(f"Number of anomalies detected: {report['Number of anomalies detected']}")
    print("Summary of activities:", report['Summary of activities'])
    print("Emotion summary:", report['Emotion summary'])
    print("Transcription summary:", report['Transcription summary'])
