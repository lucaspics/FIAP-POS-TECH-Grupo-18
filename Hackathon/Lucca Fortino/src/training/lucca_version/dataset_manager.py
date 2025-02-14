import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict
import yaml
from tqdm import tqdm

class DatasetManager:
    def __init__(self, base_path: str):
        """
        Inicializa o gerenciador de dataset.
        
        Args:
            base_path: Caminho base para o dataset
        """
        self.base_path = Path(base_path)
        self.images_path = self.base_path / "images"
        self.labels_path = self.base_path / "labels"
        self.classes = ["knife", "scissors", "blade"]
        
        # Criar diretórios necessários
        self.images_path.mkdir(parents=True, exist_ok=True)
        self.labels_path.mkdir(parents=True, exist_ok=True)
        
        # Criar estrutura para treino/validação
        for split in ["train", "val"]:
            (self.images_path / split).mkdir(exist_ok=True)
            (self.labels_path / split).mkdir(exist_ok=True)

    def prepare_dataset(self, source_images: List[str], annotations: List[Dict]):
        """
        Prepara o dataset para treinamento.
        
        Args:
            source_images: Lista de caminhos para imagens fonte
            annotations: Lista de anotações no formato YOLO
        """
        print("Preparando dataset...")
        
        # Split treino/validação (80/20)
        num_samples = len(source_images)
        num_train = int(0.8 * num_samples)
        
        indices = np.random.permutation(num_samples)
        train_indices = indices[:num_train]
        val_indices = indices[num_train:]
        
        # Processar imagens e anotações
        for idx in tqdm(range(num_samples), desc="Processando imagens"):
            img_path = source_images[idx]
            ann = annotations[idx]
            
            # Determinar split
            split = "train" if idx in train_indices else "val"
            
            # Copiar e processar imagem
            img = cv2.imread(img_path)
            if img is None:
                print(f"Erro ao ler imagem: {img_path}")
                continue
                
            # Salvar imagem processada
            new_img_path = self.images_path / split / f"img_{idx}.jpg"
            cv2.imwrite(str(new_img_path), img)
            
            # Salvar anotação
            label_path = self.labels_path / split / f"img_{idx}.txt"
            self._save_yolo_annotation(label_path, ann)

    def create_data_yaml(self):
        """
        Cria o arquivo data.yaml necessário para treinamento YOLOv8.
        """
        data = {
            "path": str(self.base_path),
            "train": str(self.images_path / "train"),
            "val": str(self.images_path / "val"),
            "names": {i: name for i, name in enumerate(self.classes)}
        }
        
        yaml_path = self.base_path / "data.yaml"
        with open(yaml_path, "w") as f:
            yaml.dump(data, f)
            
        return str(yaml_path)

    def _save_yolo_annotation(self, path: Path, annotation: Dict):
        """
        Salva anotação no formato YOLO.
        
        Args:
            path: Caminho para salvar a anotação
            annotation: Dicionário com anotações
        """
        with open(path, "w") as f:
            for obj in annotation["objects"]:
                class_id = self.classes.index(obj["class"])
                x, y, w, h = obj["bbox"]  # Formato YOLO: <class> <x> <y> <width> <height>
                f.write(f"{class_id} {x} {y} {w} {h}\n")

    def augment_data(self):
        """
        Realiza data augmentation no dataset de treino.
        """
        train_images = list((self.images_path / "train").glob("*.jpg"))
        
        for img_path in tqdm(train_images, desc="Augmentando dataset"):
            img = cv2.imread(str(img_path))
            if img is None:
                continue
                
            # Augmentations básicas
            augmentations = [
                self._horizontal_flip,
                self._adjust_brightness,
                self._add_noise,
                self._rotate
            ]
            
            for i, aug_func in enumerate(augmentations):
                aug_img = aug_func(img.copy())
                
                # Salvar imagem aumentada
                new_path = img_path.parent / f"{img_path.stem}_aug{i}{img_path.suffix}"
                cv2.imwrite(str(new_path), aug_img)
                
                # Copiar anotação correspondente
                label_path = self.labels_path / "train" / f"{img_path.stem}.txt"
                new_label_path = self.labels_path / "train" / f"{img_path.stem}_aug{i}.txt"
                
                if label_path.exists():
                    with open(label_path, "r") as f_src, open(new_label_path, "w") as f_dst:
                        f_dst.write(f_src.read())

    def _horizontal_flip(self, image: np.ndarray) -> np.ndarray:
        """Flip horizontal."""
        return cv2.flip(image, 1)

    def _adjust_brightness(self, image: np.ndarray) -> np.ndarray:
        """Ajusta brilho aleatoriamente."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        value = np.random.uniform(0.8, 1.2)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * value, 0, 255)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def _add_noise(self, image: np.ndarray) -> np.ndarray:
        """Adiciona ruído gaussiano."""
        noise = np.random.normal(0, 10, image.shape)
        noisy_img = np.clip(image + noise, 0, 255).astype(np.uint8)
        return noisy_img

    def _rotate(self, image: np.ndarray) -> np.ndarray:
        """Rotação aleatória entre -15 e 15 graus."""
        angle = np.random.uniform(-15, 15)
        height, width = image.shape[:2]
        matrix = cv2.getRotationMatrix2D((width/2, height/2), angle, 1.0)
        return cv2.warpAffine(image, matrix, (width, height))