import os
import time
import cv2
import requests
from concurrent.futures import ThreadPoolExecutor

is_running = False

rtsp_url = os.environ.get("RTSP_URL", "0")
url = 'http://backend:9000/model_api_connection/frame_post/'

executor = ThreadPoolExecutor(max_workers=1)


def send_frame(frame):
    data = cv2.imencode('.jpg', frame)[1].tobytes()
    response = requests.post(url, files={"file": data})

    if response.status_code == 200:
        print("Frame sent successfully")
    else:
        print(f"Failed to retrieve data from Django: {response.status_code}")


def subscription_loop():
    global is_running
    print(f"RTSP URL: {rtsp_url}")

    buffer_reset_interval = 3
    last_reset_time = time.time()

    cap = cv2.VideoCapture(rtsp_url)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Change to desired width
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Change to desired height

    try:
        while is_running:
            current_time = time.time()
            if current_time - last_reset_time >= buffer_reset_interval:
                last_reset_time = current_time
                cap.release()
                cap = cv2.VideoCapture(rtsp_url)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            ret, frame = cap.read()
            if not ret:
                continue

            key = cv2.waitKey(1) & 0xFF
            print("Frame captured")

            start_time = time.time()
            executor.submit(send_frame, frame)

            end_time = time.time()
            processing_time = end_time - start_time
            sleep_duration = 0.5
            time.sleep(sleep_duration)

            if key == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


def start_subscription():
    global is_running
    if not is_running:
        is_running = True
        subscription_loop()


def stop_subscription():
    global is_running
    if is_running:
        is_running = False


if __name__ == '__main__':
    start_subscription()
