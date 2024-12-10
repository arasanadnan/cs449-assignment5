import cv2
import mediapipe as mp
import tkinter as tk
import random
import threading
import time
import queue
from tkinter import messagebox

# === Global State ===
running = True
hand_present = False
scroll_mode = False
timer_threads = {}
selected_item = None
current_buttons = {}
current_timers = {}
current_button_positions = {}
current_selection_callback = None

canvas = None
cursor_window = None
cursor_label = None

fruits = []
basket = None
dragging_fruit = None
score = 0
score_label = None  # HUD için skor etiketi

last_scroll_time = time.time()
prev_cursor_x = None
prev_cursor_y = None

root = tk.Tk()
root.title("Fruit Orchard")
root.geometry("600x600")
root.configure(bg="#f5f5dc")
root.resizable(False, False)

frame_queue = queue.Queue()

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

###########################################
# Gesture Functions
###########################################
def is_finger_extended(hand_landmarks, finger_name):
    mp_hands_tips = {
        'thumb': mp_hands.HandLandmark.THUMB_TIP,
        'index': mp_hands.HandLandmark.INDEX_FINGER_TIP,
        'middle': mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
        'ring': mp_hands.HandLandmark.RING_FINGER_TIP,
        'pinky': mp_hands.HandLandmark.PINKY_TIP,
    }
    mp_hands_pips = {
        'thumb': mp_hands.HandLandmark.THUMB_IP,
        'index': mp_hands.HandLandmark.INDEX_FINGER_PIP,
        'middle': mp_hands.HandLandmark.MIDDLE_FINGER_PIP,
        'ring': mp_hands.HandLandmark.RING_FINGER_PIP,
        'pinky': mp_hands.HandLandmark.PINKY_PIP,
    }

    tip = hand_landmarks.landmark[mp_hands_tips[finger_name]]
    pip = hand_landmarks.landmark[mp_hands_pips[finger_name]]
    if finger_name == 'thumb':
        return tip.x > pip.x
    else:
        return tip.y < pip.y

def move_cursor(screen_x, screen_y):
    if not running:
        return
    if canvas is None:
        return
    try:
        canvas.coords(cursor_window, screen_x, screen_y)
        if dragging_fruit is not None:
            canvas.coords(dragging_fruit['obj'], screen_x, screen_y)
    except tk.TclError:
        pass

def hide_cursor():
    if not running:
        return
    if canvas is None:
        return
    try:
        canvas.coords(cursor_window, -100, -100)
    except tk.TclError:
        pass

def reset_selection():
    global selected_item
    selected_item = None
    for key, label in current_timers.items():
        label.config(text="")
    for btn in current_buttons.values():
        btn.config(bg="gray")

def start_timer(item_key, callback, duration=2):
    if item_key in current_timers:
        for k, l in current_timers.items():
            if k != item_key:
                l.config(text="")
        for i in range(duration, 0, -1):
            if not running:
                return
            current_timers[item_key].config(text=f"{i}s")
            time.sleep(1)
            if not hand_present or selected_item != item_key or not running:
                current_timers[item_key].config(text="")
                return
        current_timers[item_key].config(text="")
        callback(item_key)

def check_cursor_over_item(x, y, item_positions, callback, duration=2):
    global selected_item, timer_threads
    over_item = None
    for key, pos in item_positions.items():
        ix, iy = pos
        w = 150
        h = 50
        if key.startswith("fruit"):
            w = 30
            h = 30
        if key == "basket":
            w = 100
            h = 60
        if (ix - w/2) <= x <= (ix + w/2) and (iy - h/2) <= y <= (iy + h/2):
            over_item = key
            break

    if over_item:
        if selected_item == over_item:
            return
        for k, btn in current_buttons.items():
            btn.config(bg="gray")
        for k, l in current_timers.items():
            l.config(text="")
        if over_item in current_buttons:
            current_buttons[over_item].config(bg="#add8e6")
        selected_item = over_item
        if over_item not in timer_threads or not timer_threads[over_item].is_alive():
            t = threading.Thread(target=start_timer, args=(over_item, callback, duration))
            timer_threads[over_item] = t
            t.start()
    else:
        reset_selection()

def scroll_canvas(direction):
    global last_scroll_time
    if not running:
        return
    if canvas is None:
        return
    current_time = time.time()
    if current_time - last_scroll_time < 0.05:
        return
    last_scroll_time = current_time
    try:
        if direction == 'up':
            canvas.yview_scroll(-1, 'units')
        elif direction == 'down':
            canvas.yview_scroll(1, 'units')
        elif direction == 'left':
            canvas.xview_scroll(-1, 'units')
        elif direction == 'right':
            canvas.xview_scroll(1, 'units')
    except tk.TclError:
        pass

###########################################
# OpenCV & MediaPipe Thread
###########################################
def process_video():
    global hand_present, scroll_mode, prev_cursor_x, prev_cursor_y, running
    cap = cv2.VideoCapture(0)
    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:
        while running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)

            cursor_visible = False

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    index_ext = is_finger_extended(hand_landmarks, 'index')
                    middle_ext = is_finger_extended(hand_landmarks, 'middle')
                    ring_ext = is_finger_extended(hand_landmarks, 'ring')
                    pinky_ext = is_finger_extended(hand_landmarks, 'pinky')

                    # Yeni Gesture: INDEX+MIDDLE+RING açık, PINKY kapalı -> Çıkış
                    if index_ext and middle_ext and ring_ext and not pinky_ext:
                        hand_present = True
                        scroll_mode = False
                        cursor_visible = False
                        # Oyunu kapat
                        root.after(0, on_close)

                    elif index_ext and middle_ext and not ring_ext and not pinky_ext:
                        # Move mode
                        hand_present = True
                        cursor_visible = True
                        scroll_mode = False

                        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                        middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

                        cx = (index_tip.x + middle_tip.x) / 2
                        cy = (index_tip.y + middle_tip.y) / 2

                        if canvas is not None and running:
                            screen_x = cx * canvas.winfo_width() + canvas.canvasx(0)
                            screen_y = cy * canvas.winfo_height() + canvas.canvasy(0)

                            root.after(0, move_cursor, screen_x, screen_y)
                            if current_button_positions and current_selection_callback:
                                root.after(0, check_cursor_over_item, screen_x, screen_y, current_button_positions, current_selection_callback, 2)
                            prev_cursor_x, prev_cursor_y = None, None

                    elif index_ext and not middle_ext and not ring_ext and not pinky_ext:
                        # Scroll mode
                        hand_present = True
                        cursor_visible = False
                        scroll_mode = True

                        index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                        cx = index_tip.x
                        cy = index_tip.y

                        if prev_cursor_x is not None and prev_cursor_y is not None and running:
                            dx = cx - prev_cursor_x
                            dy = cy - prev_cursor_y
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
                        prev_cursor_x, prev_cursor_y = cx, cy
                        root.after(0, hide_cursor)
                        root.after(0, reset_selection)

                    else:
                        hand_present = False
                        cursor_visible = False
                        scroll_mode = False
                        prev_cursor_x, prev_cursor_y = None, None
                        root.after(0, reset_selection)
                        root.after(0, hide_cursor)
            else:
                hand_present = False
                cursor_visible = False
                scroll_mode = False
                prev_cursor_x, prev_cursor_y = None, None
                root.after(0, reset_selection)
                root.after(0, hide_cursor)

            if not cursor_visible:
                root.after(0, hide_cursor)

            frame_queue.put(frame)

    cap.release()

def show_frame():
    if not running:
        return
    if not frame_queue.empty():
        frame = frame_queue.get()
        cv2.imshow("Gesture Control", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            on_close()
            return
    root.after(10, show_frame)

###########################################
# Menu / Instructions
###########################################
def menu_selection(item_key):
    if item_key == "play":
        show_game()
    elif item_key == "instructions":
        show_instructions()
        reset_selection()
    elif item_key == "quit":
        on_close()

def show_instructions():
    messagebox.showinfo("Instructions",
                        "Use hand gestures:\n"
                        "- INDEX + MIDDLE: Move the cursor.\n"
                        "- INDEX only: Scroll the view.\n"
                        "- INDEX + MIDDLE + RING: Quit the game.\n\n"
                        "Hover 2s over items to select them.\n\n"
                        "In the game:\n"
                        "- Hover 2s over a fruit to pick it.\n"
                        "- Hover 2s over the basket to drop it and gain a point.\n"
                        "Scrolling helps you find fruits out of view!")

def show_menu():
    for w in root.winfo_children():
        if w != root:
            w.destroy()

    global canvas, cursor_window, cursor_label
    canvas = tk.Canvas(root, width=600, height=600, bg="#fffaf0", scrollregion=(0,0,600,600))
    canvas.pack(fill="both", expand=True)

    global current_buttons, current_timers, current_button_positions, current_selection_callback, timer_threads
    current_buttons = {
        "play": tk.Button(canvas, text="Play Game", font=("Arial",14), bg="gray", fg="black"),
        "instructions": tk.Button(canvas, text="Instructions", font=("Arial",14), bg="gray", fg="black"),
        "quit": tk.Button(canvas, text="Quit", font=("Arial",14), bg="gray", fg="black")
    }

    current_timers = {
        "play": tk.Label(canvas, text="", font=("Arial",12), fg="red", bg="#fffaf0"),
        "instructions": tk.Label(canvas, text="", font=("Arial",12), fg="red", bg="#fffaf0"),
        "quit": tk.Label(canvas, text="", font=("Arial",12), fg="red", bg="#fffaf0")
    }

    current_button_positions = {
        "play": (300,200),
        "instructions": (300,300),
        "quit": (300,400)
    }

    for k in current_buttons:
        x, y = current_button_positions[k]
        canvas.create_window(x, y, window=current_buttons[k], width=150, height=50)
        canvas.create_window(x, y+30, window=current_timers[k], width=150, height=20)

    timer_threads = {}
    current_selection_callback = menu_selection

    cursor_label = tk.Label(canvas, text="X", font=("Arial",12), fg="red", bg="#fffaf0")
    cursor_window = canvas.create_window(-100, -100, window=cursor_label)

###########################################
# Game Logic
###########################################
def pick_up_fruit(item_key):
    global dragging_fruit
    for f in fruits:
        if f['key'] == item_key:
            dragging_fruit = f
            break

def drop_fruit(item_key):
    global dragging_fruit, score
    if dragging_fruit is not None and running:
        try:
            canvas.delete(dragging_fruit['obj'])
        except tk.TclError:
            pass
        dragging_fruit = None
        score += 1
        # Skor labelini güncelle
        update_score_label()

def update_score_label():
    if score_label is not None:
        score_label.config(text=f"Score: {score}")

def game_selection(item_key):
    if item_key.startswith("fruit"):
        pick_up_fruit(item_key)
    elif item_key == "basket" and dragging_fruit is not None:
        drop_fruit(item_key)

def show_game():
    for w in root.winfo_children():
        if w != root:
            w.destroy()

    global canvas, cursor_label, cursor_window, fruits, basket, score, dragging_fruit, score_label
    canvas = tk.Canvas(root, width=600, height=600, bg="#fffaf0", scrollregion=(0,0,1200,1200))
    canvas.pack(fill="both", expand=True)

    vbar = tk.Scrollbar(root, orient='vertical', command=canvas.yview)
    vbar.pack(side='right', fill='y')
    hbar = tk.Scrollbar(root, orient='horizontal', command=canvas.xview)
    hbar.pack(side='bottom', fill='x')
    canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

    title_label = tk.Label(root, text="Fruit Orchard", font=("Arial",20,"bold"), fg="black", bg="#f5f5dc")
    title_label.place(x=200, y=10)

    info_label = tk.Label(root, text="Hover 2s over a fruit to pick it.\nThen hover 2s over the basket to drop it.\nUse single finger (index) to scroll!",
                          font=("Arial",12), fg="black", bg="#f5f5dc")
    info_label.place(x=120, y=50)

    # Skor etiketi (HUD)
    global score
    score = 0
    global score_label
    score_label = tk.Label(root, text=f"Score: {score}", font=("Arial",14,"bold"), fg="black", bg="#f5f5dc")
    score_label.place(x=10, y=10)  # Sol üst köşeye yakın bir yere yerleştirildi

    fruits = []
    dragging_fruit = None

    global current_buttons, current_timers, current_button_positions, current_selection_callback, timer_threads
    current_buttons = {}
    current_timers = {}
    current_button_positions = {}

    # Place fruits randomly
    for i in range(5):
        fx = random.randint(100,1100)
        fy = random.randint(100,1100)
        fruit_obj = canvas.create_text(fx, fy, text="🍎", font=("Arial",24))
        fruit_key = f"fruit{i}"
        fruits.append({'key':fruit_key, 'obj':fruit_obj, 'x':fx, 'y':fy})
        current_timers[fruit_key] = tk.Label(canvas, text="", font=("Arial",12), fg="red", bg="#fffaf0")
        canvas.create_window(fx, fy+30, window=current_timers[fruit_key], width=30, height=20)
        current_button_positions[fruit_key] = (fx, fy)

    # Basket
    basket_x = 600
    basket_y = 600
    basket_obj = canvas.create_text(basket_x, basket_y, text="🧺", font=("Arial",30))
    basket = {'key':'basket', 'obj':basket_obj, 'x':basket_x, 'y':basket_y}

    current_button_positions['basket'] = (basket_x, basket_y)
    current_timers['basket'] = tk.Label(canvas, text="", font=("Arial",12), fg="red", bg="#fffaf0")
    canvas.create_window(basket_x, basket_y+50, window=current_timers['basket'], width=100, height=20)

    timer_threads = {}
    current_selection_callback = game_selection

    cursor_label = tk.Label(canvas, text="X", font=("Arial",12), fg="red", bg="#fffaf0")
    cursor_window = canvas.create_window(-100, -100, window=cursor_label)

###########################################
# Window Close Handling
###########################################
def on_close():
    global running
    running = False
    time.sleep(0.5)
    cv2.destroyAllWindows()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)

###########################################
# Start
###########################################
def start_app():
    show_menu()
    video_thread = threading.Thread(target=process_video)
    video_thread.daemon = True
    video_thread.start()
    show_frame()
    root.mainloop()

start_app()
