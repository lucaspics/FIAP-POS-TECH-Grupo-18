import os
from pathlib import Path
import logging
import yaml
import sys
import traceback
from datetime import datetime
import torch  # Importar torch para configuração de device
from training.model_trainer import ModelTrainer

# Forçar uso de CPU
os.environ['CUDA_VISIBLE_DEVICES'] = ''
if hasattr(torch, 'cuda'):
    torch.cuda.is_available = lambda: False

# Criar diretório de logs se não existir
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configurar logging para arquivo e console
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"training_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def log_system_info():
    """Registra informações do sistema."""
    try:
        import platform
        
        logger.info("=== Informações do Sistema ===")
        logger.info(f"Sistema Operacional: {platform.system()} {platform.release()}")
        logger.info(f"Python Version: {sys.version}")
        logger.info(f"PyTorch Version: {torch.__version__}")
        logger.info(f"Device: CPU (CUDA desativado)")
        logger.info("===========================")
    except Exception as e:
        logger.error(f"Erro ao coletar informações do sistema: {str(e)}")

def log_dataset_info():
    """Registra informações do dataset."""
    try:
        logger.info("=== Informações do Dataset ===")
        
        # Verificar data.yaml
        data_yaml_path = Path("data/data.yaml")
        if data_yaml_path.exists():
            with open(data_yaml_path, "r") as f:
                data_config = yaml.safe_load(f)
                logger.info(f"Configuração do Dataset:")
                logger.info(f"Classes: {data_config.get('names', [])}")
                logger.info(f"Número de Classes: {data_config.get('nc', 0)}")
        
        # Contar imagens
        train_dir = Path("data/train/images")
        valid_dir = Path("data/valid/images")
        
        train_images = list(train_dir.glob("*.jpg")) if train_dir.exists() else []
        valid_images = list(valid_dir.glob("*.jpg")) if valid_dir.exists() else []
        
        logger.info(f"Imagens de Treino: {len(train_images)}")
        logger.info(f"Imagens de Validação: {len(valid_images)}")
        
        # Verificar labels
        train_labels = Path("data/train/labels")
        valid_labels = Path("data/valid/labels")
        
        train_labels_files = list(train_labels.glob("*.txt")) if train_labels.exists() else []
        valid_labels_files = list(valid_labels.glob("*.txt")) if valid_labels.exists() else []
        
        logger.info(f"Anotações de Treino: {len(train_labels_files)}")
        logger.info(f"Anotações de Validação: {len(valid_labels_files)}")
        logger.info("===========================")
        
    except Exception as e:
        logger.error(f"Erro ao coletar informações do dataset: {str(e)}")

def train_model():
    """
    Script para treinar o modelo YOLOv8 para detecção de facas.
    """
    try:
        print("""
╔══════════════════════════════════════╗
║       VisionGuard - Treinamento      ║
║         Detecção de Facas           ║
╚══════════════════════════════════════╝
        """)
        
        logger.info("Iniciando processo de treinamento...")
        logger.info("Modo de execução: CPU")
        
        # Registrar informações do sistema
        log_system_info()
        
        # Registrar informações do dataset
        log_dataset_info()

        # Verificar estrutura do dataset
        data_yaml_path = Path("data/data.yaml")
        if not data_yaml_path.exists():
            logger.error("Arquivo data.yaml não encontrado!")
            return

        # Carregar e validar data.yaml
        with open(data_yaml_path, "r") as f:
            data_config = yaml.safe_load(f)
            logger.info("Configuração do data.yaml:")
            logger.info(f"Train path: {data_config.get('train', '')}")
            logger.info(f"Val path: {data_config.get('val', '')}")
            logger.info(f"Classes: {data_config.get('names', [])}")

        # Verificar diretórios do dataset
        train_dir = Path("data/train/images")
        valid_dir = Path("data/valid/images")
        
        if not train_dir.exists() or not valid_dir.exists():
            logger.error("""
Estrutura de diretórios incorreta!
Esperado:
data/
  ├── train/
  │   ├── images/
  │   └── labels/
  ├── valid/
  │   ├── images/
  │   └── labels/
  └── data.yaml
            """)
            return

        # Verificar se há imagens
        train_images = list(train_dir.glob("*.jpg"))
        valid_images = list(valid_dir.glob("*.jpg"))

        logger.info(f"Encontradas {len(train_images)} imagens de treino")
        logger.info(f"Encontradas {len(valid_images)} imagens de validação")

        if len(train_images) == 0 or len(valid_images) == 0:
            logger.error("Nenhuma imagem encontrada!")
            return

        # Aplicar data augmentation
        from training.dataset_manager import DatasetManager
        dataset_manager = DatasetManager(str(Path("data")))
        logger.info("Iniciando data augmentation...")
        dataset_manager.augment_data()
        logger.info("Data augmentation concluído")

        # Atualizar caminhos no data.yaml para serem absolutos
        data_config['train'] = str(train_dir.absolute())
        data_config['val'] = str(valid_dir.absolute())
        
        # Salvar configuração atualizada
        temp_yaml = Path("data/temp_data.yaml")
        with open(temp_yaml, "w") as f:
            yaml.dump(data_config, f)
            logger.info("Arquivo de configuração temporário criado com sucesso")

        # Usar configuração de teste ou normal baseado no argumento
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--test', action='store_true', help='Usar configuração de teste rápido')
        args = parser.parse_args()
        
        config_path = "src/training/config/training_config_test.yaml" if args.test else "src/training/config/training_config.yaml"
        logger.info(f"Usando configuração: {config_path}")
        
        # Verificar se existe treinamento anterior
        trainer = ModelTrainer(config_path)
        run_dir = Path("models")
        previous_runs = [d for d in run_dir.glob("train_*") if d.is_dir()]
        
        if previous_runs:
            # Filtrar apenas diretórios que seguem o padrão correto
            valid_runs = []
            for run in previous_runs:
                try:
                    # Tentar extrair a data do nome do diretório
                    run_date = run.name.split('_')[1:]  # Pegar todos os elementos após 'train_'
                    if len(run_date) >= 1:
                        datetime.strptime('_'.join(run_date), '%Y%m%d_%H%M%S')
                        valid_runs.append(run)
                except (ValueError, IndexError):
                    continue
            
            if valid_runs:
                latest_run = max(valid_runs, key=lambda x: datetime.strptime('_'.join(x.name.split('_')[1:]), '%Y%m%d_%H%M%S'))
                logger.info(f"Encontrado treinamento anterior: {latest_run}")
            logger.info(f"Encontrado treinamento anterior: {latest_run}")
            
            # Perguntar se deseja continuar
            response = input("Deseja continuar o treinamento anterior? (s/n): ").lower()
            resume = response == 's'
        else:
            resume = False
            logger.info("Nenhum treinamento anterior encontrado. Iniciando novo treinamento...")

        # Iniciar treinamento
        logger.info("Iniciando treinamento do modelo (CPU)...")
        best_model = trainer.train(str(temp_yaml), resume=resume)

        # Limpar arquivo temporário
        temp_yaml.unlink()

        logger.info(f"""
Treinamento concluído com sucesso!
Modelo salvo em: {best_model}

Para usar o modelo:
1. Copie o modelo para a pasta 'models/'
2. Renomeie para 'best.pt'
3. Execute o sistema: .\\run.bat
        """)

    except Exception as e:
        logger.error("Erro durante o treinamento:")
        logger.error(str(e))
        logger.error("Traceback completo:")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    train_model()