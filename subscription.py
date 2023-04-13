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
    cap = cv2.VideoCapture(rtsp_url)
    url = 'http://backend:9000/model_api_connection/frame_post/'

    try:
        while is_running:
            ret, frame = cap.read()
            if not ret:
                continue
            key = cv2.waitKey(1) & 0xFF

            print("Frame captured")
            # Convert the frame to a byte stream
            data = cv2.imencode('.jpg', frame)[1].tobytes()
            # Send a POST request to the face detection API with the frame data
            response = requests.post(url, files={"file": data})

            if response.status_code == 200:
                print("Frame sent successfully")
            else:
                print(f"Failed to retrieve data from Django: {response.status_code}")

            # Check for the window close event and exit the loop if the window is closed
            if key == ord("q"):
                break

            # Control the rate at which frames are captured and sent to the API
            time.sleep(0.05)

    finally:
        # Release the camera and destroy the window
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
