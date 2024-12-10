import cv2
import mediapipe as mp
import tkinter as tk
from tkinter import messagebox
import random

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

root = tk.Tk()
root.title("CS449-LOTTERY")
root.geometry("400x400")
selected_button = None
hand_present = False
start_screen_active = True
signup_screen_active = False
game_active = False
scoreboard_active = False
player_name = ""
prize_won = None
scoreboard_data = []
prizes = random.sample([1, 10, 100, 1000], 4)
current_canvas = None
cursor = None
cursor_window = None
hovered_button = None
countdown_after_id = None
countdown_remaining = 0
letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# Utils Functions
############################
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
        return tip.x > pip.x
    else:
        return tip.y < pip.y

def reset_selection():
    global selected_button, hovered_button
    selected_button = None
    hovered_button = None
    cancel_countdown()
    if start_screen_active:
        for k,label in start_timers.items():
            label.config(text="")
        for k,btn in start_buttons.items():
            btn.config(bg="gray")
    elif signup_screen_active:
        for k,label in signup_timers.items():
            label.config(text="")
        for k,btn in signup_buttons.items():
            btn.config(bg="gray")
    elif game_active:
        for k,label in timers.items():
            label.config(text="")
        for k,btn in buttons.items():
            btn.config(bg="gray")

def hide_cursor():
    if current_canvas and cursor_window is not None:
        current_canvas.coords(cursor_window, -100, -100)

def move_cursor(screen_x, screen_y):
    if current_canvas and cursor_window is not None:
        current_canvas.coords(cursor_window, screen_x, screen_y)

    if start_screen_active:
        check_cursor_over_button_start_screen(screen_x, screen_y)
    elif signup_screen_active:
        check_cursor_over_button_signup(screen_x, screen_y)
    elif game_active:
        check_cursor_over_button_game(screen_x, screen_y)

def cancel_countdown():
    global countdown_after_id, hovered_button
    if countdown_after_id is not None:
        root.after_cancel(countdown_after_id)
        countdown_after_id = None
    hovered_button = None

def start_countdown(button_key):
    global countdown_remaining, hovered_button
    hovered_button = button_key
    countdown_remaining = 3  # Reduced to 3 seconds
    update_countdown()

def update_countdown():
    global countdown_remaining, hovered_button, countdown_after_id
    if hovered_button is None:
        return
    if countdown_remaining <= 0:
        countdown_after_id = None
        confirm_selection(hovered_button)
        return
    label = get_timer_label(hovered_button)
    if label:
        label.config(text=f"{countdown_remaining}s")
    countdown_remaining -= 1
    countdown_after_id = root.after(1000, update_countdown)

def confirm_selection(button_key):
    if start_screen_active:
        confirm_selection_start_screen(button_key)
    elif signup_screen_active:
        confirm_selection_signup(button_key)
    elif game_active:
        confirm_selection_game(button_key)

def get_timer_label(button_key):
    if start_screen_active:
        return start_timers.get(button_key)
    elif signup_screen_active:
        return signup_timers.get(button_key)
    elif game_active:
        return timers.get(button_key)
    return None

# Start Screen
############################
def confirm_selection_start_screen(button_key):
    global start_screen_active, signup_screen_active
    if selected_button == button_key and start_screen_active:
        if button_key == "start":
            start_screen_active = False
            start_frame.destroy()
            load_signup()
        elif button_key == "quit":
            root.destroy()

def hover_start_screen_button(button_key):
    if button_key == "start":
        start_buttons[button_key].config(bg='blue')
    elif button_key == "quit":
        start_buttons[button_key].config(bg='red')

def check_cursor_over_button_start_screen(x,y):
    global selected_button
    over_button=None
    for key in start_buttons:
        bx,by=start_button_positions[key]
        bw,bh=150,70
        if (bx-bw/2)<=x<=(bx+bw/2) and (by-bh/2)<=y<=(by+bh/2):
            over_button=key
            break
    if over_button:
        if selected_button==over_button:
            return
        reset_selection()
        hover_start_screen_button(over_button)
        selected_button=over_button
        start_countdown(over_button)
    else:
        reset_selection()

# Signup Screen
############################
def load_signup():
    global signup_screen_active, signup_frame, player_name
    signup_screen_active = True
    player_name = ""
    signup_frame = tk.Frame(root)
    signup_frame.pack(fill="both", expand=True)
    scanvas = tk.Canvas(signup_frame, width=400, height=400)
    scanvas.pack(fill='both', expand=True)

    global current_canvas, cursor, cursor_window
    current_canvas=scanvas
    global player_name_label
    player_name_label = tk.Label(scanvas, text="Name: ", font=("Arial",16), fg='black')
    scanvas.create_window(200,30,window=player_name_label)
    global signup_buttons, signup_timers, signup_button_positions
    signup_buttons={}
    signup_timers={}
    cols=7
    rows=4
    x_start,y_start=50,70
    x_gap=50
    y_gap=50
    letter_width=60
    letter_height=40

    # Place letters A-Z for username signup
    for i,letter in enumerate(letters):
        row=i//cols
        col=i%cols
        x_pos=x_start+(col*x_gap)
        y_pos=y_start+(row*y_gap)
        signup_buttons[letter]=tk.Button(scanvas,text=letter,font=("Arial",12),bg='gray')
        signup_timers[letter]=tk.Label(scanvas,text="",font=("Arial",10),fg='red')
        scanvas.create_window(x_pos,y_pos,window=signup_buttons[letter],width=letter_width,height=letter_height)
        scanvas.create_window(x_pos,y_pos+letter_height/2+10,window=signup_timers[letter],width=letter_width,height=20)

    # Start Game button
    signup_buttons["start_game"]=tk.Button(scanvas,text="Start Game",font=("Arial",14),bg='gray')
    signup_timers["start_game"]=tk.Label(scanvas,text="",font=("Arial",10),fg='red')
    sg_x,sg_y=200,300
    start_game_width=150
    start_game_height=70
    scanvas.create_window(sg_x,sg_y,window=signup_buttons["start_game"],width=start_game_width,height=start_game_height)
    scanvas.create_window(sg_x,sg_y+start_game_height/2+10,window=signup_timers["start_game"],width=100,height=20)
    signup_button_positions={}
    for i,letter in enumerate(letters):
        row=i//cols
        col=i%cols
        x_pos=x_start+(col*x_gap)
        y_pos=y_start+(row*y_gap)
        signup_button_positions[letter]=(x_pos,y_pos)
    signup_button_positions["start_game"]=(sg_x,sg_y)

    globals()['signup_buttons']=signup_buttons
    globals()['signup_timers']=signup_timers
    globals()['signup_button_positions']=signup_button_positions

    cursor=tk.Label(scanvas,text="X",font=("Arial",12),fg='red')
    cursor_window=scanvas.create_window(-100,-100,window=cursor)

def confirm_selection_signup(button_key):
    global selected_button, signup_screen_active, player_name
    if selected_button==button_key and signup_screen_active:
        if button_key in letters:
            player_name+=button_key
            player_name_label.config(text="Name: "+player_name)
        elif button_key=='start_game':
            signup_screen_active=False
            signup_frame.destroy()
            load_game_window()

def hover_signup_button(button_key):
    if button_key in letters:
        signup_buttons[button_key].config(bg='lightblue')
    elif button_key=='start_game':
        signup_buttons[button_key].config(bg='blue')

def check_cursor_over_button_signup(x,y):
    global selected_button
    over_button=None
    letter_width=60
    letter_height=40
    start_game_width=150
    start_game_height=70
    for k, btn in signup_buttons.items():
        bx,by=signup_button_positions[k]
        if k in letters:
            bw,bh=letter_width,letter_height
        else:
            bw,bh=start_game_width,start_game_height
        if (bx - bw/2)<=x<=(bx+bw/2) and (by - bh/2)<=y<=(by+bh/2):
            over_button=k
            break

    if over_button:
        if selected_button==over_button:
            return
        reset_selection()
        hover_signup_button(over_button)
        selected_button=over_button
        start_countdown(over_button)
    else:
        reset_selection()

# Game Window
############################
def confirm_selection_game(button_key):
    global selected_button, game_active, scoreboard_data, prize_won, player_name
    if selected_button==button_key and game_active:
        prize=prizes[list(buttons.keys()).index(button_key)]
        prize_won=prize
        messagebox.showinfo("Prize",f"Congratulations {player_name}! You won {prize} TL!")
        scoreboard_data.append((player_name,prize_won))
        load_scoreboard()

def load_scoreboard():
    global scoreboard_active,game_active
    game_active=False
    scoreboard_active=True
    for w in root.winfo_children():
        w.destroy()

    sb_frame=tk.Frame(root)
    sb_frame.pack(fill='both',expand=True)
    sb_canvas=tk.Canvas(sb_frame,width=400,height=400)
    sb_canvas.pack(fill='both',expand=True)

    title=tk.Label(sb_canvas,text="Scoreboard",font=("Arial",24),fg='blue')
    sb_canvas.create_window(200,50,window=title)
    y_pos=100
    for nm,pr in scoreboard_data:
        lbl=tk.Label(sb_canvas,text=f"{nm}: {pr} TL",font=("Arial",14))
        sb_canvas.create_window(200,y_pos,window=lbl)
        y_pos+=40

def hover_game_button(button_key):
    buttons[button_key].config(bg='lightblue')

def check_cursor_over_button_game(x,y):
    global selected_button
    game_button_width=150
    game_button_height=70
    over_button=None
    for k,btn in buttons.items():
        bx,by=button_positions[k]
        bw,bh=game_button_width,game_button_height
        if (bx-bw/2)<=x<=(bx+bw/2) and (by-bh/2)<=y<=(by+bh/2):
            over_button=k
            break
    if over_button:
        if selected_button==over_button:
            return
        reset_selection()
        hover_game_button(over_button)
        selected_button=over_button
        start_countdown(over_button)
    else:
        reset_selection()

def load_game_window():
    global game_active
    game_active=True
    for w in root.winfo_children():
        w.destroy()

    g_frame=tk.Frame(root)
    g_frame.pack(fill='both',expand=True)

    gcanvas=tk.Canvas(g_frame,width=400,height=400)
    gcanvas.pack(fill='both',expand=True)

    global current_canvas, buttons, timers, button_positions, cursor, cursor_window
    current_canvas=gcanvas

    buttons={
        "left": tk.Button(gcanvas,text="?",font=("Arial",18),bg='gray'),
        "right": tk.Button(gcanvas,text="?",font=("Arial",18),bg='gray'),
        "up": tk.Button(gcanvas,text="?",font=("Arial",18),bg='gray'),
        "down": tk.Button(gcanvas,text="?",font=("Arial",18),bg='gray'),
    }
    timers={
        "left": tk.Label(gcanvas,text="",font=("Arial",12),fg='red'),
        "right": tk.Label(gcanvas,text="",font=("Arial",12),fg='red'),
        "up": tk.Label(gcanvas,text="",font=("Arial",12),fg='red'),
        "down": tk.Label(gcanvas,text="",font=("Arial",12),fg='red'),
    }
    button_positions={
        "left":(100,200),
        "right":(300,200),
        "up":(200,100),
        "down":(200,300),
    }

    game_button_width=150
    game_button_height=70
    for k in buttons:
        x,y=button_positions[k]
        gcanvas.create_window(x,y,window=buttons[k],width=game_button_width,height=game_button_height)
        gcanvas.create_window(x,y+60,window=timers[k],width=100,height=20)

    cursor=tk.Label(gcanvas,text="X",font=("Arial",12),fg='red')
    cursor_window=gcanvas.create_window(-100,-100,window=cursor)

# Countdown Control for button select times
############################
def cancel_countdown():
    global countdown_after_id, hovered_button
    if countdown_after_id is not None:
        root.after_cancel(countdown_after_id)
        countdown_after_id = None
    hovered_button = None

def start_countdown(button_key):
    global countdown_remaining, hovered_button
    hovered_button = button_key
    countdown_remaining = 3  # 3 seconds now
    update_countdown()

def update_countdown():
    global countdown_remaining, hovered_button, countdown_after_id
    if hovered_button is None:
        return
    if countdown_remaining <= 0:
        countdown_after_id = None
        confirm_selection(hovered_button)
        return
    label = get_timer_label(hovered_button)
    if label:
        label.config(text=f"{countdown_remaining}s")
    countdown_remaining -= 1
    countdown_after_id = root.after(1000, update_countdown)


# Video Processing
############################
cap=cv2.VideoCapture(0)
mp_hand=mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)

connection_drawing_spec = mp_drawing.DrawingSpec(color=(0,255,0), thickness=2, circle_radius=2)
landmark_drawing_spec = mp_drawing.DrawingSpec(color=(255,0,0), thickness=2, circle_radius=2)

def video_loop():
    if not cap.isOpened():
        messagebox.showerror("Error","Cannot access webcam.")
        root.destroy()
        return
    ret,frame=cap.read()
    if not ret:
        root.after(10,video_loop)
        return
    frame=cv2.flip(frame,1)
    rgb_frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    results=mp_hand.process(rgb_frame)

    w,h=400,400
    if results.multi_hand_landmarks:
        found_cursor=False
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS,
                landmark_drawing_spec,
                connection_drawing_spec
            )

            index_extended=is_finger_extended(hand_landmarks,'index')
            middle_extended=is_finger_extended(hand_landmarks,'middle')
            ring_extended=is_finger_extended(hand_landmarks,'ring')
            pinky_extended=is_finger_extended(hand_landmarks,'pinky')

            if index_extended and middle_extended and not ring_extended and not pinky_extended:
                ix=hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                mx=hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                cx=(ix.x+mx.x)/2
                cy=(ix.y+mx.y)/2
                sx,sy=cx*w,cy*h
                move_cursor(sx,sy)
                found_cursor=True
                break
            elif index_extended and not middle_extended and not ring_extended and not pinky_extended and (signup_screen_active or game_active):
                hide_cursor()
                reset_selection()
                found_cursor=True
                break
        if not found_cursor:
            hide_cursor()
            reset_selection()
    else:
        hide_cursor()
        reset_selection()

    cv2.imshow("Gesture Control",frame)
    if cv2.waitKey(1)&0xFF==27:
        cap.release()
        cv2.destroyAllWindows()
        root.destroy()
        return

    root.after(10,video_loop)


# Start Screen Setup
############################
start_frame = tk.Frame(root)
start_frame.pack(fill="both", expand=True)

start_canvas = tk.Canvas(start_frame, width=400, height=400)
start_canvas.pack(fill="both", expand=True)

title_label = tk.Label(start_canvas, text="CS449-LOTTERY", font=("Arial", 24), fg="blue")
start_canvas.create_window(200, 50, window=title_label)

start_buttons = {
    "start": tk.Button(start_canvas, text="Start", font=("Arial",16), bg="gray"),
    "quit": tk.Button(start_canvas, text="Quit", font=("Arial",16), bg="gray"),
}
start_timers = {
    "start": tk.Label(start_canvas,text="",font=("Arial",12),fg='red'),
    "quit": tk.Label(start_canvas,text="",font=("Arial",12),fg='red'),
}
start_button_positions={
    "start":(200,150),
    "quit":(200,250),
}

start_button_width=150
start_button_height=70
for k in start_buttons:
    x,y=start_button_positions[k]
    start_canvas.create_window(x,y,window=start_buttons[k],width=start_button_width,height=start_button_height)
    start_canvas.create_window(x,y+start_button_height/2+10,window=start_timers[k],width=100,height=20)

cursor = tk.Label(start_canvas, text="X", font=("Arial",12), fg='red')
cursor_window=start_canvas.create_window(-100,-100,window=cursor)
current_canvas=start_canvas

root.after(100,video_loop)
root.mainloop()
