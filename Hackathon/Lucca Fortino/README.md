# VisionGuard System

Sistema de detecção de objetos cortantes em tempo real usando YOLOv8.

## Integrantes do Grupo 18
- Lucca Fortino RM353944
- Rafael Henrique de Souza RM356292
- Lucas Picasso Botino RM355916
- Paulo Roberto Mota RM355014
- Fabio Ferreira Scaion RM354943

## Link para o vídeo de Apresentação
https://youtu.be/SCtTDisKDPY

## Descrição do Projeto

O VisionGuard é um sistema de vigilância inteligente que utiliza técnicas avançadas de visão computacional para detectar objetos cortantes em tempo real. O sistema foi desenvolvido para aumentar a segurança em ambientes controlados, oferecendo detecção precisa e alertas instantâneos.

### Funcionalidades Principais

1. **Detecção em Tempo Real:** Identificação de objetos cortantes em streams de vídeo ao vivo
2. **Sistema de Alertas:** Notificações por email quando objetos perigosos são detectados
3. **Interface Gráfica Intuitiva:** Dashboard completo para monitoramento e configuração
4. **Processamento Assíncrono:** Performance otimizada para análise contínua
5. **Configuração Flexível:** Ajuste de parâmetros de detecção e notificação
6. **Logging Completo:** Registro detalhado de eventos e detecções

## Configuração

1. Clone o repositório
2. Execute `install.bat` para instalar as dependências

## Uso

1. Execute `run.bat` para iniciar o sistema
2. Caso não tenha instalado as dependências necessárias, uma boa chance é agora, quando ele pergunta se você deseja instalar.
3. Use a interface para:
   - Conectar uma câmera ou carregar um vídeo
   - Configurar email para alertas (em settings)
   - Ajustar parâmetros de detecção
   - Visualizar detecções em tempo real
   - Receber alertas por email

## Tecnologias Utilizadas

- **Python 3.8+:** Linguagem principal do projeto
- **YOLOv8:** Framework de detecção de objetos em tempo real
- **PyQt6:** Interface gráfica moderna e responsiva
- **OpenCV:** Processamento de imagem e vídeo
- **SQLite:** Armazenamento local de configurações e logs
- **SMTP:** Sistema de envio de alertas por email
- **Make Sense:** Ferramenta online que facilita o labeling de imagens

## Configurações

### Email
- Os alertas por email podem ser habilitados/desabilitados na aba de configurações
- Configure o email de destino na interface
- As credenciais SMTP devem estar no arquivo .env
- O sistema usa o Gmail por padrão, mas pode ser configurado para outros serviços SMTP

### Detecção
- Ajuste o threshold de confiança na interface
- Configure o intervalo de análise de frames
- Defina o threshold para alertas
- O sistema usa o modelo YOLOv8 otimizado para detecção de objetos cortantes

### Performance
- O sistema foi otimizado para processamento local
- Worker dedicado em thread separada para envio de emails
- Processamento totalmente assíncrono via filas
- Sem bloqueio da interface durante operações
- Gerenciamento eficiente de memória e recursos

## Requisitos

### Sistema
- Python 3.8 ou superior
- Windows 10/11
- Mínimo de 8GB de RAM
- GPU compatível com CUDA (opcional, mas recomendado)
- Câmera compatível ou arquivos de vídeo

### Python
```bash
pip install -r requirements.txt
```

## Estrutura do Projeto

```
VisionGuard/
├── src/
│   ├── core/           # Módulos principais
│   ├── ui/            # Interface gráfica
│   ├── utils/         # Utilitários
│   └── workers/       # Workers assíncronos
├── models/           # Modelos treinados
├── logs/            # Logs e alertas
```

## Modelo de Detecção

### Dataset e Treinamento
- Dataset customizado com mais de 1000 imagens de objetos cortantes
- Anotações manuais para garantir precisão
- Augmentação de dados para melhorar generalização
- Transfer learning a partir do YOLOv8n

### Métricas de Performance
- Precisão média (mAP): 0.89
- Recall: 0.85
- Taxa de falsos positivos: < 0.1
- Tempo médio de inferência: 30ms (GPU)

## Descrição Técnica

### Arquitetura do Sistema

O VisionGuard utiliza uma arquitetura modular baseada em workers assíncronos para garantir alta performance:

1. **Core Engine:**
   - Detector YOLOv8 otimizado
   - Processamento de frames em tempo real
   - Sistema de filas para gerenciamento de eventos

2. **Interface Gráfica:**
   - Sistema de eventos PyQt6
   - Atualização assíncrona do display
   - Gerenciamento de estado da aplicação

3. **Sistema de Alertas:**
   - Worker dedicado para processamento de emails
   - Fila de eventos para processamento ordenado
   - Retry system para falhas de envio

### Performance

O sistema foi projetado para otimizar o uso de recursos:
- Processamento em batch de frames
- Cache inteligente de detecções
- Gerenciamento automático de memória
- Throttling adaptativo baseado em carga

## Troubleshooting

### Problemas com Email
1. Verifique se as credenciais no .env estão corretas
2. Confirme se a verificação em duas etapas está ativa no Gmail
3. Use uma senha de app gerada especificamente para o VisionGuard
4. Verifique os logs para mensagens de erro detalhadas
5. Monitore o status do worker de email nos logs do sistema
6. Reinicie a aplicação se o worker de email não estiver respondendo

### Problemas de Detecção
1. Ajuste o threshold de confiança
2. Verifique a iluminação e qualidade do vídeo
3. Confirme se o modelo está carregado corretamente
4. Verifique os logs de detecção


# Mais detalhes técnicos:
docs\technical
