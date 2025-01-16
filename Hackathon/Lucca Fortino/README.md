# Sistema de Câmera de Segurança

Este projeto é um sistema de câmera de segurança desenvolvido em Python, utilizando a biblioteca PyQt5 para a interface gráfica e OpenCV para manipulação de vídeo.

## Dependências

Para executar este projeto, você precisará das seguintes bibliotecas Python:

- PyQt5
- OpenCV
- aiosmtplib

Você pode instalar todas as dependências usando o seguinte comando:

```bash
pip install PyQt5 opencv-python aiosmtplib
```

## Gerando o Executável

Para gerar um arquivo executável (.exe) do projeto, siga os passos abaixo:

1. **Instale o PyInstaller**: Certifique-se de que o PyInstaller está instalado no seu ambiente Python. Caso não esteja, instale-o com o comando:

   ```bash
   pip install pyinstaller
   ```

2. **Crie o Executável**: Navegue até o diretório do projeto e execute o seguinte comando para gerar o executável:

   ```bash
   python -m PyInstaller --onefile --windowed src/main.py
   ```

   O executável será gerado na pasta `dist` dentro do diretório do projeto.

## Estrutura do Projeto

- `src/main.py`: Arquivo principal do projeto que contém a lógica do sistema de câmera de segurança.
- `logs/`: Diretório onde os arquivos de log são salvos.

## Uso

1. Execute o arquivo `main.exe` gerado na pasta `dist`.
2. Configure o email para alertas na aba de configurações.
3. Conecte-se a um vídeo para iniciar o monitoramento.

## Contato

Para mais informações, entre em contato com o time de desenvolvimento em fiap.iadev.2023.team18@gmail.com.