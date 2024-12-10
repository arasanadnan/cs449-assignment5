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
hand_present = False  # Track if a hand is detected

# Random prize allocation for buttons
prizes = random.sample([1, 10, 100, 1000], 4)

root = tk.Tk()

# Function to confirm selection after 5 seconds
def confirm_selection(button_key):
    global root
    if selected_button == button_key:
        prize = prizes[list(buttons.keys()).index(button_key)]
        messagebox.showinfo("Prize", f"Congratulations! You won {prize} TL!")
        root.after(0, root.destroy)  # Close the game after showing the prize

# Function to start the 5-second timer
def start_timer(button_key):
    global timers, timer_threads, hand_present
    if button_key in timers:
        for key, label in timers.items():
            if key != button_key:
                root.after(0, label.config, {'text': ''})  # Clear other timers
        for i in range(5, 0, -1):
            root.after(0, timers[button_key].config, {'text': f"{i}s"})
            time.sleep(1)
            if not hand_present or selected_button != button_key:  # Stop timer if no hand detected or selection changes
                root.after(0, timers[button_key].config, {'text': ''})
                return
        root.after(0, confirm_selection, button_key)

# Function to check if a finger is extended
def is_finger_extended(hand_landmarks, finger_name):
    finger_tips = {
        'thumb': mp_hands.HandLandmark.THUMB_TIP,
        'index': mp_hands.HandLandmark.INDEX_FINGER_TIP,
        'middle': mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        'ring': mp_hands.HandLandmark.RING_FINGER_TIP,
        'pinky': mp_hands.HandLandmark.PINKY_TIP,
    }
    finger_pips = {
        'thumb': mp_hands.HandLandmark.THUMB_IP,
        'index': mp_hands.HandLandmark.INDEX_FINGER_PIP,
        'middle': mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
        'ring': mp_hands.HandLandmark.RING_FINGER_PIP,
        'pinky': mp_hands.HandLandmark.PINKY_PIP,
    }
    tip = hand_landmarks.landmark[finger_tips[finger_name]]
    pip = hand_landmarks.landmark[finger_pips[finger_name]]
    return tip.y < pip.y  # Finger is extended if tip is above PIP joint

# Function to move the cursor
def move_cursor(screen_x, screen_y):
    cursor.place(x=screen_x, y=screen_y)
    cursor.lift()

# Function to hide the cursor
def hide_cursor():
    cursor.place_forget()

# Function to reset selection
def reset_selection():
    global selected_button
    selected_button = None  # Reset selection
    for key, label in timers.items():
        label.config(text="")  # Clear all timers
    for btn in buttons.values():
        btn.config(bg="gray")  # Reset button highlights

# Function to check if cursor is over a button
def check_cursor_over_button(x, y):
    global selected_button, timer_threads
    over_button = None
    for key, btn in buttons.items():
        btn_x = btn.winfo_x()
        btn_y = btn.winfo_y()
        btn_width = btn.winfo_width()
        btn_height = btn.winfo_height()

        if btn_x <= x <= btn_x + btn_width and btn_y <= y <= btn_y + btn_height:
            over_button = key
            break

    if over_button:
        if selected_button == over_button:
            return  # Already selected
        for key, btn in buttons.items():
            btn.config(bg="gray")  # Reset all buttons
            timers[key].config(text="")  # Reset all timers
        buttons[over_button].config(bg="blue")
        selected_button = over_button
        if over_button not in timer_threads or not timer_threads[over_button].is_alive():
            timer_threads[over_button] = threading.Thread(target=start_timer, args=(over_button,))
            timer_threads[over_button].start()
    else:
        # Cursor not over any button
        reset_selection()

# Video processing for gesture detection
def process_video():
    global hand_present, selected_button
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

            # Initialize variables
            cursor_visible = False

            # Check if a hand is detected
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw landmarks
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )

                    # Check if index and middle fingers are extended, others closed
                    index_extended = is_finger_extended(hand_landmarks, 'index')
                    middle_extended = is_finger_extended(hand_landmarks, 'middle')
                    ring_extended = is_finger_extended(hand_landmarks, 'ring')
                    pinky_extended = is_finger_extended(hand_landmarks, 'pinky')

                    if index_extended and middle_extended and not ring_extended and not pinky_extended:
                        # Cursor gesture detected
                        hand_present = True
                        cursor_visible = True
                        # Get the positions of index and middle finger tips
                        index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                        middle_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

                        # Average their positions
                        cursor_x = (index_finger_tip.x + middle_finger_tip.x) / 2
                        cursor_y = (index_finger_tip.y + middle_finger_tip.y) / 2

                        # Map to screen coordinates
                        window_width = 400  # As set in root.geometry("400x400")
                        window_height = 400

                        screen_x = (1 - cursor_x) * window_width  # Flip x
                        screen_y = cursor_y * window_height

                        # Move the cursor widget
                        root.after(0, move_cursor, screen_x, screen_y)

                        # Check if cursor is over a button
                        root.after(0, check_cursor_over_button, screen_x, screen_y)

                        break  # Only process the first detected hand
                    else:
                        # Cursor gesture not detected
                        hand_present = False
                        cursor_visible = False
                        root.after(0, reset_selection)
            else:
                # No hand detected
                hand_present = False
                cursor_visible = False
                root.after(0, reset_selection)

            # Hide cursor if not visible
            if not cursor_visible:
                root.after(0, hide_cursor)

            # Display the video feed
            cv2.imshow("Gesture Control", frame)

            if cv2.waitKey(1) & 0xFF == 27:  # Press 'Esc' to quit
                break

    cap.release()
    cv2.destroyAllWindows()

# Main game window
def game_window():
    global buttons, timers, timer_threads, root, cursor
    root.title("CS449-LOTTERY")
    root.geometry("400x400")

    # Create buttons for directions
    buttons = {
        "left": tk.Button(root, text="?", font=("Arial", 18), bg="gray"),
        "right": tk.Button(root, text="?", font=("Arial", 18), bg="gray"),
        "up": tk.Button(root, text="?", font=("Arial", 18), bg="gray"),
        "down": tk.Button(root, text="?", font=("Arial", 18), bg="gray"),
    }

    # Create timer labels for each button
    timers = {
        "left": tk.Label(root, text="", font=("Arial", 12), fg="red"),
        "right": tk.Label(root, text="", font=("Arial", 12), fg="red"),
        "up": tk.Label(root, text="", font=("Arial", 12), fg="red"),
        "down": tk.Label(root, text="", font=("Arial", 12), fg="red"),
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

    # Cursor widget
    cursor = tk.Label(root, text="X", font=("Arial", 12), fg="red")
    cursor.place(x=0, y=0)

    # Start video processing in a separate thread
    video_thread = threading.Thread(target=process_video)
    video_thread.daemon = True
    video_thread.start()

    root.mainloop()

# Start the game
game_window()
