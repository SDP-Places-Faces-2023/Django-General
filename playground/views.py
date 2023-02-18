from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt
import cv2
import requests
import time



async def get_data(request):
    data = get_data_from_fastapi(request)
    return render(request, 'template.html', {'data': data})


async def get_data_from_fastapi(request):
    url = 'http://127.0.0.1:8000/ddd/'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return JsonResponse(data)
    else:
        return JsonResponse({'error': 'Failed to retrieve data from FastAPI'}, status=500)


@csrf_exempt
def get_object_detection(request):
    if request.method == 'POST':
        url = 'http://127.0.0.1:8000/objectdetection/'
        files = {'file': request.FILES['file'].read()}
        response = requests.post(url, files=files)
        if response.status_code == 200:
            data = response.json()
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'Failed to retrieve data from FastAPI'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def get_object_classification(request):
    if request.method == 'POST':
        url = 'http://127.0.0.1:8000/predict/image'
        files = {'file': request.FILES['file'].read()}
        response = requests.post(url, files=files)
        if response.status_code == 200:
            data = response.json()
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'error': 'Failed to retrieve data from FastAPI'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

@csrf_exempt
def frame_post(request):
    if request.method == 'POST':
        url = 'http://127.0.0.1:8000/predict/'
        files = {'file': request.FILES['file'].read()}
        response = requests.post(url, files=files)
        #Get face coordinates, crop the face, send face to recognition API, return Employee ID

        if response.status_code == 200:
            data = response.json()
            return JsonResponse(data)
        else:
            return JsonResponse({'error': 'Failed to retrieve data from FastAPI'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


