# Análise de Vídeo com Reconhecimento Facial e Detecção de Atividades

Este projeto é uma aplicação em Python que realiza a análise de um vídeo, utilizando técnicas de reconhecimento facial, análise de expressões emocionais, detecção de atividades e geração de resumo de texto. O vídeo a ser analisado deve estar na raiz do projeto com o nome `video-tc4.mp4`.

## Integrantes do Grupo
*Rafael RM356292*

*Lucas RM355916*

*Lucca RM353944*

*Paulo RM355014*

*Fábio RM354943*

## Link para o vídeo de Apresentação
https://youtu.be/ (Adicionar o link final da Apresentação)

## Funcionalidades

1. **Reconhecimento Facial:** Identifica e marca os rostos presentes no vídeo.
2. **Análise de Expressões Emocionais:** Detecta emoções predominantes como felicidade, tristeza, raiva, neutralidade, entre outras.
3. **Classificação Anômalas:** Classifica emoções anômalas quando múltiplas emoções significativas são detectadas em um rosto.
4. **Detecção de Atividades:** Detecta movimentos como braços levantados, mãos próximas ao rosto ou braços curvados.
5. **Classificação de Atividades Anômalas:** Classifica atividades anômalas quando múltiplos movimentos divergentes ocorrem simultaneamente.
5. **Resumo e Visualização:** Gera gráficos que resumem as emoções e atividades detectadas.
6. **Vídeo Processado com Marcações:** Salva o vídeo com marcações visuais indicando emoções e atividades detectadas.

## Tecnologias Utilizadas

- **Python:** Linguagem principal do projeto.
- **Bibliotecas:**
  - `DeepFace`: Para análise de expressões emocionais.
  - `mediapipe`: Para detecção de atividades corporais.
  - `opencv-python`: Para manipulação de vídeo.
  - `matplotlib`: Para geração de gráficos e visualizações.

## Pré-requisitos

Antes de executar o projeto, certifique-se de ter o Python 3.x e as bibliotecas necessárias instaladas. Instale as dependências com o comando:

```bash
pip install deepface mediapipe opencv-python matplotlib --user
```

## Estrutura do Projeto
```
/project-root
│
├── video-tc4.mp4         # Vídeo a ser analisado
├── tc-4.py               # Código principal para análise do vídeo
├── output_video.mp4      # Vídeo processado com as marcações (gerado pelo script)
└── README.md             # Documentação do projeto
```
## Como Executar o Projeto
1- Clone ou baixe o repositório para o seu computador.

2- Navegue até a pasta do projeto.

3- Execute o script Python com o seguinte comando:
```
python tc-4.py
```

4- Resultados Gerados:
* Um vídeo processado será salvo como output_video.mp4, com marcações das emoções e atividades detectadas.
* Resumo exibido no console, incluindo: (Total de frames analisados, Número de anomalias detectadas, Resumo das atividades e emoções)

5- Visualização Gráfica:
* Após a execução, gráficos das atividades e emoções detectadas serão exibidos.
