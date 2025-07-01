🚦 Contactless Gesture & Voice LED Control
This project uses Python, OpenCV, Mediapipe, and Arduino to control traffic LEDs through contactless hand gestures or voice commands. An authorized red wristband ensures safe, hygienic control.

📂 Files
gesture_voice_control.py

arduino_traffic_led.ino

🚀 How to Run
Upload the Arduino sketch to your Arduino Uno.

Install the required Python packages:

nginx
Copy
Edit
pip install opencv-python mediapipe speechrecognition pyserial
Check the COM port in gesture_voice_control.py and update if needed.

Run the Python program:

nginx
Copy
Edit
python gesture_voice_control.py
Select your desired input mode (fist gesture, finger counting, or voice command) in the GUI and test the system.

📝 License
MIT
