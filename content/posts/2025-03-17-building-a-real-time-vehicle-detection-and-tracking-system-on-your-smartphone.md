---
author: Gunn Kim
date: '2025-03-16T19:07:00.000Z'
description: Step-by-step guide to building a real-time vehicle detection and tracking
  system on your smartphone using YOLOv8 and DeepSORT. Ideal for beginners and enthusiasts
  in computer vision.
draft: true
lastmod: '2025-03-16T19:07:00.000Z'
notion_id: 1b87522e-eb2f-8116-baa7-f3c4f8af499e
subtitle: Step-by-Step Guide to Detecting and Tracking Vehicles Using YOLOv8 and DeepSORT
summary: Step-by-step guide to building a real-time vehicle detection and tracking
  system on your smartphone using YOLOv8 and DeepSORT. Ideal for beginners and enthusiasts
  in computer vision.
title: Building a Real-Time Vehicle Detection and Tracking System on Your Smartphone
---

### 

**Introduction**
Welcome back! In the first part, we discussed the basics of speed measurement and the technologies involved. Now, we will move on to the practical implementation of detecting and tracking vehicles using YOLOv8 and DeepSORT.

---

**1. Installing and Setting Up YOLOv8**
First, you need to install the YOLOv8 model. YOLOv8 can be installed via the Ultralytics library.

```python
from ultralytics import YOLO

# Load a pre-trained YOLOv8 model
model = YOLO('yolov8n.pt')

```

**2. Capturing Video from Your Smartphone**
You can use OpenCV to capture video from your smartphone’s camera.

```python
import cv2

# Capture video from the smartphone camera
cap = cv2.VideoCapture(0)  # 0 for default camera

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Process the frame
    results = model.predict(source=frame)
    # Further processing...

```

**3. Implementing Object Tracking with DeepSORT**
DeepSORT helps in maintaining the identity of vehicles across multiple frames. Here’s how you can integrate it:

```python
from deep_sort_pytorch.deep_sort import DeepSort

# Initialize DeepSORT
deepsort = DeepSort('deep_sort_pytorch/deep/checkpoint/ckpt.t7')

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model.predict(source=frame)
    bboxes = extract_bboxes(results)  # Custom function to extract bounding boxes

    # Update tracker
    outputs = deepsort.update(bboxes)
    for output in outputs:
        bbox = output[:4]
        track_id = output[4]
        # Draw bounding box and track ID on frame

```

**4. Displaying the Results**
Use OpenCV to display the video with detected and tracked vehicles.

```python
    for output in outputs:
        bbox = output[:4]
        track_id = output[4]

        # Draw bounding box and track ID on frame
        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
        cv2.putText(frame, f'ID: {track_id}', (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    cv2.imshow('Frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

```

**Conclusion**
In this part, we implemented the basics of vehicle detection and tracking using YOLOv8 and DeepSORT. In the final part, we will focus on calculating the speed of the detected vehicles and integrating GPS data for more accurate measurements.

---

