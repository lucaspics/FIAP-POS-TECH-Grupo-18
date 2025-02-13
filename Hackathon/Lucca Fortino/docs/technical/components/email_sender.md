# Sistema de Email (src/core/email_sender.py)

## Visão Geral
Sistema assíncrono de envio de emails com worker dedicado, otimizado para processamento em background e gerenciamento eficiente de notificações.

## Arquitetura

### EmailWorker
Worker dedicado que processa emails em uma thread separada.

```python
class EmailWorker:
    def __init__(self, smtp_config: Dict)
    def start(self)
    def stop(self)
```

#### Características
- Thread dedicada para processamento
- Fila assíncrona de mensagens
- Gerenciamento automático de recursos
- Reconexão automática

### EmailSender
Gerenciador principal de envio de emails.

```python
class EmailSender(QObject):
    def __init__(self, smtp_server: str, smtp_port: int, 
                 sender_email: Optional[str], sender_password: Optional[str])
```

## Funcionalidades Principais

### 1. Processamento Assíncrono
- Worker dedicado em thread separada
- Fila de mensagens não-bloqueante
- Throttling automático
- Gestão de recursos

### 2. Sistema de Templates
```html
<h2 style="color: #f44336;">⚠️ Alerta de Detecção</h2>
<div style="margin: 20px 0; padding: 10px;">
    <p><strong>Timestamp:</strong> {timestamp}</p>
    <p><strong>Detecções:</strong> {detections}</p>
</div>
```

### 3. Gestão de Anexos
- Processamento otimizado de imagens
- Compressão automática
- Validação de formatos
- Limite de tamanho

## Pipeline de Envio

### 1. Preparação
```python
msg = MIMEMultipart()
msg['Subject'] = ALERT_CONFIG['alert_subject']
msg['From'] = sender_email
msg['To'] = recipient_email
```

### 2. Processamento de Imagens
- Conversão para JPEG
- Redimensionamento se necessário
- Otimização de qualidade
- Anexos inline

### 3. Envio
- Conexão SMTP segura
- Retry automático
- Validação de envio
- Logging de status

## Otimizações

### Performance
- Queue assíncrona
- Processamento em batch quando possível
- Cache de conexões SMTP
- Gerenciamento de memória

### Confiabilidade
- Reconexão automática
- Validação de emails
- Tratamento de erros
- Sistema de retry

## Configurações

### SMTP
```python
smtp_config = {
    'server': 'smtp.gmail.com',
    'port': 587,
    'email': sender_email,
    'password': sender_password
}
```

### Alertas
```python
ALERT_CONFIG = {
    'alert_subject': str,
    'alert_template': str,
    'enable_email_alerts': bool,
    'notification_email': str
}
```

## Integração com Sistema

### Entrada
- Detecções do AlertManager
- Frames de vídeo
- Configurações de alerta
- Dados de timestamp

### Saída
- Status de envio
- Logs de erro
- Métricas de performance
- Confirmações de entrega

## Recursos de Segurança

### Autenticação
- TLS/SSL para SMTP
- Validação de credenciais
- Proteção de senha
- Timeout configurável

### Validação
```python
pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
return bool(re.match(pattern, email))
```

## Monitoramento

### Métricas
- Taxa de envio
- Erros de envio
- Tempo de processamento
- Tamanho da fila

### Logs
- Status de envio
- Erros detalhados
- Performance
- Conexões SMTP

## Considerações de Uso

### Inicialização
- Configurar credenciais SMTP
- Validar conexão
- Iniciar worker
- Verificar templates

### Manutenção
- Monitorar fila
- Verificar logs
- Gerenciar conexões
- Atualizar templates

## Dependências
- smtplib
- email.mime
- asyncio
- PyQt5 (QObject)
- OpenCV (processamento de imagens)

## Boas Práticas
- Sempre usar TLS/SSL
- Implementar retry
- Monitorar erros
- Limitar tamanho de anexos
- Validar emails antes do envio