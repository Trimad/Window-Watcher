import argparse
import logging
import pygetwindow as gw
import pyautogui
from flask import Flask
import requests
from io import BytesIO
import threading
import time
import signal
import os
import pygame.mixer



# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Take screenshots of a window and send them with a custom prompt every N seconds")
    parser.add_argument('--prompt', type=str, required=True, help='The prompt to send along with the screenshots')
    parser.add_argument('--window', type=str, required=True, help='The name of the window to capture')
    parser.add_argument('--seconds', type=int, required=True, help='Interval in seconds between each screenshot')
    parser.add_argument('--url', type=str, required=True, help='The URL of the server to send screenshots')
    return parser.parse_args()

def take_screenshot_of_window(window_title):
    try:
        window = gw.getWindowsWithTitle(window_title)[0]
        if window:
            window.activate()
            return pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))
        else:
            return None
    except Exception as e:
        logging.error(f'An error occurred while taking screenshot: {e}')
        return None

def play_alert_sound():
    try:
        pygame.mixer.init()  # Initialize only the mixer module
        pygame.mixer.music.load('alert.mp3')
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():  # Wait for the audio to finish playing
            pygame.time.wait(100)  # Waiting in a non-blocking way
    except Exception as e:
        logging.error(f"Error playing alert sound: {e}")

        
def send_screenshot(window_name, prompt, server_url):
    screenshot = take_screenshot_of_window(window_name)
    if screenshot:
        img_byte_arr = BytesIO()
        screenshot.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        files = {'image': ('screenshot.png', img_byte_arr, 'image/png')}
        data = {'prompt': prompt}

        try:
            response = requests.post(server_url, files=files, data=data)
            if response.status_code == 200:
                response_json = response.json()  # Parse the response as JSON
                logging.info(f"Server Response: {response_json}")
                print(f"Actual Response Text: {response_json}")  # Print the JSON response
                if response_json.get("text") != "0":  # Check the value of the "text" key
                    play_alert_sound()  # Play the alert sound if the response text is "0"
            else:
                logging.error(f"Failed to send screenshot: Status Code {response.status_code}")
                try:
                    response_data = response.json()
                    logging.error(f"Error Detail: {response_data.get('error', 'No detailed error message provided.')}")
                except ValueError:
                    logging.error("Error Detail: Response did not contain JSON.")
        except requests.exceptions.RequestException as e:
            logging.error(f"An error occurred while making the request: {e}")
    else:
        logging.error("Failed to take screenshot of the specified window.")


def continuous_screenshot(window_name, prompt, seconds, server_url):
    while True:
        send_screenshot(window_name, prompt, server_url)
        time.sleep(seconds)

@app.route('/')
def index():
    return "Screenshot service is running."

def signal_handler(signal, frame):
    logging.info("Signal received, stopping the application.")
    os._exit(0)

if __name__ == "__main__":
    args = parse_args()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    thread = threading.Thread(target=continuous_screenshot, args=(args.window, args.prompt, args.seconds, args.url))
    thread.start()
    app.run(port=5001, debug=False)
