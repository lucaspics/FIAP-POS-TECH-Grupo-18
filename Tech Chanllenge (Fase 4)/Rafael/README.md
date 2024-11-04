# Análise de Vídeo com Reconhecimento Facial e Detecção de Atividades

Este projeto é uma aplicação em Python que realiza a análise de um vídeo, utilizando técnicas de reconhecimento facial, análise de expressões emocionais, detecção de atividades e geração de resumo de texto. O vídeo a ser analisado deve estar na raiz do projeto com o nome `video-tc4.mp4`.

## Funcionalidades

1. **Reconhecimento Facial:** Identifica e marca rostos presentes no vídeo.
2. **Análise de Expressões Emocionais:** Analisa as expressões emocionais dos rostos identificados.
3. **Detecção de Atividades:** Detecta e categoriza as atividades realizadas no vídeo.
4. **Transcrição de Áudio:** Transcreve o áudio do vídeo para texto.
5. **Geração de Resumo:** Cria um resumo automático das principais atividades e emoções detectadas.

## Tecnologias Utilizadas

- **Python:** Linguagem de programação.
- **Bibliotecas:**
  - `face_recognition`: Para reconhecimento facial.
  - `DeepFace`: Para análise de expressões emocionais.
  - `MoviePy`: Para manipulação de vídeo e áudio.
  - `SpeechRecognition`: Para transcrição de áudio.
  - `transformers`: Para sumarização de texto.
  - `mediapipe`: Para detecção de atividades.

## Pré-requisitos

Antes de executar o projeto, certifique-se de ter o Python e as bibliotecas necessárias instaladas. Você pode instalar as dependências necessárias utilizando o `pip`:

```bash
pip install face_recognition deepface moviepy SpeechRecognition transformers mediapipe opencv-python --user
```

## Pré-requisitos
```
/project-root
│
├── video-tc4.mp4         # Vídeo a ser analisado
├── analyze_video.py      # Código principal para análise do vídeo
└── README.md             # Documentação do projeto
```
## Como Executar o Projeto
1- Clone ou baixe o repositório para o seu computador.

2- Navegue até a pasta do projeto.

3- Execute o script Python com o seguinte comando:
```
python analyze_video.py
```

4- O resultado da análise será exibido no console, incluindo:
* Total de frames analisados.
* Número de anomalias detectadas.
* Resumo das atividades e emoções.

