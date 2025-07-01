import cv2
import mediapipe as mp
import serial
import time
import threading
import tkinter as tk
import speech_recognition as sr
import numpy as np

# Serial Communication
try:
    arduino = serial.Serial('COM10', 9600)
    time.sleep(2)
    print("Connected to Arduino on COM10")
except:
    print("Failed to connect to Arduino. Check COM port.")
    arduino = None

# Mediapipe Setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.7)

# Global State
cap = None
current_mode = None
running = False
voice_running = False

def send_command(cmd):
    try:
        if arduino and arduino.is_open:
            print(f"Sending to Arduino: {cmd}")
            arduino.write(cmd.encode())
        else:
            print("Arduino not connected.")
    except Exception as e:
        print(f"Error sending command: {e}")

def is_fist(hand_landmarks):
    tip_ids = [8, 12, 16, 20]
    return all(hand_landmarks.landmark[tip].y > hand_landmarks.landmark[tip - 2].y for tip in tip_ids)

def is_open_palm(hand_landmarks, label):
    tip_ids = [4, 8, 12, 16, 20]
    if label == "Right":
        thumb_open = hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x
    else:
        thumb_open = hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x

    fingers = [thumb_open]
    for i in range(1, 5):
        fingers.append(hand_landmarks.landmark[tip_ids[i]].y < hand_landmarks.landmark[tip_ids[i] - 2].y)

    return fingers.count(True) == 5

def is_pinch(hand_landmarks):
    thumb_tip = hand_landmarks.landmark[4]
    index_tip = hand_landmarks.landmark[8]
    distance = ((thumb_tip.x - index_tip.x)**2 + (thumb_tip.y - index_tip.y)**2)**0.5
    return distance < 0.05

def count_fingers(hand_landmarks, label):
    tip_ids = [4, 8, 12, 16, 20]
    if label == "Right":
        thumb_open = hand_landmarks.landmark[4].x < hand_landmarks.landmark[3].x
    else:
        thumb_open = hand_landmarks.landmark[4].x > hand_landmarks.landmark[3].x

    fingers = [thumb_open]
    for i in range(1, 5):
        fingers.append(hand_landmarks.landmark[tip_ids[i]].y < hand_landmarks.landmark[tip_ids[i] - 2].y)

    return fingers.count(True)

# Modified function: Detect if wristband color matches red in ROI around wrist
def wristband_color_matches(frame, hand_landmarks):
    h, w, _ = frame.shape
    # Get wrist landmark coords (landmark 0 is wrist)
    wrist = hand_landmarks.landmark[0]
    cx, cy = int(wrist.x * w), int(wrist.y * h)
    
    # Define ROI rectangle around wrist (adjust size as needed)
    roi_size = 40
    x1 = max(cx - roi_size, 0)
    y1 = max(cy - roi_size, 0)
    x2 = min(cx + roi_size, w)
    y2 = min(cy + roi_size, h)
    
    roi = frame[y1:y2, x1:x2]
    if roi.size == 0:
        return False
    
    # Convert ROI to HSV for color detection
    hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    
    # Define color ranges in HSV for red wristband only
    # Red can have two ranges because it wraps around the hue circle
    red_lower1 = np.array([0, 120, 70])
    red_upper1 = np.array([10, 255, 255])
    red_lower2 = np.array([170, 120, 70])
    red_upper2 = np.array([180, 255, 255])
    
    # Masks
    mask_red1 = cv2.inRange(hsv_roi, red_lower1, red_upper1)
    mask_red2 = cv2.inRange(hsv_roi, red_lower2, red_upper2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    
    # Count how many pixels match red color
    red_count = cv2.countNonZero(mask_red)
    
    # Threshold for detection (adjust as needed)
    threshold = 50
    
    if red_count > threshold:
        return True
    else:
        return False

def run_camera(mode):
    global cap, running
    cap = cv2.VideoCapture(0)
    running = True
    update_status(f"Camera running in {mode} mode")

    while running:
        ret, frame = cap.read()
        if not ret:
            break

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(image_rgb)

        frame_text = "No Gesture"
        color = (255, 255, 255)

        if result.multi_hand_landmarks and result.multi_handedness:
            # Filter hands that have wristband color detected
            valid_hands = []
            valid_labels = []
            for hand_landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
                if wristband_color_matches(frame, hand_landmarks):
                    valid_hands.append(hand_landmarks)
                    valid_labels.append(handedness.classification[0].label)

            if not valid_hands:
                send_command('0')
                frame_text = "No wristband detected"
                color = (200, 200, 200)
            else:
                for hand_landmarks, label in zip(valid_hands, valid_labels):
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    if mode == "fist":
                        if is_fist(hand_landmarks):
                            send_command('R')
                            frame_text = f"{label} Fist - RED"
                            color = (0, 0, 255)
                        elif is_pinch(hand_landmarks):
                            send_command('Y')
                            frame_text = f"{label} Pinch 🤌 - YELLOW"
                            color = (0, 255, 255)
                        elif is_open_palm(hand_landmarks, label):
                            send_command('G')
                            frame_text = f"{label} Open Palm 🖐 - GREEN"
                            color = (0, 255, 0)
                        else:
                            send_command('0')
                            frame_text = "Unknown Gesture"
                            color = (200, 200, 200)

                    elif mode == "fingers":
                        finger_count = count_fingers(hand_landmarks, label)
                        if finger_count == 1:
                            send_command('R')
                            frame_text = f"{label} 1 Finger - RED"
                            color = (0, 0, 255)
                        elif finger_count == 2:
                            send_command('Y')
                            frame_text = f"{label} 2 Fingers - YELLOW"
                            color = (0, 255, 255)
                        elif finger_count == 3:
                            send_command('G')
                            frame_text = f"{label} 3 Fingers - GREEN"
                            color = (0, 255, 0)
                        else:
                            send_command('0')
                            frame_text = f"{label} {finger_count} Fingers - LED OFF"
                            color = (255, 255, 255)

                    # Only process the first valid hand found for now, comment this break if you want multiple hands
                    break

        else:
            send_command('0')

        cv2.putText(frame, frame_text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        cv2.imshow("Gesture Control", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    send_command('0')
    update_status("Camera stopped")

def voice_control():
    global voice_running
    r = sr.Recognizer()
    mic = sr.Microphone()
    voice_running = True
    update_status("Voice control running")

    with mic as source:
        r.adjust_for_ambient_noise(source)

    red_keywords = ["red", "r", "are", "aar", "arr"]
    yellow_keywords = ["yellow", "y", "why", "wye"]
    green_keywords = ["green", "g", "ji", "gee"]

    while voice_running:
        with mic as source:
            print("Listening for voice command...")
            try:
                audio = r.listen(source, timeout=5)
                command = r.recognize_google(audio).lower().strip()
                print(f"Recognized: {command}")

                matched = False

                for word in red_keywords:
                    if word in command:
                        send_command('R')
                        matched = True
                        break

                if not matched:
                    for word in yellow_keywords:
                        if word in command:
                            send_command('Y')
                            matched = True
                            break

                if not matched:
                    for word in green_keywords:
                        if word in command:
                            send_command('G')
                            matched = True
                            break

                if not matched:
                    send_command('0')

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                print("Could not understand audio")
            except sr.RequestError:
                print("Speech service error")

    update_status("Voice control stopped")
    send_command('0')

def start_mode(selected_mode):
    global current_mode, running, voice_running, cam_thread, voice_thread
    stop_all()
    current_mode = selected_mode

    if selected_mode == "fist" or selected_mode == "fingers":
        cam_thread = threading.Thread(target=run_camera, args=(selected_mode,), daemon=True)
        cam_thread.start()
    elif selected_mode == "voice":
        voice_thread = threading.Thread(target=voice_control, daemon=True)
        voice_thread.start()

def stop_all():
    global running, voice_running
    running = False
    voice_running = False

def update_status(msg):
    status_label.config(text=msg)

# GUI setup
root = tk.Tk()
root.title("Gesture & Voice LED Control")
root.geometry("400x200")

frame = tk.Frame(root)
frame.pack(pady=20)

status_label = tk.Label(root, text="Select Input Mode", font=("Arial", 14))
status_label.pack(pady=10)

btn_fist = tk.Button(frame, text="Hand Fist Gesture", command=lambda: start_mode("fist"), width=20)
btn_fingers = tk.Button(frame, text="Finger Counting", command=lambda: start_mode("fingers"), width=20)
btn_voice = tk.Button(frame, text="Voice Command", command=lambda: start_mode("voice"), width=20)
btn_stop = tk.Button(root, text="Stop All", command=stop_all, width=20, fg="red")

btn_fist.grid(row=0, column=0, padx=10, pady=5)
btn_fingers.grid(row=0, column=1, padx=10, pady=5)
btn_voice.grid(row=1, column=0, padx=10, pady=5)
btn_stop.pack(pady=10)

root.protocol("WM_DELETE_WINDOW", lambda: [stop_all(), root.destroy()])

root.mainloop()
