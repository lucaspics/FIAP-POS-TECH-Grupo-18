import cv2
import torch
from ultralytics import YOLO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import threading  # Para evitar travamento no envio de e-mail
from collections import defaultdict, deque  # Para histórico de detecções


class Detector:
    def __init__(self, model_path, email_config):
        self.model = YOLO(model_path)  # Carrega o modelo YOLO
        self.email_config = email_config
        self.class_names = ['cortante']  # Adicione os nomes das classes na ordem do treinamento
        self.alert_sent = set()  # Para rastrear os objetos detectados e evitar múltiplos envios
        self.detection_history = defaultdict(lambda: deque(maxlen=3))  # Histórico de detecções (últimos 3 frames)

    def send_email_thread(self, frame):
        """Executa o envio de e-mail em uma thread separada."""
        thread = threading.Thread(target=self.send_alert, args=(frame,))
        thread.start()

    def send_alert(self, frame):
        """Envia um alerta por e-mail com a imagem capturada."""
        try:
            print("[INFO] Tentando enviar alerta por e-mail...")
            server = smtplib.SMTP_SSL(self.email_config["SMTP_SERVER"], self.email_config["SMTP_PORT"])
            server.login(self.email_config["EMAIL"], self.email_config["PASSWORD"])

            # Configuração do e-mail
            msg = MIMEMultipart()
            msg['From'] = self.email_config["EMAIL"]
            msg['To'] = self.email_config["RECIPIENT"]
            msg['Subject'] = "Alerta: Objeto Perigoso Detectado"

            body = "Um objeto perigoso foi detectado. Confira a imagem em anexo."
            msg.attach(MIMEText(body, 'plain'))

            # Adiciona a imagem
            _, img_encoded = cv2.imencode('.jpg', frame)
            img_attachment = MIMEImage(img_encoded.tobytes(), name="alert.jpg")
            msg.attach(img_attachment)

            # Envia o e-mail
            server.sendmail(self.email_config["EMAIL"], self.email_config["RECIPIENT"], msg.as_string())
            server.quit()
            print("[INFO] Alerta enviado com sucesso.")
        except Exception as e:
            print(f"[ERRO] Falha ao enviar alerta: {e}")

    def detect(self, source):
        """Processa a fonte (webcam ou vídeo) e detecta objetos."""
        cap = cv2.VideoCapture(1 if source == "webcam" else source)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Realiza a detecção
            results = self.model(frame)

            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls = int(box.cls.cpu().numpy())  # Classe do objeto detectado
                    conf = float(box.conf.cpu().numpy())  # Confiança da detecção

                    # Define a cor com base na classe
                    if cls == 0:  # guns
                        color = (255, 0, 0)  # Azul
                    elif cls == 1:  # knife
                        color = (0, 255, 255)  # Amarelo
                    else:
                        color = (0, 0, 255)  # Vermelho padrão

                    # Condição para desenhar a caixa
                    if conf > 0.5:  # Confiança mínima para desenhar
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()  # Coordenadas da caixa
                        x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))  # Converte para inteiros

                        # Desenhar a caixa na imagem com a cor definida
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                        # Adicionar o nome da classe e a confiança no rótulo
                        label = f"{self.class_names[cls]} ({conf:.2f})"
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                    # Adicionar a detecção ao histórico
                    self.detection_history[cls].append(conf > 0.7)  # Verifica se a confiança é > 70%

                    # Verifica se o objeto foi detectado consistentemente nos últimos 3 frames
                    if len(self.detection_history[cls]) == 3 and all(self.detection_history[cls]):
                        # Enviar e-mail apenas se a confiança for maior que 80%
                        if conf > 0.8 and cls not in self.alert_sent:
                            print(f"[INFO] Enviando alerta para: {self.class_names[cls]} com confiança de {conf:.2f}")
                            self.alert_sent.add(cls)
                            self.send_email_thread(frame)

            # Exibe o vídeo
            cv2.imshow("Detecção", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def run(self, source):
        """Executa a detecção com a fonte especificada."""
        self.detect(source)