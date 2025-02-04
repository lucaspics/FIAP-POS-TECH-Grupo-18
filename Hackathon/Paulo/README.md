# 🔪 Detecção de Objetos Cortantes com IA e Alertas por E-mail

## 📌 Sobre o Projeto
Este projeto é o projeto final da turma de pós-graduação IA para DEVs da FIAP. Ele utiliza Inteligência Artificial (IA) e Visão Computacional para detectar objetos cortantes (como facas e tesouras) em vídeos. Caso um objeto seja identificado, o sistema:

1. **Exibe o alerta no console** 📢
2. **Salva um frame da detecção** 📸
3. **Envia um e-mail com o frame anexado** ✉️
4. **Evita e-mails duplicados** ao aguardar pelo menos 30 segundos entre alertas ⏳

## 🚀 Tecnologias Utilizadas
- **Python 3.8+**
- **PyTorch** (Treinamento e Inferência)
- **OpenCV** (Processamento de Vídeo)
- **Torchvision** (Modelos pré-treinados)
- **smtplib** (Envio de e-mails)
- **PIL (Pillow)** (Manipulação de imagens)

## 📁 Estrutura do Projeto
```
├── dataset/                # (Opcional) Dataset para treinamento
│   ├── train/
│   ├── val/
├── frames_detectados/      # Frames capturados durante a detecção
├── email_alert.py          # Módulo para envio de e-mails
├── 1_train.py                # Script para treinar o modelo
├── 2_predict_image.py        # Script de detecção em images (criado apenas para validação)
├── 3_predict_video.py        # Script de detecção em vídeos
├── modelo_resnet18.pth     # Modelo treinado salvo
├── requirements.txt        # Dependências do projeto
├── README.md               # Documentação do projeto
```

## 🔧 Instalação
1. **Clone o repositório**
   ```bash
   git clone git@github.com:lucaspics/FIAP-POS-TECH-Grupo-18.git
   cd Hackathon/Paulo
   ```

2. **Crie um ambiente virtual (opcional, recomendado)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ Como Rodar o Projeto

### **1️⃣ Treinar o modelo**
```bash
python 1_train.py
```

Essa etapas é fundamental para gerar o arquivo do modelo que será usado pelo script de detecção. Para o projeto foi incluído um numero restrito de imagens a fim de tornar mais acessível em computadores pessoais comuns. 

### **2️⃣ Rodar a Detecção em Vídeos**
```bash
python 3_predict_video.py
```

### **3️⃣ Configurar Envio de E-mail**
1. No arquivo `email_alert.py`, configure suas credenciais:
   ```python
   EMAIL_REMETENTE = "seuemail@gmail.com"
   EMAIL_SENHA = "suasenha"
   EMAIL_DESTINATARIO = "destinatario@gmail.com"
   ```
2. Caso use **Gmail**, ative a autenticação para **apps menos seguros** ou gere uma **senha de app** [aqui](https://myaccount.google.com/security).

## 🛠 Melhorias Futuras
✅ Deploy como API usando **Flask** ou **FastAPI**  
✅ Integração com **câmeras ao vivo** para monitoramento em tempo real  
✅ Notificações via **WhatsApp ou Telegram**  

📩 **Dúvidas ou sugestões?** Sinta-se à vontade para abrir uma _issue_ ou contribuir com o projeto! 🚀

