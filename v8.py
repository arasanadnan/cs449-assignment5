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

# Global variables
selected_button = None
timers = {}
timer_threads = {}
start_screen_active = True
game_active = False

# Random prize allocation for buttons
prizes = random.sample([1, 10, 100, 1000], 4)

# Function to confirm selection after 5 seconds
def confirm_selection(button_key):
    global root
    if selected_button == button_key:
        if start_screen_active:
            if button_key == "start":
                load_game()
            elif button_key == "quit":
                quit_game()
        elif game_active:
            prize = prizes[list(buttons.keys()).index(button_key)]
            messagebox.showinfo("Prize", f"Congratulations! You won {prize} TL!")
            root.destroy()  # Close the game after showing the prize

# Function to start the 5-second timer
def start_timer(button_key):
    global timers, timer_threads
    if button_key in timers:
        for key, label in timers.items():
            if key != button_key:
                label.config(text="")  # Clear other timers
        for i in range(5, 0, -1):
            timers[button_key].config(text=f"{i}s")
            time.sleep(1)
            if selected_button != button_key:  # If selection changes, reset timer
                timers[button_key].config(text="")
                return
        confirm_selection(button_key)

# Function to highlight a button and start its timer
def highlight_button(direction):
    global selected_button, timer_threads
    for key, btn in buttons.items():
        btn.config(bg="gray")  # Reset all buttons
        timers[key].config(text="")  # Reset all timers
    if direction in buttons:
        buttons[direction].config(bg="blue")
        selected_button = direction
        if direction not in timer_threads or not timer_threads[direction].is_alive():
            timer_threads[direction] = threading.Thread(target=start_timer, args=(direction,))
            timer_threads[direction].start()

# Video processing for gesture detection
def process_video():
    global start_screen_active, game_active
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
                    if start_screen_active:
                        if y_diff < -0.1:
                            highlight_button("start")
                        elif y_diff > 0.1:
                            highlight_button("quit")
                    elif game_active:
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

# Function to quit the game
def quit_game():
    root.destroy()

# Function to start the game
def load_game():
    global start_screen_active, game_active
    start_screen_active = False
    main_menu.destroy()
    game_window()

# Main game window
def game_window():
    global buttons, timers, game_active, timer_threads
    game_active = True
    game = tk.Tk()
    game.title("CS449-LOTTERY")
    game.geometry("400x400")

    # Create buttons for directions
    buttons = {
        "left": tk.Button(game, text="?", font=("Arial", 18), bg="gray"),
        "right": tk.Button(game, text="?", font=("Arial", 18), bg="gray"),
        "up": tk.Button(game, text="?", font=("Arial", 18), bg="gray"),
        "down": tk.Button(game, text="?", font=("Arial", 18), bg="gray"),
    }

    # Create timer labels for each button
    timers = {
        "left": tk.Label(game, text="", font=("Arial", 12), fg="red"),
        "right": tk.Label(game, text="", font=("Arial", 12), fg="red"),
        "up": tk.Label(game, text="", font=("Arial", 12), fg="red"),
        "down": tk.Label(game, text="", font=("Arial", 12), fg="red"),
    }

    timer_threads = {}

    # Position buttons and timers
    buttons["left"].place(x=50, y=180, width=100, height=50)
    timers["left"].place(x=50, y=240, width=100, height=20)

    buttons["right"].place(x=250, y=180, width=100, height=50)
    timers["right"].place(x=250, y=240, width=100, height=20)

    buttons["up"].place(x=150, y=100, width=100, height=50)
    timers["up"].place(x=150, y=160, width=100, height=20)

    buttons["down"].place(x=150, y=260, width=100, height=50)
    timers["down"].place(x=150, y=320, width=100, height=20)

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
buttons = {
    "start": tk.Button(main_menu, text="Start", font=("Arial", 16), bg="gray"),
    "quit": tk.Button(main_menu, text="Quit", font=("Arial", 16), bg="gray"),
}

timers = {
    "start": tk.Label(main_menu, text="", font=("Arial", 12), fg="red"),
    "quit": tk.Label(main_menu, text="", font=("Arial", 12), fg="red"),
}

buttons["start"].place(x=150, y=150, width=100, height=50)
timers["start"].place(x=150, y=210, width=100, height=20)

buttons["quit"].place(x=150, y=250, width=100, height=50)
timers["quit"].place(x=150, y=310, width=100, height=20)

# Start video processing in a separate thread
video_thread = threading.Thread(target=process_video)
video_thread.daemon = True
video_thread.start()

root.mainloop()
