#!/usr/bin/env python
from ultralytics import YOLO
import os
from pathlib import Path
import yaml
import logging
from datetime import datetime
from typing import Optional, Dict
import shutil

class ModelTrainer:
    def __init__(self, config_path: str):
        """
        Inicializa o treinador do modelo.
        
        Args:
            config_path: Caminho para o arquivo de configuração YAML
        """
        self.config_path = Path(config_path)
        self.setup_logging()
        
        # Carregar configuração
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
            
        # Configurar caminhos
        self.model_dir = Path(self.config.get("model_dir", "models"))
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_logging(self):
        """Configura logging para o treinamento."""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"training_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)

    def find_latest_checkpoint(self, run_name: str) -> Optional[str]:
        """
        Encontra o checkpoint mais recente de um treinamento.
        
        Args:
            run_name: Nome do diretório de treinamento
            
        Returns:
            Caminho para o último checkpoint ou None se não encontrado
        """
        checkpoint_dir = self.model_dir / run_name / "weights"
        if not checkpoint_dir.exists():
            return None
            
        checkpoints = list(checkpoint_dir.glob("epoch*.pt"))
        if not checkpoints:
            return None
            
        # Ordenar por número da época
        latest = max(checkpoints, key=lambda x: int(x.stem.replace("epoch", "")))
        return str(latest)

    def backup_checkpoint(self, checkpoint_path: str, run_name: str):
        """
        Cria um backup do checkpoint.
        
        Args:
            checkpoint_path: Caminho para o checkpoint
            run_name: Nome do diretório de treinamento
        """
        backup_dir = self.model_dir / run_name / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        checkpoint_file = Path(checkpoint_path)
        backup_path = backup_dir / f"{checkpoint_file.name}.backup"
        
        shutil.copy2(checkpoint_path, backup_path)
        self.logger.info(f"Backup do checkpoint criado: {backup_path}")

    def train(self, data_yaml_path: str, pretrained_weights: Optional[str] = None, resume: bool = True) -> str:
        """
        Treina o modelo YOLOv8.
        
        Args:
            data_yaml_path: Caminho para o arquivo data.yaml
            pretrained_weights: Caminho opcional para pesos pré-treinados
            resume: Se deve tentar retomar treinamento anterior
            
        Returns:
            Caminho para o modelo treinado
        """
        self.logger.info("Iniciando treinamento do modelo...")
        
        try:
            # Definir nome do treinamento
            run_name = f"train_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Verificar checkpoints anteriores
            if resume:
                latest_checkpoint = self.find_latest_checkpoint(run_name)
                if latest_checkpoint:
                    self.logger.info(f"Encontrado checkpoint anterior: {latest_checkpoint}")
                    self.logger.info("Retomando treinamento a partir do checkpoint...")
                    pretrained_weights = latest_checkpoint
            
            # Carregar modelo
            if pretrained_weights:
                model = YOLO(pretrained_weights)
                self.logger.info(f"Carregado modelo: {pretrained_weights}")
            else:
                model = YOLO("yolov8n.pt")  # Usar modelo nano como base
                self.logger.info("Carregado modelo YOLOv8n base")
            
            # Configurar parâmetros de treinamento
            train_args = {
                "data": data_yaml_path,
                "epochs": self.config.get("epochs", 100),
                "imgsz": self.config.get("image_size", 640),
                "batch": self.config.get("batch_size", 16),
                "device": self.config.get("device", "cpu"),
                "workers": self.config.get("num_workers", 8),
                "patience": self.config.get("patience", 50),
                "project": str(self.model_dir),
                "name": run_name,
                "exist_ok": True,
                "pretrained": True,
                "optimizer": self.config.get("optimizer", "SGD"),
                "lr0": self.config.get("learning_rate", 0.01),
                "weight_decay": self.config.get("weight_decay", 0.0005),
                "warmup_epochs": self.config.get("warmup_epochs", 3),
                "close_mosaic": self.config.get("close_mosaic", 10),
                "box": self.config.get("box_loss_weight", 7.5),
                "cls": self.config.get("cls_loss_weight", 0.5),
                "dfl": self.config.get("dfl_loss_weight", 1.5),
                "plots": True,
                "save": True,
                "save_period": self.config.get("save_period", 10),  # Salvar a cada N épocas
                "cache": self.config.get("cache", True)
            }
            
            # Iniciar treinamento
            self.logger.info("Configurações de treinamento:")
            for k, v in train_args.items():
                self.logger.info(f"{k}: {v}")
                
            results = model.train(**train_args)
            
            # Salvar métricas finais
            try:
                metrics = self._extract_metrics(results)
                self._save_metrics(metrics, run_name)
            except Exception as e:
                self.logger.error(f"Erro ao extrair métricas: {str(e)}")
                self.logger.error("Continuando com o salvamento do modelo...")
            
            best_model_path = self.model_dir / run_name / "weights" / "best.pt"
            
            # Criar backup do melhor modelo
            if best_model_path.exists():
                self.backup_checkpoint(str(best_model_path), run_name)
            
            self.logger.info(f"Treinamento concluído. Melhor modelo salvo em: {best_model_path}")
            
            return str(best_model_path)
            
        except Exception as e:
            self.logger.error(f"Erro durante treinamento: {str(e)}")
            raise

    def _extract_metrics(self, results) -> Dict:
        """
        Extrai métricas relevantes dos resultados do treinamento.
        """
        try:
            metrics = {}
            
            # Tentar extrair métricas básicas
            if hasattr(results, 'results_dict'):
                metrics['precision'] = float(results.results_dict.get("metrics/precision(B)", 0))
                metrics['recall'] = float(results.results_dict.get("metrics/recall(B)", 0))
                metrics['f1-score'] = float(results.results_dict.get("metrics/F1(B)", 0))
            
            # Tentar extrair mAP
            if hasattr(results, 'maps'):
                if len(results.maps) > 0:
                    metrics['mAP50'] = float(results.maps[0])
                if len(results.maps) > 1:
                    metrics['mAP50-95'] = float(results.maps[1])
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Erro ao extrair métricas: {str(e)}")
            return {
                'error': 'Falha ao extrair métricas',
                'details': str(e)
            }

    def _save_metrics(self, metrics: Dict, run_name: str):
        """
        Salva métricas em arquivo YAML.
        """
        try:
            metrics_dir = self.model_dir / run_name / "metrics"
            metrics_dir.mkdir(exist_ok=True)
            
            metrics_file = metrics_dir / "metrics.yaml"
            with open(metrics_file, "w") as f:
                yaml.dump(metrics, f)
                
            self.logger.info(f"Métricas salvas em: {metrics_file}")
            self.logger.info("Métricas finais:")
            for k, v in metrics.items():
                if isinstance(v, float):
                    self.logger.info(f"{k}: {v:.4f}")
                else:
                    self.logger.info(f"{k}: {v}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar métricas: {str(e)}")

if __name__ == "__main__":
    # Exemplo de uso
    config_path = "config/training_config.yaml"
    data_yaml_path = "data/data.yaml"
    
    trainer = ModelTrainer(config_path)
    best_model = trainer.train(data_yaml_path)
    print(f"Melhor modelo salvo em: {best_model}")