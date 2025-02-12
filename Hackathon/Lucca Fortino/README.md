# VisionGuard System

Sistema de detecção de objetos cortantes em tempo real usando YOLOv8.

## Configuração

1. Clone o repositório
2. Execute `install.bat` para instalar as dependências

## Uso

1. Execute `run.bat` para iniciar o sistema
2. Use a interface para:
   - Conectar uma câmera ( wip ) ou carregar um vídeo
   - Configurar email para alertas ( em settings )
   - Ajustar parâmetros de detecção
   - Visualizar detecções em tempo real
   - Receber alertas por email

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

- Python 3.8 ou superior
- Windows 10/11
- Câmera compatível ou arquivos de vídeo
- Conta Gmail para envio de alertas (ou outro servidor SMTP)

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
└── data/            # Dados de treinamento
```

## Alertas por Email

O sistema processa alertas por email através de um worker dedicado, garantindo que a interface permaneça responsiva. Cada email inclui:
- Timestamp da detecção
- Imagem do frame com a detecção
- Nível de confiança da detecção
- Tempo do vídeo
- Visualização gráfica da confiança

O processamento assíncrono garante que múltiplos alertas possam ser enviados sem impactar a performance do sistema.

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

## Suporte

Para problemas e sugestões, abra uma issue no repositório.