import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import messagebox
import random
import threading
import time

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Random prize allocation for buttons
prizes = random.sample([1, 10, 100, 1000], 4)

# Global variables for button selection and timer
selected_button = None
timer_running = False

# Function to start the game
def start_game():
    main_menu.destroy()
    game_window()

# Function to quit the game
def quit_game():
    root.destroy()

# Function to confirm selection after 5 seconds
def confirm_selection():
    global selected_button, timer_running
    if selected_button:
        prize = prizes[list(buttons.keys()).index(selected_button)]
        messagebox.showinfo("Prize", f"Congratulations! You won {prize} TL!")
        timer_running = False
    else:
        messagebox.showwarning("No Selection", "No button selected!")

# Function to start the 5-second timer
def start_timer():
    global timer_running
    timer_running = True
    for i in range(5, 0, -1):
        timer_label.config(text=f"Confirming in {i}...")
        time.sleep(1)
        if not timer_running:  # If another button is selected, reset the timer
            return
    confirm_selection()

# Function to highlight a button
def highlight_button(direction):
    global selected_button, timer_running
    for btn in buttons.values():
        btn.config(bg="gray")
    if direction in buttons:
        buttons[direction].config(bg="blue")
        selected_button = direction
        if not timer_running:
            threading.Thread(target=start_timer).start()

# Video processing for gesture detection
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
                    index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]

                    x_diff = index_finger_tip.x - wrist.x
                    y_diff = index_finger_tip.y - wrist.y

                    # Detect gestures
                    if x_diff < -0.1:
                        highlight_button("left")
                    elif x_diff > 0.1:
                        highlight_button("right")
                    elif y_diff < -0.1:
                        highlight_button("up")
                    elif y_diff > 0.1:
                        highlight_button("down")

            # Display the video feed
            cv2.imshow("Gesture Control", frame)

            if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to quit
                break

    cap.release()
    cv2.destroyAllWindows()

# Main game window
def game_window():
    global buttons, timer_label
    game = tk.Tk()
    game.title("CS449-LOTTERY")
    game.geometry("400x400")

    # Create buttons for directions
    buttons = {
        "left": tk.Button(game, text=f"Left: {prizes[0]} TL", font=("Arial", 12), bg="gray"),
        "right": tk.Button(game, text=f"Right: {prizes[1]} TL", font=("Arial", 12), bg="gray"),
        "up": tk.Button(game, text=f"Up: {prizes[2]} TL", font=("Arial", 12), bg="gray"),
        "down": tk.Button(game, text=f"Down: {prizes[3]} TL", font=("Arial", 12), bg="gray"),
    }

    # Position buttons
    buttons["left"].place(x=50, y=180, width=100, height=50)
    buttons["right"].place(x=250, y=180, width=100, height=50)
    buttons["up"].place(x=150, y=100, width=100, height=50)
    buttons["down"].place(x=150, y=260, width=100, height=50)

    # Timer label
    timer_label = tk.Label(game, text="", font=("Arial", 12), fg="red")
    timer_label.pack(side="bottom", pady=10)

    # Start video processing in a separate thread
    video_thread = threading.Thread(target=process_video)
    video_thread.daemon = True
    video_thread.start()

    game.mainloop()

# Main menu window
root = tk.Tk()
root.title("CS449-LOTTERY")
root.geometry("400x400")

main_menu = tk.Frame(root)
main_menu.pack(fill="both", expand=True)

# Game title
title_label = tk.Label(main_menu, text="CS449-LOTTERY", font=("Arial", 24), fg="blue")
title_label.pack(pady=50)

# Start and Quit buttons
start_button = tk.Button(main_menu, text="Start", font=("Arial", 16), command=start_game)
start_button.pack(pady=20)

quit_button = tk.Button(main_menu, text="Quit", font=("Arial", 16), command=quit_game)
quit_button.pack(pady=20)

root.mainloop()
