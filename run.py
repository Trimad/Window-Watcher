import pygetwindow as gw
import pyautogui
import pyscreeze
from flask import Flask, request, jsonify
import requests
from io import BytesIO
import threading

app = Flask(__name__)

def take_screenshot_of_window(window_title):
    try:
        # Find the window by title
        window = gw.getWindowsWithTitle(window_title)[0]

        if window:
            # Bring the window to the foreground
            window.activate()

            # Take a screenshot
            screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))

            return screenshot
        else:
            return None

    except Exception as e:
        print(f'An error occurred: {e}')
        return None

def send_screenshot():
    screenshot = take_screenshot_of_window("Genesys Cloud")

    if screenshot is not None:
        img_byte_arr = BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        url = 'http://192.168.1.3:5001/receive_screenshot'
        files = {'screenshot': ('screenshot.png', img_byte_arr, 'image/png')}
        response = requests.post(url, files=files)

        if response.status_code == 200:
            print("Screenshot sent successfully")
        else:
            print("Failed to send screenshot")
    else:
        print("Failed to take screenshot")

    # Schedule the next call
    threading.Timer(60, send_screenshot).start()

@app.route('/')
def index():
    return "Screenshot service is running."

if __name__ == "__main__":
    threading.Timer(60, send_screenshot).start()
    app.run(port=5001, debug=True)
