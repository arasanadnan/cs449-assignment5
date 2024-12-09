import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import messagebox
import random
import threading
import time

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
selected_button = None
timers = {}
timer_threads = {}
hand_present = False
scroll_mode = False
last_scroll_time = time.time()
start_screen_active = True
game_active = False
prizes = random.sample([1, 10, 100, 1000], 4)

root = tk.Tk()

# Functions for Start Screen
########################################
def confirm_selection_start_screen(button_key):
    global root, start_screen_active, game_active
    if selected_button == button_key and start_screen_active:
        if button_key == "start":
            start_screen_active = False
            load_game()
        elif button_key == "quit":
            root.destroy()

def start_timer_start_screen(button_key):
    if button_key in start_timers:
        for key, label in start_timers.items():
            if key != button_key:
                root.after(0, label.config, {'text': ''})
        # Countdown 5 seconds
        for i in range(5, 0, -1):
            root.after(0, start_timers[button_key].config, {'text': f"{i}s"})
            time.sleep(1)
            if selected_button != button_key:
                root.after(0, start_timers[button_key].config, {'text': ''})
                return
        root.after(0, confirm_selection_start_screen, button_key)

def check_cursor_over_button_start_screen(x, y):
    global selected_button, timer_threads
    over_button = None
    for key in start_buttons:
        btn_x, btn_y = start_button_positions[key]
        btn_width = 100
        btn_height = 50
        if (btn_x - btn_width / 2) <= x <= (btn_x + btn_width / 2) and \
           (btn_y - btn_height / 2) <= y <= (btn_y + btn_height / 2):
            over_button = key
            break
    if over_button:
        if selected_button == over_button:
            return
        for k, btn in start_buttons.items():
            btn.config(bg="gray")
            start_timers[k].config(text="")
            #if the cursor is on quit
        if over_button == "quit":
            start_buttons[over_button].config(bg="red")  # change color to red
        else:
            start_buttons[over_button].config(bg="blue") # base case: it remains blue

        selected_button = over_button
        if over_button not in timer_threads or not timer_threads[over_button].is_alive():
            timer_threads[over_button] = threading.Thread(target=start_timer_start_screen, args=(over_button,))
            timer_threads[over_button].start()
    else:
        reset_selection()
# Main Game Functions
########################################
def confirm_selection_game(button_key):
    global root
    if selected_button == button_key and game_active:
        prize = prizes[list(buttons.keys()).index(button_key)]
        messagebox.showinfo("Prize", f"Congratulations! You won {prize} TL!")
        root.after(0, root.destroy)

def start_timer_game(button_key):
    if button_key in timers:
        for key, label in timers.items():
            if key != button_key:
                root.after(0, label.config, {'text': ''})
        for i in range(5, 0, -1):
            root.after(0, timers[button_key].config, {'text': f"{i}s"})
            time.sleep(1)
            if selected_button != button_key:
                root.after(0, timers[button_key].config, {'text': ''})
                return
        root.after(0, confirm_selection_game, button_key)

def check_cursor_over_button_game(x, y):
    global selected_button, timer_threads
    over_button = None
    for key in buttons:
        btn_x, btn_y = button_positions[key]
        btn_width = 100
        btn_height = 50
        if (btn_x - btn_width / 2) <= x <= (btn_x + btn_width / 2) and \
           (btn_y - btn_height / 2) <= y <= (btn_y + btn_height / 2):
            over_button = key
            break

    if over_button:
        if selected_button == over_button:
            return
        for k, btn in buttons.items():
            btn.config(bg="gray")
            timers[k].config(text="")
        buttons[over_button].config(bg="blue")
        selected_button = over_button
        if over_button not in timer_threads or not timer_threads[over_button].is_alive():
            timer_threads[over_button] = threading.Thread(target=start_timer_game, args=(over_button,))
            timer_threads[over_button].start()
    else:
        reset_selection()

# Common Functions
########################################
def is_finger_extended(hand_landmarks, finger_name):
    # Detect if a specific finger is extended or changed
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
        return tip.x > pip.x
    else:
        return tip.y < pip.y

def move_cursor(screen_x, screen_y):
    if game_active:
        canvas.coords(cursor_window, screen_x, screen_y)
    elif start_screen_active:
        start_canvas.coords(start_cursor_window, screen_x, screen_y)

def hide_cursor():
    if game_active:
        canvas.coords(cursor_window, -100, -100)
    elif start_screen_active:
        start_canvas.coords(start_cursor_window, -100, -100)

def reset_selection():
    global selected_button
    selected_button = None
    if game_active:
        for key, label in timers.items():
            label.config(text="")
        for btn in buttons.values():
            btn.config(bg="gray")
    elif start_screen_active:
        for key, label in start_timers.items():
            label.config(text="")
        for btn in start_buttons.values():
            btn.config(bg="gray")

def scroll_canvas(direction):
    global last_scroll_time
    current_time = time.time()
    if current_time - last_scroll_time < 0.05:
        return
    last_scroll_time = current_time
    if direction == 'up':
        canvas.yview_scroll(-1, 'units')
    elif direction == 'down':
        canvas.yview_scroll(1, 'units')
    elif direction == 'left':
        canvas.xview_scroll(-1, 'units')
    elif direction == 'right':
        canvas.xview_scroll(1, 'units')

def process_video():
    global hand_present, selected_button, scroll_mode, start_screen_active, game_active
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        messagebox.showerror("Error", "Cannot access webcam.")
        root.destroy()
        return

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

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            cursor_visible = False

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )

                    # Check finger states
                    index_extended = is_finger_extended(hand_landmarks, 'index')
                    middle_extended = is_finger_extended(hand_landmarks, 'middle')
                    ring_extended = is_finger_extended(hand_landmarks, 'ring')
                    pinky_extended = is_finger_extended(hand_landmarks, 'pinky')

                    # Cursor mode (index + middle)
                    if index_extended and middle_extended and not ring_extended and not pinky_extended:
                        hand_present = True
                        cursor_visible = True
                        scroll_mode = False

                        index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                        middle_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

                        cursor_x = (index_finger_tip.x + middle_finger_tip.x) / 2
                        cursor_y = (index_finger_tip.y + middle_finger_tip.y) / 2

                        if game_active:
                            screen_x = cursor_x * canvas.winfo_width() + canvas.canvasx(0)
                            screen_y = cursor_y * canvas.winfo_height() + canvas.canvasy(0)
                            root.after(0, move_cursor, screen_x, screen_y)
                            root.after(0, check_cursor_over_button_game, screen_x, screen_y)
                        elif start_screen_active:
                            screen_x = cursor_x * start_canvas.winfo_width()
                            screen_y = cursor_y * start_canvas.winfo_height()
                            root.after(0, move_cursor, screen_x, screen_y)
                            root.after(0, check_cursor_over_button_start_screen, screen_x, screen_y)

                        prev_cursor_x, prev_cursor_y = None, None

                    elif index_extended and not middle_extended and not ring_extended and not pinky_extended and game_active:
                        # Scrolling gesture in game mode only
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

            if not cursor_visible:
                root.after(0, hide_cursor)

            cv2.imshow("Gesture Control", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()

# UI Setup
########################################
def load_game():
    global game_active, start_screen_active
    start_screen_active = False
    start_frame.destroy()
    game_window()

def game_window():
    global buttons, timers, timer_threads, root, cursor, canvas, cursor_window, button_positions, game_active
    game_active = True
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True)

    # Create a canvas for scrolling content
    canvas = tk.Canvas(frame, width=400, height=400, scrollregion=(0, 0, 800, 800))
    canvas.pack(side="left", fill="both", expand=True)

    vbar = tk.Scrollbar(frame, orient='vertical', command=canvas.yview)
    vbar.pack(side='right', fill='y')
    hbar = tk.Scrollbar(root, orient='horizontal', command=canvas.xview)
    hbar.pack(side='bottom', fill='x')

    canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

    buttons = {
        "left": tk.Button(canvas, text="?", font=("Arial", 18), bg="gray"),
        "right": tk.Button(canvas, text="?", font=("Arial", 18), bg="gray"),
        "up": tk.Button(canvas, text="?", font=("Arial", 18), bg="gray"),
        "down": tk.Button(canvas, text="?", font=("Arial", 18), bg="gray"),
    }

    timers = {
        "left": tk.Label(canvas, text="", font=("Arial", 12), fg="red"),
        "right": tk.Label(canvas, text="", font=("Arial", 12), fg="red"),
        "up": tk.Label(canvas, text="", font=("Arial", 12), fg="red"),
        "down": tk.Label(canvas, text="", font=("Arial", 12), fg="red"),
    }

    timer_threads.clear()
    button_positions = {
        "left": (50, 180),
        "right": (650, 180),
        "up": (350, 50),
        "down": (350, 650),
    }
    for key in buttons:
        x, y = button_positions[key]
        canvas.create_window(x, y, window=buttons[key], width=100, height=50)
        canvas.create_window(x, y + 60, window=timers[key], width=100, height=20)

    # Cursor
    cursor = tk.Label(canvas, text="X", font=("Arial", 12), fg="red")
    cursor_window = canvas.create_window(-100, -100, window=cursor)  # Initially off-screen

    globals()['buttons'] = buttons
    globals()['timers'] = timers
    globals()['canvas'] = canvas
    globals()['cursor_window'] = cursor_window
    globals()['button_positions'] = button_positions

# Start Screen Window
########################################
start_frame = tk.Frame(root)
start_frame.pack(fill="both", expand=True)
root.title("CS449-LOTTERY")
root.geometry("400x400")

start_canvas = tk.Canvas(start_frame, width=400, height=400)
start_canvas.pack(fill="both", expand=True)

title_label = tk.Label(start_canvas, text="CS449-LOTTERY", font=("Arial", 24), fg="blue")
start_canvas.create_window(200, 50, window=title_label)

start_buttons = {
    "start": tk.Button(start_canvas, text="Start", font=("Arial", 16), bg="gray"),
    "quit": tk.Button(start_canvas, text="Quit", font=("Arial", 16), bg="gray"),
}

start_timers = {
    "start": tk.Label(start_canvas, text="", font=("Arial", 12), fg="red"),
    "quit": tk.Label(start_canvas, text="", font=("Arial", 12), fg="red"),
}

start_button_positions = {
    "start": (200, 150),
    "quit": (200, 250),
}

for key in start_buttons:
    x, y = start_button_positions[key]
    start_canvas.create_window(x, y, window=start_buttons[key], width=100, height=50)
    start_canvas.create_window(x, y+60, window=start_timers[key], width=100, height=20)

start_cursor = tk.Label(start_canvas, text="X", font=("Arial", 12), fg="red")
start_cursor_window = start_canvas.create_window(-100, -100, window=start_cursor)  # off-screen initially

globals()['start_buttons'] = start_buttons
globals()['start_timers'] = start_timers
globals()['start_canvas'] = start_canvas
globals()['start_cursor_window'] = start_cursor_window
globals()['start_button_positions'] = start_button_positions

# Video processing
video_thread = threading.Thread(target=process_video)
video_thread.daemon = True
video_thread.start()

root.mainloop()