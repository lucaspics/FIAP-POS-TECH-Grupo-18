# VisionGuard - Detecção de Objetos Cortantes

## Arquitetura do Sistema

O sistema é dividido em três componentes principais:

### 1. Sistema de Treinamento (Training Pipeline)
- `training/`
  - `dataset_manager.py`: Gerenciamento e preparação do dataset
  - `model_trainer.py`: Treinamento do modelo YOLOv8
  - `model_evaluator.py`: Avaliação de performance do modelo
  - `config.py`: Configurações do treinamento

### 2. API de Detecção (Detection API)
- `api/`
  - `main.py`: Aplicação FastAPI
  - `detector.py`: Classe de detecção usando modelo treinado
  - `alert_manager.py`: Gerenciamento de alertas
  - `config.py`: Configurações da API

### 3. Frontend (Existente)
- `src/`
  - `main.py`: Interface PyQt5 existente
  - `assets/`: Recursos da interface

## Pipeline de Desenvolvimento

1. **Preparação do Dataset**
   - Coleta de imagens de objetos cortantes
   - Anotação do dataset
   - Augmentação de dados

2. **Treinamento do Modelo**
   - Utilização do YOLOv8 para detecção de objetos
   - Fine-tuning para objetos cortantes
   - Validação e ajustes

3. **Desenvolvimento da API**
   - Endpoints para processamento de frames
   - Sistema de cache para performance
   - Integração com sistema de alertas

4. **Integração**
   - Conexão do frontend com a API
   - Sistema de logs e monitoramento
   - Testes de performance

## Tecnologias Utilizadas

- **Machine Learning**: YOLOv8, PyTorch
- **Backend**: FastAPI, OpenCV
- **Frontend**: PyQt5
- **Ferramentas**: Docker, Redis (cache)

## Configuração do Ambiente

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```

3. Execute o sistema de treinamento:
```bash
python -m training.model_trainer
```

4. Inicie a API:
```bash
uvicorn api.main:app --reload
```

5. Execute o frontend:
```bash
python src/main.py