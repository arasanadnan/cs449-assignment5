import cv2
import mediapipe as mp
import math

# Constants
DESIRED_HEIGHT = 480
DESIRED_WIDTH = 480

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


# Helper function to resize and show image
def resize_and_show(image):
    h, w = image.shape[:2]
    if h < w:
        img = cv2.resize(image, (DESIRED_WIDTH, math.floor(h / (w / DESIRED_WIDTH))))
    else:
        img = cv2.resize(image, (math.floor(w / (h / DESIRED_HEIGHT)), DESIRED_HEIGHT))
    cv2.imshow('Image', img)


# Start video capture
cap = cv2.VideoCapture(0)

with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7) as hands:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Unable to access camera.")
            break

        # Flip the image horizontally for a later selfie-view display
        # Convert the BGR image to RGB
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Process the image and find hands
        results = hands.process(rgb_frame)

        # Draw the hand annotations on the image
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # Gesture recognition based on landmarks
                index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

                x_diff = index_finger_tip.x - wrist.x
                y_diff = index_finger_tip.y - wrist.y

                if x_diff < -0.1:
                    gesture = "Pointing Left"
                elif x_diff > 0.1:
                    gesture = "Pointing Right"
                elif y_diff < -0.1:
                    gesture = "Pointing Up"
                else:
                    gesture = "Neutral"

                # Display gesture text
                cv2.putText(frame, f'Gesture: {gesture}', (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)

        # Show the frame
        resize_and_show(frame)

        # Exit condition
        if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to quit
            break

cap.release()
cv2.destroyAllWindows()