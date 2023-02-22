import time
import cv2
import requests


def subscription_loop():
    cap = cv2.VideoCapture(0)
    url = 'http://127.0.0.1:9000/model_api_connection/frame-post/'

    try:
        while True:
            ret, frame = cap.read()

            cv2.waitKey(1)
            cv2.imshow("current_frame", frame)
            if not ret:
                continue

            # Convert the frame to a byte stream
            data = cv2.imencode('.jpg', frame)[1].tobytes()
            # Send a POST request to the face detection API with the frame data
            response = requests.post(url, files={"file": data})
            if response.status_code == 200:
                print("Frame sent successfully")
            else:
                print(f"Failed to retrieve data from Django: {response.status_code}")

            # Control the rate at which frames are captured and sent to the API
            time.sleep(0.05)

    finally:
        # Release the camera and destroy the window
        cap.release()


if __name__ == '__main__':
    subscription_loop()
