# Function to send an email with the image attached
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

def send_email(recipient, subject, message, image_path):
    # SMTP server settings
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    sender = 'fiap.iadev.2023.team18@gmail.com'  # Replace with your email
    password = 'yymr taas eeuw yptz'  # Replace with your password or app password

    # Create the message
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject

    # Add the message text
    msg.attach(MIMEText(message, 'plain'))

    # Add the image as an attachment
    with open(image_path, 'rb') as img:
        mime_image = MIMEImage(img.read(), name='detected_object.jpg')
        msg.attach(mime_image)

    # Connect to the SMTP server and send the email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")
    finally:
        server.quit()