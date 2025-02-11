# Plano de Limpeza e Reorganização do Projeto VisionGuard

## 1. Arquivos e Pastas a Serem Removidos

### Pastas Redundantes
- `src/logs/` (duplicada da pasta raiz `logs/`)
- `src/data/` (duplicada da pasta raiz `data/`)
- `src/models/` (duplicada da pasta raiz `models/`)
- `src/assets/` (sem uso atual)
- `src/api/` (será removida conforme plano de refatoração)

### Arquivos Obsoletos
- Todos os arquivos dentro de `src/api/`
- `src/run.py` (funcionalidade movida para main.py)

## 2. Nova Estrutura de Diretórios

```
visionguard/
├── data/                    # Dados de treinamento e validação
│   ├── train/
│   ├── valid/
│   └── data.yaml
├── docs/                    # Documentação do projeto
│   ├── technical/          # Documentação técnica
│   └── user/               # Documentação do usuário
├── logs/                    # Logs centralizados
│   ├── alerts/
│   ├── errors/
│   ├── frames/
│   ├── metrics/
│   └── results/
├── models/                  # Modelos treinados
│   ├── best.pt
│   └── backups/
├── src/                    # Código fonte
│   ├── config/            # Configurações
│   ├── core/             # Lógica principal
│   ├── ui/               # Interface gráfica
│   ├── utils/            # Utilitários
│   └── workers/          # Workers assíncronos
├── tests/                 # Testes automatizados
└── tools/                 # Scripts de utilidade
```

## 3. Ações de Limpeza

### 3.1 Consolidação de Configurações
- Mover todas as configurações para `src/config/`
- Unificar arquivos de configuração relacionados
- Criar arquivo de configuração padrão

### 3.2 Organização de Logs
- Centralizar todos os logs na pasta raiz `logs/`
- Implementar rotação de logs
- Definir política de retenção

### 3.3 Documentação
- Mover todos os arquivos .md para `docs/`
- Converter documentos .docx para markdown
- Organizar por categoria (técnica/usuário)

### 3.4 Scripts de Utilidade
- Renomear pasta `utils/` para `tools/`
- Consolidar scripts de setup e treinamento
- Documentar uso de cada script

## 4. Sequência de Implementação

1. **Backup**
   - Criar backup completo do projeto
   - Documentar estado atual

2. **Limpeza Inicial**
   - Remover pastas redundantes
   - Deletar arquivos obsoletos
   - Consolidar logs

3. **Reorganização**
   - Criar nova estrutura de diretórios
   - Mover arquivos para novas localizações
   - Atualizar imports e referências

4. **Documentação**
   - Atualizar documentação existente
   - Criar documentação faltante
   - Validar links e referências

5. **Testes**
   - Verificar funcionalidades principais
   - Validar logs e configurações
   - Testar scripts de utilidade

## 5. Impacto no Desenvolvimento

### Benefícios
- Estrutura mais clara e organizada
- Menor redundância
- Manutenção simplificada
- Documentação centralizada

### Pontos de Atenção
- Atualizar documentação de desenvolvimento
- Comunicar mudanças à equipe
- Verificar impacto em scripts de build
- Atualizar caminhos em arquivos de configuração

## 6. Validação

1. **Verificações Funcionais**
   - Inicialização do sistema
   - Detecção de objetos
   - Sistema de alertas
   - Interface gráfica

2. **Verificações Técnicas**
   - Logs funcionando corretamente
   - Configurações carregando
   - Scripts de utilidade executando
   - Backups e recuperação

## 7. Próximos Passos

1. Revisão do plano pela equipe
2. Aprovação das mudanças
3. Implementação por fases
4. Validação contínua
5. Atualização da documentação