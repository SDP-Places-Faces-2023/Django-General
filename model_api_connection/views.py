import base64
import json
from django.urls import reverse
from django.http import QueryDict, HttpRequest
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from django.utils import timezone
from fastapi import UploadFile
from datetime import date

from model_api_connection.models import Employee, Attendance

employee_attendance_cache = {}


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
        url = 'http://127.0.0.1:8000/detect_recognize/'
        files = {'file': request.FILES['file'].read()}
        response = requests.post(url, files=files)

        if response.status_code == 200:
            data = response.json()
            print(data)
            if 'recognition_results' in data and 'predicted_face' in data['recognition_results']:
                employee_id = data['recognition_results']['predicted_face']

                if not has_attendance_recorded_today(employee_id):
                    attendance_data = {'employee_id': employee_id}
                    attendance_response = record_attendance(request, attendance_data)
                    attendance_response_json = json.loads(attendance_response.content)
                    data.update(attendance_response_json)

            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'error': 'Failed to retrieve data from FastAPI'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def add_employee(request):
    if request.method == 'POST':
        name = request.POST['name']
        surname = request.POST['surname']
        patronymic = request.POST['patronymic']
        department = request.POST['department']
        pincode = request.POST['pincode']
        employee = Employee(name=name, surname=surname, patronymic=patronymic, department=department,
                            pincode=pincode)
        try:
            Employee.objects.get(pincode=pincode)
            return JsonResponse({'error': 'Employee with the same pincode already exists'})
        except:
            pass
        employee.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})


@csrf_exempt
def get_employee(request):
    if request.method == 'POST':
        pincode = request.POST.get('pincode')
        try:
            employee = Employee.objects.get(pincode=pincode)
            data = serializers.serialize('json', [employee])
            return JsonResponse({'success': True, 'employee': data})
        except (Employee.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Employee does not exist'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


def list_employees(request):
    employees = Employee.objects.all()
    data = serializers.serialize('json', employees)
    formatted_data = json.dumps(json.loads(data), indent=4)
    return HttpResponse(formatted_data, content_type='application/json')


def list_attendance(request):
    attendance = Attendance.objects.all()
    data = serializers.serialize('json', attendance)
    formatted_data = json.dumps(json.loads(data), indent=4)
    return HttpResponse(formatted_data, content_type='application/json')


@csrf_exempt
def delete_employee(request):
    if request.method == 'POST':
        pincode = request.POST.get('pincode')
        try:
            employee = Employee.objects.get(pincode=pincode)
            employee.delete()
            return JsonResponse({'success': True, 'deleted': pincode})
        except (Employee.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Employee does not exist'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def edit_employee(request):
    try:
        employee_id = request.POST['employee_id']
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Employee not found'})

    if request.method == 'POST':
        name = request.POST['name']
        surname = request.POST['surname']
        patronymic = request.POST['patronymic']
        department = request.POST['department']
        pincode = request.POST['pincode']

        employee.name = name
        employee.surname = surname
        employee.patronymic = patronymic
        employee.department = department
        employee.pincode = pincode
        employee.save()

        return JsonResponse({'success': True})
    else:
        data = serializers.serialize('json', [employee, ])
        return JsonResponse({'employee': data})


@csrf_exempt
def upload_images(request):
    # Get the ID from the request parameters
    pincode = request.GET.get('pincode')
    employee = Employee.objects.get(pincode=pincode)

    employee_id = employee.id
    # Get the images from the request body
    images = request.FILES.getlist('images')

    # Build the request URL
    url = 'http://localhost:8000/upload_images/?id=' + str(employee_id)

    # Build the request data
    data = []
    for image in images:
        data.append(('images', (image.name, image.file.read(), image.content_type)))

    # Send the request
    response = requests.post(url, files=data)

    if response.status_code == 200:
        return JsonResponse({'success': True, 'added images to': employee_id})
    else:
        return JsonResponse({'success': False})


@csrf_exempt
def delete_images(request):
    # Get the ID from the request parameters
    pincode = request.GET.get('pincode')
    try:

        employee = Employee.objects.get(pincode=pincode)

        employee_id = employee.id

        # Build the request URL
        url = 'http://localhost:8000/delete_images/?id=' + str(employee_id)

        response = requests.post(url)
        response_json = response.json()
        message = response_json.get('message')
        return JsonResponse({'message': message})

    except:
        return JsonResponse({'error': 'Could not reach FastAPI server'})


@csrf_exempt
def has_images(request):
    pincode = request.GET.get('pincode')
    employee = Employee.objects.get(pincode=pincode)
    employee_id = employee.id
    url = 'http://localhost:8000/has_images/?id=' + str(employee_id)

    response = requests.get(url)

    if response.status_code == 200:
        has_images = response.json().get('has_images')
        return JsonResponse({'has_images': has_images})
    else:
        return JsonResponse({'error': 'Could not check for images'})


@csrf_exempt
def get_images(request):
    # Get the ID from the request parameters
    pincode = request.GET.get('pincode')
    employee = Employee.objects.get(pincode=pincode)

    employee_id = employee.id

    # Build the request URL
    url = 'http://localhost:8000/get_images/?id=' + str(employee_id)

    # Send the request
    response = requests.get(url)

    if response.status_code == 200:
        # Parse the response as a dictionary of image filenames and their corresponding Base64-encoded strings
        encoded_images = response.json()

        # Build HTML img tags for each image file
        img_tags = []
        for image_filename, encoded_image in encoded_images.items():
            img_tags.append(f'<img src="data:image/{image_filename.split(".")[-1]};base64,{encoded_image}"/>')

        # Join the img tags into a single string and return it in a JsonResponse
        return JsonResponse({'images': '\n'.join(img_tags)})
    else:
        return JsonResponse({'error': 'Could not get images'})


def has_attendance_recorded_today(employee_id):
    global employee_attendance_cache
    now = timezone.now().date()

    # Check the cache
    cached_value = employee_attendance_cache.get(employee_id)
    if isinstance(cached_value, date) and cached_value == now:
        return True

    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return False

    existing_attendance_records = Attendance.objects.filter(employee=employee, date=now)

    if existing_attendance_records.exists():
        employee_attendance_cache[employee_id] = now
        return True

    # Update the cache with None to avoid unnecessary database queries
    employee_attendance_cache[employee_id] = None
    return False


@csrf_exempt
def record_attendance(request, attendance_data=None):
    if request.method == 'POST' or attendance_data:
        employee_id = attendance_data['employee_id'] if attendance_data else request.POST.get('employee_id')
        if not employee_id:
            return JsonResponse({'success': False, 'error': 'Employee ID is missing'})

        # Check if the employee exists
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Employee does not exist'})

        # Get the current date and time
        now = timezone.now()

        # Check if an attendance record already exists for this employee and date
        existing_attendance_records = Attendance.objects.filter(employee=employee, date__date=now.date())
        if existing_attendance_records.exists():
            return JsonResponse({'success': False, 'error': 'Attendance already recorded for this employee today'})

        # Save the attendance record to the database
        attendance_record = Attendance(employee=employee, date=now.date())
        attendance_record.save()

        # Update the employee_attendance_cache
        employee_attendance_cache[employee_id] = now.date()
        print(employee_attendance_cache)
        return JsonResponse({'success': True, 'employee_id': employee_id, 'date': now.date()})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def get_attendance(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        try:
            employee = Employee.objects.get(id=employee_id)
            attendance_records = Attendance.objects.filter(employee=employee)
            data = serializers.serialize('json', attendance_records)
            return JsonResponse({'success': True, 'attendance': data})
        except (Employee.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Employee does not exist'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
