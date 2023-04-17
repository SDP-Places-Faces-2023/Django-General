import os
import time
import cv2
import requests


is_running = False

rtsp_url = os.environ.get("RTSP_URL", "0")
url = 'http://backend:9000/model_api_connection/frame_post/'


def subscription_loop():
    global is_running
    print(f"RTSP URL: {rtsp_url}")

    buffer_reset_interval = 1
    last_reset_time = time.time()

    cap = cv2.VideoCapture(rtsp_url)

    # Wait for the first successful RTSP connection and frame capture
    while True:
        ret, _ = cap.read()
        if ret:
            break
        print("Waiting for RTSP connection...")
        time.sleep(0.05)

    try:
        while is_running:
            cap = cv2.VideoCapture(rtsp_url)
            ret, frame = cap.read()
            if not ret:
                continue

            key = cv2.waitKey(1) & 0xFF
            print("Frame captured")

            start_time = time.time()
            data = cv2.imencode('.jpg', frame)[1].tobytes()
            response = requests.post(url, files={"file": data})

            if response.status_code == 200:
                print("Frame sent successfully")
            else:
                print(f"Failed to retrieve data from Django: {response.status_code}")

            end_time = time.time()
            processing_time = end_time - start_time
            sleep_duration = 0.05
            time.sleep(sleep_duration)

            if key == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
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
