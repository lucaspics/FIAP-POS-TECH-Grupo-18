# FIAP VisionGuard - Detecção de Objetos Cortantes

Este projeto é um MVP para detecção de objetos cortantes (facas, armas brancas e de fogo) utilizando inteligência artificial. Ele é capaz de identificar objetos perigosos em vídeos ou pela webcam e enviar alertas por e-mail. O objetivo é validar a viabilidade de integrar esta funcionalidade ao software de monitoramento de câmeras de segurança da FIAP VisionGuard.

## Funcionalidades

- Detecta objetos perigosos em vídeos ou webcam em tempo real.
- Envia alertas por e-mail ao detectar um objeto perigoso.
- Baseado no modelo YOLOv8 treinado com dataset específico.

---

## Estrutura do Projeto

```
fiaphackaton
├── config.py                # Configurações gerais, incluindo e-mail
├── main.py                  # Ponto de entrada do projeto
├── scripts
│   ├── detector.py          # Script principal para detecção
│   ├── train.py             # Script de treinamento do modelo
├── models                   # Modelos treinados e pré-treinados
│   ├── yolov8n.pt           # Modelo YOLOv8 pré-treinado
│   └── weapon-detection3
│       └── weights
│           └── best.pt      # Melhor modelo treinado
├── datasets                 # Dataset utilizado no treinamento
│   └── weapon-dataset
│       ├── train
│       ├── test
│       └── data.yaml
└── README.md                # Documentação do projeto
```

---

## Requisitos

- Python 3.9+
- Dependências listadas no arquivo `requirements.txt`
- Dataset exportado no formato YOLOv8

---

## Instalação

1. Clone o repositório e navegue até a pasta do projeto:

```bash
git clone <URL_DO_REPOSITORIO>
cd fiaphackaton
```

2. Crie um ambiente virtual e ative-o:

```bash
python -m venv venv
# Ativar o ambiente:
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

3. Instale as dependências:

```bash
pip install -r requirements.txt
```

4. Baixe o dataset no formato YOLOv8 e extraia para `datasets/weapon-dataset`.

5. Ajuste o arquivo `config.py` com as credenciais de e-mail para envio de alertas.

---

## Treinamento do Modelo

1. Verifique o arquivo `datasets/weapon-dataset/data.yaml` e assegure-se de que os caminhos do dataset estão corretos:

```yaml
train: C:/Users/rafae/PycharmProjects/fiaphackaton/pythonProject2/datasets/weapon-dataset/train/images
val: C:/Users/rafae/PycharmProjects/fiaphackaton/pythonProject2/datasets/weapon-dataset/test/images
nc: 2
names: ['guns', 'knife']
```

2. Execute o script de treinamento:

```bash
python scripts/train.py
```

3. Após o treinamento, o modelo treinado estará em `models/weapon-detection3/weights/best.pt`.

---

## Uso

1. Execute o script principal para iniciar a detecção em tempo real:

### Para Webcam
```bash
python main.py --source webcam
```

### Para Vídeo
Substitua `<caminho_do_video>` pelo caminho do vídeo:
```bash
python main.py --source <caminho_do_video>
```

2. Para encerrar a detecção, pressione `q` na janela de exibição.

---

## Envio de Alertas por E-mail

- Certifique-se de configurar as credenciais de e-mail em `config.py`:

```python
EMAIL_CONFIG = {
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587,
    "EMAIL": "seu-email@gmail.com",
    "PASSWORD": "sua-senha",
    "RECIPIENT": "destinatario@gmail.com"
}
```

- Um e-mail será enviado sempre que um objeto perigoso for detectado, contendo uma imagem do evento.

---

## Considerações

- **Desempenho:** Certifique-se de usar uma máquina com uma GPU adequada para melhor desempenho.
- **Limitações:** O modelo YOLOv8 e o dataset influenciam diretamente a precisão da detecção. 
- **Melhorias:** Testar com mais classes e ajustar o limiar de confiança pode reduzir falsos positivos.

---

## Créditos

- Desenvolvido com base no modelo YOLOv8 pela Ultralytics.
- Dataset utilizado: [Weapon-2 Dataset](https://universe.roboflow.com/joao-assalim-xmovq/weapon-2/dataset/2).

---