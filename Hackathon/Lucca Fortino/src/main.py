import sys
import cv2
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QListWidget, QListWidgetItem, QLineEdit, QTabWidget
)
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import QTimer, Qt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import asyncio
import aiosmtplib
from qasync import QEventLoop

class SecurityCameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Câmera de Segurança")
        self.setGeometry(100, 100, 1000, 600)

        # Tamanho padrão do vídeo
        self.video_width = 640
        self.video_height = 480

        # Variáveis de controle
        self.analysis_interval = 30  # Intervalo de análise em frames
        self.current_frame_count = 0

        # Layout principal
        self.main_layout = QHBoxLayout()  # Layout horizontal para incluir vídeo e logs
        self.setLayout(self.main_layout)

        # Adiciona um TabWidget para abas
        self.tabs = QTabWidget()
        self.main_layout.addWidget(self.tabs)

        # Aba de vídeo
        self.video_tab = QWidget()
        self.tabs.addTab(self.video_tab, "Vídeo")
        self.video_layout = QHBoxLayout()  # Alterado para HBoxLayout para mover logs para a direita
        self.video_tab.setLayout(self.video_layout)

        # Layout esquerdo (vídeo e controles)
        self.left_layout = QVBoxLayout()
        self.video_layout.addLayout(self.left_layout)

        # Título da seção de vídeo
        self.video_title = QLabel("Monitoramento de Vídeo")
        self.video_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.left_layout.addWidget(self.video_title)

        # Widgets de vídeo
        self.video_label = QLabel("Feed da câmera aparecerá aqui")
        self.video_label.setFixedSize(self.video_width, self.video_height)
        self.video_label.setStyleSheet("background-color: black;")
        self.left_layout.addWidget(self.video_label)

        # Overlay acima do vídeo
        self.overlay_label = QLabel(self.video_label)
        self.overlay_label.setFixedSize(self.video_width, self.video_height)
        self.overlay_label.setAlignment(Qt.AlignCenter)
        self.overlay_label.setStyleSheet("background: transparent;")  # Garantir transparência

        # Carrega a imagem do overlay
        overlay_path = "src/assets/images/cam_overlay.png"
        if os.path.exists(overlay_path):
            self.overlay_pixmap = QPixmap(overlay_path).scaled(
                self.video_width, self.video_height, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.overlay_label.setPixmap(self.overlay_pixmap)
        else:
            print(f"Overlay não encontrado: {overlay_path}")

        self.time_label = QLabel("Tempo: 0s")
        self.left_layout.addWidget(self.time_label)

        self.connect_button = QPushButton("Conectar à Câmera")
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        self.connect_button.clicked.connect(self.connect_camera)
        self.left_layout.addWidget(self.connect_button)

        # Controles de tempo
        self.controls_layout = QHBoxLayout()

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.setEnabled(False)
        self.play_pause_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 14px;")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.controls_layout.addWidget(self.play_pause_button)

        self.rewind_button = QPushButton("Retroceder 5s")
        self.rewind_button.setEnabled(False)
        self.rewind_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")
        self.rewind_button.clicked.connect(self.rewind_video)
        self.controls_layout.addWidget(self.rewind_button)

        self.forward_button = QPushButton("Avançar 5s")
        self.forward_button.setEnabled(False)
        self.forward_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")
        self.forward_button.clicked.connect(self.forward_video)
        self.controls_layout.addWidget(self.forward_button)

        self.left_layout.addLayout(self.controls_layout)

        self.alert_button = QPushButton("Disparar Alerta")
        self.alert_button.setEnabled(False)
        self.alert_button.setStyleSheet("background-color: #e7e7e7; color: black; font-size: 14px;")
        self.alert_button.clicked.connect(self.trigger_alert)
        self.left_layout.addWidget(self.alert_button)

        # Painel de Logs Visuais
        self.logs_list = QListWidget()
        self.logs_list.setFixedWidth(300)
        self.logs_list.itemClicked.connect(self.jump_to_alert)
        self.video_layout.addWidget(self.logs_list)  # Movido para a direita

        # Aba de Configurações
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "Configurações")
        self.settings_layout = QVBoxLayout()
        self.settings_layout.setAlignment(Qt.AlignTop)  # Alinha os itens no topo
        self.settings_tab.setLayout(self.settings_layout)

        # Título da seção de configurações
        self.settings_title = QLabel("Configurações do Sistema")
        self.settings_title.setFont(QFont("Arial", 16, QFont.Bold))
        self.settings_layout.addWidget(self.settings_title)

        # Campo de Email
        self.email_label = QLabel("Email para alertas:")
        self.email_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.settings_layout.addWidget(self.email_label)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Digite o email para alertas")
        self.email_input.setText("fiap.iadev.2023.team18@gmail.com")
        self.settings_layout.addWidget(self.email_input)

        # Campo de Intervalo de Análise
        self.interval_label = QLabel("Intervalo de análise de frames:")
        self.interval_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.settings_layout.addWidget(self.interval_label)
        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText("Intervalo de análise de frames (em frames)")
        self.interval_input.setText(str(self.analysis_interval))  # Define o valor padrão inicial
        self.settings_layout.addWidget(self.interval_input)

        # Botão para salvar configurações
        self.save_button = QPushButton("Salvar Configurações")
        self.save_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")
        self.save_button.clicked.connect(self.save_settings)
        self.settings_layout.addWidget(self.save_button)

        # Variáveis de controle
        self.video_path = None
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.is_playing = False

    def connect_camera(self):
        options = QFileDialog.Options()
        self.video_path, _ = QFileDialog.getOpenFileName(
            self, "Selecione o vídeo", "", "Arquivos de Vídeo (*.mp4 *.avi *.mov)", options=options
        )
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            if self.cap.isOpened():
                # Ativa os controles
                self.play_pause_button.setEnabled(True)
                self.rewind_button.setEnabled(True)
                self.forward_button.setEnabled(True)
                self.alert_button.setEnabled(True)

                # Desativa o botão de conectar
                self.connect_button.setEnabled(False)

                print(f"Vídeo carregado: {self.video_path}")
                self.toggle_play_pause()  # Inicia automaticamente em modo Play
            else:
                print("Erro ao carregar o vídeo.")

    def toggle_play_pause(self):
        if self.is_playing:
            self.timer.stop()
            self.play_pause_button.setText("Play")
        else:
            self.timer.start(30)  # Atualiza o frame a cada 30ms (~33 FPS)
            self.play_pause_button.setText("Pause")
        self.is_playing = not self.is_playing

    def rewind_video(self):
        if not self.cap:
            return
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        target_frame = max(0, current_frame - 150)  # 5 segundos (30 FPS * 5)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    def forward_video(self):
        if not self.cap:
            return
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        total_frames = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        target_frame = min(total_frames - 1, current_frame + 150)  # 5 segundos (30 FPS * 5)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            print("Fim do vídeo.")
            self.timer.stop()
            self.is_playing = False
            self.play_pause_button.setText("Play")
            return

        # Redimensiona o frame para o tamanho padrão
        frame = cv2.resize(frame, (self.video_width, self.video_height))

        # Converte o frame para QImage
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        step = channel * width
        qimg = QImage(frame_rgb.data, width, height, step, QImage.Format_RGB888)

        # Exibe o frame no QLabel
        self.video_label.setPixmap(QPixmap.fromImage(qimg))

        # Atualiza o tempo no label
        current_time = int(self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
        self.time_label.setText(f"Tempo: {current_time}s")

        # Incrementa o contador de frames
        self.current_frame_count += 1

        # Verifica se é hora de analisar o frame
        if self.current_frame_count % self.analysis_interval == 0:
            self.analyze_frame(frame_rgb)

    def analyze_frame(self, frame_rgb):
        # API para análise de frame
        print("Analisando frame...")  # Placeholder para futura implementação de análise
        # Aqui você pode adicionar código para processar a imagem do frame

    def trigger_alert(self):
        if not self.cap or not self.cap.isOpened():
            print("Erro: Nenhum vídeo conectado.")
            return

        ret, frame = self.cap.read()
        if not ret:
            print("Não foi possível capturar o frame.")
            return

        # Tempo do vídeo em milissegundos
        current_time = int(self.cap.get(cv2.CAP_PROP_POS_MSEC))
        alert_time = datetime.now().strftime("%H:%M:%S")
        alert_frame_path = f"alert-{current_time}.png"

        cv2.imwrite(alert_frame_path, frame)

        # Adiciona o log visual
        item_widget = QWidget()
        item_layout = QHBoxLayout()
        item_layout.setContentsMargins(0, 0, 0, 0)

        thumb_pixmap = QPixmap(alert_frame_path).scaled(100, 75)
        thumb_label = QLabel()
        thumb_label.setPixmap(thumb_pixmap)
        item_layout.addWidget(thumb_label)

        text_label = QLabel(f"Tempo: {current_time}ms\nAlerta detectado")
        item_layout.addWidget(text_label)

        item_widget.setLayout(item_layout)
        list_item = QListWidgetItem()
        list_item.setSizeHint(item_widget.sizeHint())
        list_item.setData(0, current_time)  # Associa o tempo ao item

        self.logs_list.addItem(list_item)
        self.logs_list.setItemWidget(list_item, item_widget)

        # Enviar e-mail de forma assíncrona
        subject = f"Security Cam - Alert - {alert_time}"
        body = f"""
        <h2>Security Camera Alert</h2>
        <p><b>Tempo:</b> {alert_time}</p>
        <p><b>Mensagem:</b> Alerta detectado.</p>
        """
        asyncio.create_task(self.send_email(subject, body, alert_frame_path))

    def jump_to_alert(self, item):
        """Salta para 1 segundo antes do alerta."""
        if not self.cap:
            return

        alert_time = item.data(0)  # Recupera o tempo associado ao item
        target_time = max(0, alert_time - 1000)  # 1 segundo antes
        self.cap.set(cv2.CAP_PROP_POS_MSEC, target_time)

        # Atualiza manualmente o frame para garantir que o vídeo mostre o estado correto
        ret, frame = self.cap.read()
        if ret:
            # Redimensiona e exibe o frame
            frame = cv2.resize(frame, (self.video_width, self.video_height))
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame.shape
            step = channel * width
            qimg = QImage(frame.data, width, height, step, QImage.Format_RGB888)

            # Exibe o frame no QLabel
            self.video_label.setPixmap(QPixmap.fromImage(qimg))

            # Certifica-se de que o overlay ainda está visível
            self.overlay_label.raise_()

    async def send_email(self, subject, body, attachment_path):
        # Configurações do servidor SMTP
        EMAIL_ADDRESS = "fiap.iadev.2023.team18@gmail.com"  # Substitua pelo seu e-mail
        EMAIL_PASSWORD = "yymr taas eeuw yptz"  # Substitua pela sua senha
        
        SMTP_SERVER = "smtp.gmail.com"
        SMTP_PORT = 587

        # Configuração do destinatário
        TO_EMAIL = self.email_input.text()  # Usa o email do campo de configuração

        if not TO_EMAIL:
            print("Erro: Campo de email vazio.")
            self.email_input.setStyleSheet("border: 1px solid red;")
            return
        else:
            self.email_input.setStyleSheet("")

        # Configurar o e-mail
        msg = MIMEMultipart()
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = TO_EMAIL
        msg["Subject"] = subject

        # Corpo do e-mail
        msg.attach(MIMEText(body, "html"))

        # Anexar a imagem, se disponível
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={os.path.basename(attachment_path)}",
            )
            msg.attach(part)

        # Enviar o e-mail
        try:
            await aiosmtplib.send(
                msg,
                hostname=SMTP_SERVER,
                port=SMTP_PORT,
                start_tls=True,
                username=EMAIL_ADDRESS,
                password=EMAIL_PASSWORD,
            )
            print(f"E-mail enviado com sucesso para {TO_EMAIL}.")
        except Exception as e:
            print(f"Erro ao enviar o e-mail: {e}")

    def save_settings(self):
        # Salva o intervalo de análise
        try:
            self.analysis_interval = int(self.interval_input.text())
            self.interval_input.setStyleSheet("")
        except ValueError:
            print("Erro: Intervalo de análise inválido.")
            self.interval_input.setStyleSheet("border: 1px solid red;")

        # Reinicia o contador de frames para aplicar o novo intervalo
        self.current_frame_count = 0

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    window = SecurityCameraApp()
    window.show()
    with loop:
        loop.run_forever()
