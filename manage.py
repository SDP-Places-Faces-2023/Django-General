# #!/usr/bin/env python
# """Django's command-line utility for administrative tasks."""
# import os
# import sys
# import threading
# import time
# import cv2
# import requests
#
#
# def main():
#     """Run administrative tasks."""
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'generalapp.settings')
#     try:
#         from django.core.management import execute_from_command_line
#     except ImportError as exc:
#         raise ImportError(
#             "Couldn't import Django. Are you sure it's installed and "
#             "available on your PYTHONPATH environment variable? Did you "
#             "forget to activate a virtual environment?"
#         ) from exc
#     execute_from_command_line(sys.argv)
#
#
# def subscription_loop():
#     cap = cv2.VideoCapture(0)
#     url = 'http://127.0.0.1:8000/predict/'
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             continue
#
#         # Convert the frame to a byte stream
#         data = cv2.imencode('.jpg', frame)[1].tobytes()
#         # Send a POST request to the face detection API with the frame data
#         response = requests.post(url, files={"file": data})
#         if response.status_code == 200:
#             data = response.json()
#             print(data)
#         else:
#             print(f"Failed to retrieve data from face detection API. Status code: {response.status_code}")
#
#         # Control the rate at which frames are captured and sent to the API
#         time.sleep(1)
#
#     # Release the camera and destroy the window
#     cap.release()
#
#
# if __name__ == '__main__':
#     t = threading.Thread(target=subscription_loop, daemon=True)
#     t.start()
#     main()
#
# !/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import threading
import time
import cv2
import requests


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'generalapp.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)



if __name__ == '__main__':

    main()
