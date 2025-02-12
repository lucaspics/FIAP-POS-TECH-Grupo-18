from ultralytics import YOLO
import cv2
import time
import requests
from Utils.database import insert_incident
from Utils.sendEmail import send_email

# Load the YOLOv8 model
model = YOLO('database/yolov8n.pt')  # Replace with your trained model if necessary

sharp_objects = [
    "knife",
    "razor",
    "scissors",
    "box cutter",
    "scalpel",
    "machete",
    "axe",
    "chisel",
    "saw",
    "glass shard",
    "blade",
    "shears",
    "cleaver",
    "hacksaw",
    "pruning shears",
    "scythe",
    "letter opener",
    "ice pick"
]

# Function to choose between webcam and video
def input_choose():
    print("Choose video input:")
    print("1 - Webcam")
    print("2 - Video1")
    print("3 - Video2")
    choose = input("Enter the number corresponding to your choice: ")
    
    if choose == '1':
        return 'webcam'
    elif choose == '2':
        return 'video1'
    elif choose == '3':
        return 'video2'
    else:
        print("Invalid choice. Using webcam by default.")
        return 'webcam'

# Choose the input
input_data = input_choose()

if input_data == 'webcam':
    # Open the webcam
    cap = cv2.VideoCapture(0)
elif input_data == 'video1':
    # Path to the video
    video_path = 'videos/video.mp4'
    cap = cv2.VideoCapture(video_path)
elif input_data == 'video2':
    # Path to the video
    video_path = 'videos/video2.mp4'
    cap = cv2.VideoCapture(video_path)

# Check if the webcam was opened successfully
if not cap.isOpened():
    print("Error opening webcam")
    exit()

# Loop to process each frame from the webcam
while True:
    # Capture frame by frame
    ret, frame = cap.read()

    # Check if the frame was captured successfully
    if not ret:
        print("Error capturing frame")
        break

    # Perform object detection with YOLOv8
    results = model(frame)

    # Check if a knife was detected
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls)  # Detected class ID
            class_name = model.names[class_id]  # Class name

            # Check if the detected class is "knife"
            if class_name in sharp_objects:

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # Draw the bounding box on the frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Add the class name above the box
                cv2.putText(frame, class_name, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                image_name = str(time.time()) + '.jpg'
                image_path = 'static/screenshots/' + image_name
                message = 'Sharp object detected'
                subject = 'Alert: Knife Detected'
                cv2.imwrite(image_path, frame)
                print("Sharp object detected. Sending email...")
                insert_incident(image_name, message)
                requests.get('http://localhost:5000/update')
                send_email("fabiohan.defcon4@gmail.com", subject, message, image_path)
                time.sleep(10)  # Avoid multiple emails

    # Display the frame with detections
    cv2.imshow('YOLOv8 - Object Detection', frame)

    # Stop the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()