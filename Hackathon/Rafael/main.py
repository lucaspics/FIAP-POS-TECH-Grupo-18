import argparse
from scripts.detector import Detector
from config import EMAIL_CONFIG

def main():
    parser = argparse.ArgumentParser(description="FIAP VisionGuard - Detecção de Objetos Cortantes")
    parser.add_argument('--source', type=str, required=True, help="Fonte: 'webcam' ou caminho do vídeo")
    args = parser.parse_args()

    #detector = Detector(model_path="models/sharp-detection/weights/best.pt", email_config=EMAIL_CONFIG)
    detector = Detector(model_path="scripts/models/cortante2/weights/best.pt", email_config=EMAIL_CONFIG)
    detector.run(source=args.source)

if __name__ == "__main__":
    main()


#verificar video
#python main.py --source videos/video.mp4
#python main.py --source videos/video2.mp4

#verificar Webcam
#python main.py --source webcam