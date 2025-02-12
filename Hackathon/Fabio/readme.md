# Sobre o Projeto VisionGuard

O projeto visa construir um sistema de reconhecimento de objetos perigosos cortantes que ameaçam a segurança de pessoas por meio de IA.

## Crie o ambiente virtual

```
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

## Instale as dependencias do projeto:

- ultralytics
- CV2
- Flask
- Flask_socketio
- requests
- time
- sqlite3
- smtplib

## Rodar o projeto

Para rodar o projeto primeiro executo o comando para criar a base de dados que ira salvar os incidentes registrados

```
python database_init.py
```

Após execute os dois comandos para rodar o server que ira subir o sistema web com a captura em tempo real dos incidentes e o programa inicial que irá fazer a detecção dos objetos

```
python server.py # inicia o servidor
python init.py # inicia a detecção de objetos
```

Ao executar o servidor voc6e poderá acessar pelo endereço http://localhost:5000
Ao executar o comando de init serão exibidas 3 opções:
```
Choose video input:
1 - Webcam
2 - Video1
3 - Video2
Enter the number corresponding to your choice:
```

Você poderá escolher por executar o programa de detecção de objetos apartir de uma webcam ou por 2 videos predefinidos de teste

## Treinamento do Modelo

Para o treinamento do modelo foi utilizado o yolo como base e um dataset extraido da internet, o mesmo pode ser encontrado na pastar datasets/datasets e para realizar o treinamento foi executado o seguinte comando
```
python Utils/trainModels.py
```

# Arquivos do projeto

## Init.py

### Componentes Principais

### 1. Modelo YOLOv8
O YOLOv8 é um modelo de detecção de objetos que consegue identificar e localizar objetos em imagens ou vídeos com alta precisão e velocidade. Neste sistema, o modelo é carregado a partir de um arquivo de pesos pré-treinados, mas pode ser substituído por um modelo personalizado, caso necessário.

### 2. Lista de Objetos Afiados
O sistema é configurado para detectar uma lista específica de objetos afiados, como facas, tesouras, lâminas, entre outros. Essa lista pode ser ajustada conforme a necessidade do usuário, permitindo a detecção de outros objetos perigosos.

### 3. Escolha da Fonte de Vídeo
O sistema permite ao usuário escolher entre três opções de entrada de vídeo:

Webcam: Captura vídeo em tempo real a partir da câmera do computador.

Vídeo 1 e Vídeo 2: Utiliza vídeos pré-gravados armazenados em pastas específicas.

Caso o usuário não faça uma escolha válida, o sistema assume a webcam como fonte padrão.

### 4. Processamento de Frames
O sistema captura frames da fonte de vídeo selecionada e os processa utilizando o modelo YOLOv8. Para cada frame, o modelo realiza a detecção de objetos e verifica se algum dos objetos detectados está na lista de objetos afiados.

### 5. Detecção de Objetos Afiados
Quando um objeto afiado é detectado, o sistema realiza as seguintes ações:

Desenha uma caixa delimitadora: O objeto detectado é destacado no frame com uma caixa verde e o nome do objeto é exibido acima da caixa.

Salva uma imagem: O frame é salvo como uma imagem no sistema, com um nome único baseado no timestamp.

Registra o incidente: O sistema insere um registro do incidente em um banco de dados, armazenando o nome da imagem e uma mensagem de alerta.

Envia um e-mail: Um e-mail é enviado para um destinatário pré-definido, contendo a imagem capturada e uma mensagem de alerta.

Evita múltiplos alertas: Para evitar o envio de vários e-mails em um curto período, o sistema aguarda 10 segundos após cada detecção.

### 6. Exibição do Vídeo
O vídeo processado, com as detecções em tempo real, é exibido em uma janela. O usuário pode interromper o sistema a qualquer momento pressionando a tecla 'q'.

## Server.py

### Componentes Principais

Flask: É o núcleo do framework Flask, usado para criar a aplicação web.

render_template: Uma função do Flask que permite renderizar templates HTML.

SocketIO: Uma extensão do Flask que habilita a comunicação bidirecional em tempo real entre o cliente e o servidor usando WebSockets.

get_incidents e delete_incident: Funções importadas de um módulo chamado Utils.database. Essas funções são responsáveis por interagir com o banco de dados para obter e excluir registros de incidentes.

### Inicialização da Aplicação:

A aplicação Flask é criada e uma instância do SocketIO é associada a ela. Isso permite que a aplicação suporte WebSockets.

### WebSocket - Conexão do Cliente:

Quando um cliente se conecta ao servidor via WebSocket, a função handle_connect é chamada. Ela imprime uma mensagem no console indicando que o cliente foi conectado e envia uma atualização de mensagens (incidentes) para o cliente usando a função emit.

### Rota Principal (/):

A rota principal (/) renderiza um template HTML chamado index.html. Esse template recebe um título e uma lista de mensagens (incidentes) obtidas do banco de dados. Essas mensagens são exibidas na página web.

### Rota de Atualização (/update):

Quando esta rota é acessada, o servidor emite uma atualização para todos os clientes conectados via WebSocket, enviando a lista mais recente de incidentes. Isso permite que a interface do cliente seja atualizada em tempo real.

### Rota de Exclusão (/delete/<id>):

Esta rota permite a exclusão de um incidente específico com base no id fornecido na URL. Após a exclusão, uma resposta é enviada indicando que o incidente foi deletado.

### Execução da Aplicação:

A aplicação é executada com o socketio.run, que inicia o servidor Flask com suporte a WebSockets. O modo debug=True é ativado para facilitar o desenvolvimento, pois ele recarrega automaticamente o servidor quando há mudanças no código e exibe mensagens de erro detalhadas.