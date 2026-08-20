import cv2
import mediapipe as mp

mp_face = mp.solutions.face_detection

face_detection = mp_face.FaceDetection(
    model_selection=0,
    min_detection_confidence=0.5
)

def detect_face(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    results = face_detection.process(rgb_frame)

    if results.detections:
        return True

    return False