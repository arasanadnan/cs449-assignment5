import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import messagebox
import math
import threading

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Game variables
selected_section = 0  # Starts at section 0
sections = ["A", "B", "C", "D", "E", "F", "G", "H"]

# Stop condition for the video loop
stop_processing = False


# Function to draw the circular interface
def draw_interface(canvas, selected_index):
    canvas.delete("all")  # Clear canvas
    width, height = 400, 400
    center_x, center_y = width // 2, height // 2
    radius = 150
    angle_step = 360 // len(sections)

    for i, section in enumerate(sections):
        angle = math.radians(i * angle_step)
        x = center_x + radius * math.cos(angle)
        y = center_y - radius * math.sin(angle)

        # Highlight selected section
        fill_color = "red" if i == selected_index else "gray"

        canvas.create_oval(
            x - 50, y - 50, x + 50, y + 50, fill=fill_color, outline="black"
        )
        canvas.create_text(x, y, text=section, font=("Arial", 16), fill="white")


# Function for action on selection
def on_selection(section):
    messagebox.showinfo("Action", f"Selected Section: {section}")


# Function to update the game interface
def update_interface():
    global selected_section
    draw_interface(canvas, selected_section)


# Function to process gestures and control the game
def process_gesture(x_diff, y_diff):
    global selected_section
    if x_diff < -0.1:  # Move left
        print("Detected Gesture: Moving Left")
        selected_section = (selected_section - 1) % len(sections)
        update_interface()
    elif x_diff > 0.1:  # Move right
        print("Detected Gesture: Moving Right")
        selected_section = (selected_section + 1) % len(sections)
        update_interface()
    elif y_diff < -0.1:  # Select current section
        print(f"Detected Gesture: Selecting Section {sections[selected_section]}")
        on_selection(sections[selected_section])
    else:
        print("Detected Gesture: Neutral (No action taken)")


# Video processing
def process_video():
    global stop_processing
    cap = cv2.VideoCapture(0)

    with mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7) as hands:

        while not stop_processing and cap.isOpened():
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
                    index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

                    x_diff = index_finger_tip.x - wrist.x
                    y_diff = index_finger_tip.y - wrist.y

                    # Process gesture
                    process_gesture(x_diff, y_diff)

            # Display the video feed
            cv2.imshow("Gesture Control", frame)

            if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to quit
                stop_processing = True
                break

    cap.release()
    cv2.destroyAllWindows()


# Tkinter GUI setup
root = tk.Tk()
root.title("Hand Gesture Game")
root.geometry("400x400")

# Canvas for game interface
canvas = tk.Canvas(root, width=400, height=400, bg="white")
canvas.pack()

# Initial interface setup
draw_interface(canvas, selected_section)


# Function to stop the video loop when the Tkinter window is closed
def on_closing():
    global stop_processing
    stop_processing = True
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_closing)

# Start video processing in a separate thread
video_thread = threading.Thread(target=process_video)
video_thread.daemon = True
video_thread.start()

# Run the Tkinter main loop
root.mainloop()