import cv2
import os
import urllib.request
import numpy as np
from datetime import datetime
from ultralytics import YOLO

# Load YOLOv8 model
model = YOLO("yolov8n.pt")

# Stream URL (Update with your camera IP or path)
url = 'http://192.168.211.99/cam-hi.jpg'

# File to store vehicle count for south direction
vehicle_count_file = "vehicle_count_south.txt"

# Create the vehicle count file if it doesn't exist
if os.path.exists(vehicle_count_file):
    os.remove(vehicle_count_file)

# List of vehicle classes that YOLOv8 detects
vehicle_classes = ['car', 'motorbike', 'bus', 'truck', 'bicycle']
ambulance_class = 'truck'  # Temporary detection workaround for ambulance
confidence_threshold = 0.5  # YOLO confidence threshold

# Function to log vehicle count and ambulance status
def log_vehicle_count(count, previous_count, ambulance_detected):
    if count != previous_count:
        with open(vehicle_count_file, 'w') as f:
            now = datetime.now()
            dtString = now.strftime('%H:%M:%S')
            ambulance_status = "ambulance true" if ambulance_detected else "ambulance false"
            f.write(f'Vehicle{count},{dtString} {ambulance_status}\n')

def main():
    previous_vehicle_count = 0
    ambulance_detected = False

    while True:
        try:
            img_resp = urllib.request.urlopen(url)
            imgnp = np.array(bytearray(img_resp.read()), dtype=np.uint8)
            frame = cv2.imdecode(imgnp, -1)

            if frame is None:
                continue

            results = model(frame, imgsz=640, verbose=False)[0]
            vehicle_count = 0
            ambulance_detected = False

            for box in results.boxes:
                if box.conf > confidence_threshold:
                    cls_id = int(box.cls)
                    label = model.names[cls_id]

                    if label in vehicle_classes:
                        vehicle_count += 1
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                    if label == ambulance_class and box.conf > confidence_threshold:
                        ambulance_detected = True
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, "Ambulance", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Log vehicle count and ambulance status
            log_vehicle_count(vehicle_count, previous_vehicle_count, ambulance_detected)
            previous_vehicle_count = vehicle_count

            # Display vehicle count on the frame
            cv2.putText(frame, f"Vehicles (South): {vehicle_count}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            if ambulance_detected:
                cv2.putText(frame, "Ambulance Detected!", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Show the frame
            cv2.imshow('South Road Vehicle Detection', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except Exception as e:
            print(f"Error: {e}")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
