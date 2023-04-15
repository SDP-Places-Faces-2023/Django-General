import os
import time
import cv2
import requests

# Global flag to control the subscription loop
is_running = False

rtsp_url = os.environ.get("RTSP_URL", "0")


def subscription_loop():
    global is_running
    print(f"RTSP URL: {rtsp_url}")

    buffer_reset_interval = 2
    last_reset_time = time.time()

    while is_running:
        cap = cv2.VideoCapture(rtsp_url)
        url = 'http://backend:9000/model_api_connection/frame_post/'

        try:
            while is_running:
                current_time = time.time()
                if current_time - last_reset_time >= buffer_reset_interval:
                    break

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
                sleep_duration = max(1 - processing_time, 0)
                time.sleep(sleep_duration)

                if key == ord("q"):
                    break

        finally:
            cap.release()
            last_reset_time = time.time()
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
