import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import messagebox
import random
import threading

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Initialize random prize amounts for the buttons
prizes = random.sample([1, 10, 100, 1000], 4)

# Tkinter GUI setup
root = tk.Tk()
root.title("CS449-LOTTERY")
root.geometry("400x400")

# Create buttons for directions
buttons = {
    "left": tk.Button(root, text=f"Left: {prizes[0]} TL", font=("Arial", 12), bg="gray"),
    "right": tk.Button(root, text=f"Right: {prizes[1]} TL", font=("Arial", 12), bg="gray"),
    "up": tk.Button(root, text=f"Up: {prizes[2]} TL", font=("Arial", 12), bg="gray"),
    "down": tk.Button(root, text=f"Down: {prizes[3]} TL", font=("Arial", 12), bg="gray"),
}

# Position buttons
buttons["left"].place(x=50, y=180, width=100, height=50)
buttons["right"].place(x=250, y=180, width=100, height=50)
buttons["up"].place(x=150, y=100, width=100, height=50)
buttons["down"].place(x=150, y=260, width=100, height=50)

# Variables to track selected button
selected_button = None

# Function to highlight a button
def highlight_button(direction):
    global selected_button
    for btn in buttons.values():
        btn.config(bg="gray")
    if direction in buttons:
        buttons[direction].config(bg="blue")
        selected_button = direction

# Function to confirm selection
def confirm_selection():
    if selected_button:
        prize = prizes[list(buttons.keys()).index(selected_button)]
        messagebox.showinfo("Prize", f"Congratulations! You won {prize} TL!")
    else:
        messagebox.showwarning("No Selection", "No button selected!")

# Video processing
def process_video():
    cap = cv2.VideoCapture(0)

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Flip and process frame
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )

                    # Gesture recognition
                    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    index_finger_tip = hand_landmarks.landmark[
                        mp_hands.HandLandmark.INDEX_FINGER_TIP
                    ]
                    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

                    x_diff = index_finger_tip.x - wrist.x
                    y_diff = index_finger_tip.y - wrist.y
                    thumb_diff = thumb_tip.y - index_finger_tip.y

                    # Detect gestures
                    if x_diff < -0.1:
                        highlight_button("left")
                    elif x_diff > 0.1:
                        highlight_button("right")
                    elif y_diff < -0.1:
                        highlight_button("up")
                    elif y_diff > 0.1:
                        highlight_button("down")
                    elif thumb_diff < -0.05:
                        confirm_selection()

            # Display the video feed
            cv2.imshow("Gesture Control", frame)

            if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to quit
                break

    cap.release()
    cv2.destroyAllWindows()

# Start video processing in a separate thread
video_thread = threading.Thread(target=process_video)
video_thread.daemon = True
video_thread.start()

# Run the Tkinter main loop
root.mainloop()
