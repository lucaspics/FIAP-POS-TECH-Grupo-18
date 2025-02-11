# Plano de Implementação da Limpeza do Projeto VisionGuard

## Fase 1: Preparação e Backup

1. Criar backup do projeto
```bash
# Criar pasta de backup com timestamp
mkdir backup_$(date +%Y%m%d_%H%M%S)
# Copiar todos os arquivos
cp -r * backup_$(date +%Y%m%d_%H%M%S)/
```

## Fase 2: Remoção de Código Obsoleto

### 2.1 Remover Pastas Redundantes
- [ ] src/logs/
- [ ] src/data/
- [ ] src/models/
- [ ] src/assets/
- [ ] src/api/

### 2.2 Remover Arquivos Obsoletos
- [ ] src/run.py
- [ ] Todos os arquivos em src/api/

## Fase 3: Reorganização de Diretórios

### 3.1 Criar Nova Estrutura
```bash
mkdir -p docs/technical docs/user
mkdir -p tests
mkdir -p tools
```

### 3.2 Mover Arquivos
- [ ] Mover documentação para docs/
  - how_works.md → docs/technical/
  - *.md → docs/technical/
  - *.docx → docs/user/

- [ ] Consolidar scripts de utilidade
  - utils/* → tools/
  - Renomear scripts para nomes mais descritivos

## Fase 4: Atualização de Configurações

### 4.1 Modificar app_config.py
```python
# Remover constantes legadas
- VIDEO_WIDTH
- VIDEO_HEIGHT
- OVERLAY_PATH
- DEFAULT_EMAIL
- DEFAULT_ANALYSIS_INTERVAL
- FRAME_INTERVAL
- MIN_TIME_BETWEEN_ALERTS

# Atualizar caminhos base
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TOOLS_DIR = BASE_DIR / 'tools'
DOCS_DIR = BASE_DIR / 'docs'
```

### 4.2 Atualizar Referências
- [ ] Verificar e atualizar imports em todos os arquivos
- [ ] Atualizar caminhos nos scripts de utilidade
- [ ] Verificar referências nos arquivos de configuração

## Fase 5: Limpeza de Logs

### 5.1 Consolidar Sistema de Logs
- [ ] Mover todos os logs para pasta raiz logs/
- [ ] Implementar rotação de logs
- [ ] Definir política de retenção

### 5.2 Atualizar logging_config.py
```python
# Adicionar configuração de rotação
LOGGING_CONFIG = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    }
}
```

## Fase 6: Testes e Validação

### 6.1 Verificações Funcionais
- [ ] Inicialização do sistema
- [ ] Detecção de objetos
- [ ] Sistema de alertas
- [ ] Interface gráfica

### 6.2 Verificações Técnicas
- [ ] Logs sendo gerados corretamente
- [ ] Configurações carregando sem erros
- [ ] Scripts de utilidade funcionando
- [ ] Sistema de backup operacional

## Fase 7: Documentação Final

### 7.1 Atualizar Documentação
- [ ] README.md principal
- [ ] Documentação técnica
- [ ] Guia de desenvolvimento
- [ ] Documentação de configuração

### 7.2 Criar Novos Documentos
- [ ] Guia de manutenção
- [ ] Política de logs
- [ ] Procedimentos de backup

## Comandos de Verificação

### Verificar Arquivos Não Utilizados
```bash
# Listar arquivos não referenciados
find . -type f -not -path "*/\.*" -not -path "*/backup*" -print0 | 
while IFS= read -r -d '' file; do
    grep -r "$(basename "$file")" . > /dev/null || echo "$file"
done
```

### Verificar Imports Quebrados
```python
# Script de verificação
import py_compile
import os

def check_imports():
    for root, _, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                try:
                    py_compile.compile(os.path.join(root, file))
                except:
                    print(f"Erro em: {os.path.join(root, file)}")
```

## Rollback Plan

### Em Caso de Problemas
1. Parar todos os serviços
2. Restaurar backup
3. Verificar permissões
4. Reiniciar serviços
5. Validar funcionamento

### Comandos de Rollback
```bash
# Restaurar do backup
cp -r backup_[timestamp]/* .

# Verificar permissões
chmod -R 755 tools/
chmod -R 644 docs/
```

## Checklist Final

- [ ] Todos os arquivos obsoletos removidos
- [ ] Nova estrutura de diretórios implementada
- [ ] Configurações atualizadas
- [ ] Logs consolidados
- [ ] Testes passando
- [ ] Documentação atualizada
- [ ] Backup final realizado
- [ ] Equipe notificada das mudanças