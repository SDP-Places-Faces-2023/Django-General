import uuid

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt
import cv2
import requests
import time

from model_api_connection.models import Employee


# These views are not necessary for now
#
# async def get_data(request):
#     data = get_data_from_fastapi(request)
#     return render(request, 'template.html', {'data': data})
#
#
# async def get_data_from_fastapi(request):
#     url = 'http://127.0.0.1:8000/ddd/'
#     response = requests.get(url)
#     if response.status_code == 200:
#         data = response.json()
#         return JsonResponse(data)
#     else:
#         return JsonResponse({'error': 'Failed to retrieve data from FastAPI'}, status=500)
#
#
# @csrf_exempt
# def get_object_detection(request):
#     if request.method == 'POST':
#         url = 'http://127.0.0.1:8000/objectdetection/'
#         files = {'file': request.FILES['file'].read()}
#         response = requests.post(url, files=files)
#         if response.status_code == 200:
#             data = response.json()
#             return JsonResponse(data)
#         else:
#             return JsonResponse({'error': 'Failed to retrieve data from FastAPI'}, status=500)
#     return JsonResponse({'error': 'Invalid request method'}, status=400)
#
#
# @csrf_exempt
# def get_object_classification(request):
#     if request.method == 'POST':
#         url = 'http://127.0.0.1:8000/predict/image'
#         files = {'file': request.FILES['file'].read()}
#         response = requests.post(url, files=files)
#         if response.status_code == 200:
#             data = response.json()
#             return JsonResponse(data, safe=False)
#         else:
#             return JsonResponse({'error': 'Failed to retrieve data from FastAPI'}, status=500)
#     return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def frame_post(request):
    if request.method == 'POST':
        url = 'http://127.0.0.1:8000/detect_faces/'
        # The url of the CNN model
        # url_face = 'http://127.0.0.1:8000/predict/'
        # The url of the LBPH model
        url_face = 'http://127.0.0.1:8000/recognize_faces/'
        files = {'file': request.FILES['file'].read()}
        response = requests.post(url, files=files)

        if response.status_code == 200:
            data = response.json()
            print(data)
            if data != "No Face":
                rec_response = requests.post(url_face, files=files)
                face_data = rec_response.json()
                print(data, face_data)
                return JsonResponse(face_data, safe=False)
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'error': 'Failed to retrieve data from FastAPI'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def add_employee(request):
    if request.method == 'POST':
        name = request.POST['name']
        surname = request.POST['surname']
        fathers_name = request.POST['fathers_name']
        department = request.POST['department']
        pincode = request.POST['pincode']
        employee = Employee(name=name, surname=surname, fathers_name=fathers_name, department=department,
                            pincode=pincode)
        employee.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})


@csrf_exempt
def delete_employee(request):
    if request.method == 'POST':
        emp_id = request.POST.get('id')
        try:
            employee = Employee.objects.get(id=str(emp_id))
            employee.delete()
            return JsonResponse({'success': True, 'deleted': emp_id})
        except (Employee.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Employee does not exist'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def upload_images_view(request):
    # Get the ID from the request parameters
    id = request.GET.get('id')

    # Get the images from the request body
    images = request.FILES.getlist('images')

    # Build the request URL
    url = 'http://localhost:8000/upload_images/?id=' + id
    # Build the request data
    data = []
    for image in images:
        data.append(('images', (image.name, image.file.read(), image.content_type)))

    # Send the request
    response = requests.post(url, files=data)

    # Check if the request was successful
    if response.status_code == 200:
        return JsonResponse({'success': True, 'added images to': id})
    else:
        return JsonResponse({'success': False})
