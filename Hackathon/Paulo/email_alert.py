import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

# Configurações do e-mail (ideal usar variáveis de ambiente)
EMAIL_REMETENTE = os.getenv("EMAIL_REMETENTE", "fiap.iadev.2023.team18@gmail.com")
EMAIL_SENHA = os.getenv("EMAIL_SENHA", "yymr taas eeuw yptz")
EMAIL_DESTINATARIO = os.getenv("EMAIL_DESTINATARIO", "pauloroberto.mota@gmail.com")

def enviar_alerta(tempo_video, frame_path):
    """ Envia um e-mail quando um objeto cortante for detectado """
    assunto = "⚠️ Alerta de Objeto Cortante Detectado!"
    corpo = f"Objeto cortante detectado no vídeo em {tempo_video:.2f} segundos.\nVeja a imagem em anexo."

    # Criar e-mail
    msg = MIMEMultipart()
    msg["From"] = EMAIL_REMETENTE
    msg["To"] = EMAIL_DESTINATARIO
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "plain"))

    # Anexar a imagem do frame
    if os.path.exists(frame_path):
        with open(frame_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(frame_path)}")
            msg.attach(part)

    try:
        # Conectar ao servidor SMTP do Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()  # Segurança
        server.login(EMAIL_REMETENTE, EMAIL_SENHA)  # Login no e-mail
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())  # Enviar e-mail
        server.quit()

        print(f"🔔 E-mail de alerta enviado para {EMAIL_DESTINATARIO}")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
