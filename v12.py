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
scroll_mode = False   # Flag to indicate scrolling mode
last_scroll_time = time.time()

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
    if finger_name == 'thumb':
        return tip.x > pip.x  # For thumb, x-axis comparison
    else:
        return tip.y < pip.y  # For other fingers, y-axis comparison

# Function to move the cursor
def move_cursor(screen_x, screen_y):
    canvas.coords(cursor_window, screen_x, screen_y)

# Function to hide the cursor
def hide_cursor():
    canvas.coords(cursor_window, -100, -100)  # Move cursor off-screen

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
    for key in buttons:
        btn_x, btn_y = button_positions[key]
        btn_width = 100  # As specified in create_window
        btn_height = 50

        if (btn_x - btn_width / 2) <= x <= (btn_x + btn_width / 2) and \
           (btn_y - btn_height / 2) <= y <= (btn_y + btn_height / 2):
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

# Function to scroll the canvas
def scroll_canvas(direction):
    global last_scroll_time
    current_time = time.time()
    if current_time - last_scroll_time < 0.05:
        return  # Limit scroll rate
    last_scroll_time = current_time
    if direction == 'up':
        canvas.yview_scroll(-1, 'units')
    elif direction == 'down':
        canvas.yview_scroll(1, 'units')
    elif direction == 'left':
        canvas.xview_scroll(-1, 'units')
    elif direction == 'right':
        canvas.xview_scroll(1, 'units')

# Video processing for gesture detection
def process_video():
    global hand_present, selected_button, scroll_mode
    cap = cv2.VideoCapture(0)

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:
        prev_cursor_x, prev_cursor_y = None, None
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

                    # Check which fingers are extended
                    index_extended = is_finger_extended(hand_landmarks, 'index')
                    middle_extended = is_finger_extended(hand_landmarks, 'middle')
                    ring_extended = is_finger_extended(hand_landmarks, 'ring')
                    pinky_extended = is_finger_extended(hand_landmarks, 'pinky')
                    thumb_extended = is_finger_extended(hand_landmarks, 'thumb')

                    if index_extended and middle_extended and not ring_extended and not pinky_extended:
                        # Cursor gesture detected
                        hand_present = True
                        cursor_visible = True
                        scroll_mode = False

                        # Get the positions of index and middle finger tips
                        index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                        middle_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

                        # Average their positions
                        cursor_x = (index_finger_tip.x + middle_finger_tip.x) / 2
                        cursor_y = (index_finger_tip.y + middle_finger_tip.y) / 2

                        # Map to canvas coordinates considering the scroll position
                        window_width = 400  # As set in root.geometry("400x400")
                        window_height = 400

                        screen_x = cursor_x * canvas.winfo_width() + canvas.canvasx(0)
                        screen_y = cursor_y * canvas.winfo_height() + canvas.canvasy(0)

                        # Move the cursor widget
                        root.after(0, move_cursor, screen_x, screen_y)

                        # Check if cursor is over a button
                        root.after(0, check_cursor_over_button, screen_x, screen_y)

                        prev_cursor_x, prev_cursor_y = None, None  # Reset scroll tracking

                    elif index_extended and not middle_extended and not ring_extended and not pinky_extended:
                        # Scrolling gesture detected
                        hand_present = True
                        cursor_visible = False
                        scroll_mode = True

                        index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

                        cursor_x = index_finger_tip.x
                        cursor_y = index_finger_tip.y

                        if prev_cursor_x is not None and prev_cursor_y is not None:
                            dx = cursor_x - prev_cursor_x
                            dy = cursor_y - prev_cursor_y

                            if abs(dx) > abs(dy):
                                if dx > 0.01:
                                    root.after(0, scroll_canvas, 'right')
                                elif dx < -0.01:
                                    root.after(0, scroll_canvas, 'left')
                            else:
                                if dy > 0.01:
                                    root.after(0, scroll_canvas, 'down')
                                elif dy < -0.01:
                                    root.after(0, scroll_canvas, 'up')
                        prev_cursor_x, prev_cursor_y = cursor_x, cursor_y
                        root.after(0, hide_cursor)
                        root.after(0, reset_selection)

                    else:
                        # No recognized gesture
                        hand_present = False
                        cursor_visible = False
                        scroll_mode = False
                        prev_cursor_x, prev_cursor_y = None, None
                        root.after(0, reset_selection)
                        root.after(0, hide_cursor)
            else:
                # No hand detected
                hand_present = False
                cursor_visible = False
                scroll_mode = False
                prev_cursor_x, prev_cursor_y = None, None
                root.after(0, reset_selection)
                root.after(0, hide_cursor)

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
    global buttons, timers, timer_threads, root, cursor, canvas, cursor_window, button_positions
    root.title("CS449-LOTTERY")
    root.geometry("400x400")

    # Create a frame for canvas and scrollbars
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True)

    # Create a canvas for scrolling content
    canvas = tk.Canvas(frame, width=400, height=400, scrollregion=(0, 0, 800, 800))
    canvas.pack(side="left", fill="both", expand=True)

    # Add scrollbars
    vbar = tk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    vbar.pack(side='right', fill='y')
    hbar = tk.Scrollbar(root, orient='horizontal', command=canvas.xview)
    hbar.pack(side='bottom', fill='x')

    canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

    # Create buttons for directions on the canvas
    buttons = {
        "left": tk.Button(canvas, text="?", font=("Arial", 18), bg="gray"),
        "right": tk.Button(canvas, text="?", font=("Arial", 18), bg="gray"),
        "up": tk.Button(canvas, text="?", font=("Arial", 18), bg="gray"),
        "down": tk.Button(canvas, text="?", font=("Arial", 18), bg="gray"),
    }

    # Create timer labels for each button
    timers = {
        "left": tk.Label(canvas, text="", font=("Arial", 12), fg="red"),
        "right": tk.Label(canvas, text="", font=("Arial", 12), fg="red"),
        "up": tk.Label(canvas, text="", font=("Arial", 12), fg="red"),
        "down": tk.Label(canvas, text="", font=("Arial", 12), fg="red"),
    }

    timer_threads = {}

    # Store button positions
    button_positions = {
        "left": (50, 180),
        "right": (650, 180),
        "up": (350, 50),
        "down": (350, 650),
    }

    # Position buttons and timers on the canvas using create_window
    for key in buttons:
        x, y = button_positions[key]
        canvas.create_window(x, y, window=buttons[key], width=100, height=50)
        canvas.create_window(x, y + 60, window=timers[key], width=100, height=20)

    # Cursor widget
    cursor = tk.Label(canvas, text="X", font=("Arial", 12), fg="red")
    cursor_window = canvas.create_window(-100, -100, window=cursor)  # Initially off-screen

    # Start video processing in a separate thread
    video_thread = threading.Thread(target=process_video)
    video_thread.daemon = True
    video_thread.start()

    root.mainloop()

# Start the game
game_window()
