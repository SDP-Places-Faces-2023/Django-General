import datetime
import json
from threading import Thread
import base64
from django.core import serializers
from django.db import connection
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from django.utils import timezone
from datetime import date

from django.views.decorators.http import require_GET

import subscription
from model_api_connection.models import Employee, Attendance

employee_attendance_cache = {}
current_frame_data = {}
last_recognized_data = None


@csrf_exempt
def start_subscription(request):
    try:
        # Start the subscription loop in a separate thread
        t = Thread(target=subscription.start_subscription)
        t.start()
        return JsonResponse({'status': 'success', 'message': 'Subscription started successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error starting subscription: {str(e)}'})


@csrf_exempt
def stop_subscription(request):
    try:
        subscription.stop_subscription()
        return JsonResponse({'status': 'success', 'message': 'Subscription stopped successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error stopping subscription: {str(e)}'})


@csrf_exempt
def frame_post(request):
    global last_recognized_data
    global current_frame_data
    if request.method == 'POST':
        url = 'http://127.0.0.1:8000/detect_recognize/'
        file_data = request.FILES['file'].read()
        files = {'file': file_data}
        current_frame_data = file_data
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
                recognition_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                last_recognized_data = {
                    'frame': file_data,
                    'employee_id': employee_id,
                    'recognition_time': recognition_time
                }

            return JsonResponse(data, safe=False)
        else:
            return JsonResponse({'error': 'Failed to retrieve data from FastAPI'}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def get_frame(request):
    global last_recognized_data
    global current_frame_data

    if request.method == 'GET':
        if last_recognized_data:
            # Convert the last recognized frame to a base64 string without any tags
            last_frame_base64 = base64.b64encode(last_recognized_data['frame']).decode('utf-8').replace('\n', '')

            # Get the recognition timestamp
            recognition_time = last_recognized_data['recognition_time']

            # Convert the current frame data to a base64 string without any tags
            current_frame_base64 = base64.b64encode(current_frame_data).decode('utf-8').replace('\n', '')

            response_data = {
                'last_recognized_frame': last_frame_base64,
                'last_employee_id': last_recognized_data['employee_id'],
                'current_frame': current_frame_base64,
                'timestamp': recognition_time
            }
            return JsonResponse(response_data, safe=False)
        else:
            return JsonResponse({'error': 'No recognized frame available'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def training_status(request):
    if request.method == 'GET':
        url = 'http://localhost:8000/training_status/'
        response = requests.get(url)

        if response.status_code == 200:
            return JsonResponse(response.json(), safe=False)
        else:
            return JsonResponse({'success': False, 'error': 'Error retrieving training status from FastAPI server'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


@csrf_exempt
def train_model(request):
    if request.method == 'POST':
        url = 'http://localhost:8000/train_model/'
        response = requests.post(url)

        if response.status_code == 200:
            return JsonResponse(response.json(), safe=False)
        else:
            return JsonResponse({'success': False, 'error': 'Error training model on FastAPI server'})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})


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


def list_raw_attendance(request):
    attendance = Attendance.objects.all()
    data = serializers.serialize('json', attendance)
    formatted_data = json.dumps(json.loads(data), indent=4)
    return HttpResponse(formatted_data, content_type='application/json')


def list_attendance(request):
    attendance = Attendance.objects.select_related('employee').values(
        'id', 'date',
        'employee__id', 'employee__name', 'employee__surname', 'employee__patronymic',
        'employee__pincode', 'employee__department'
    )
    attendance_list = list(attendance)
    return JsonResponse(attendance_list, safe=False)


@csrf_exempt
def delete_employee(request):
    if request.method == 'POST':
        pincode = request.POST.get('pincode')
        try:
            employee = Employee.objects.get(pincode=pincode)

            # Check if the employee has images
            has_images_response = has_images(request, pincode)
            has_images_data = json.loads(has_images_response.content)

            if has_images_data.get('has_images'):
                # Delete the employee's images
                delete_images_response = delete_images(request, pincode)
                delete_images_data = json.loads(delete_images_response.content)

                if not delete_images_data.get('success', False):
                    return JsonResponse({'success': False, 'error': "Error deleting employee's images"})

            # Delete the employee
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
    try:
        # Get the ID from the request parameters
        pincode = request.GET.get('pincode')
        employee = Employee.objects.get(pincode=pincode)

        employee_id = employee.id
        # Get the images from the request body
        images = request.FILES.getlist('images')

        # Build the request URL
        url = f'http://localhost:8000/upload_images/?id={employee_id}'

        # Build the request data
        data = []
        for image in images:
            data.append(('images', (image.name, image.file.read(), image.content_type)))

        # Send the request
        response = requests.post(url, files=data)

        if response.status_code == 200:
            return JsonResponse({'success': True, 'added images to': employee_id})
        else:
            return JsonResponse({'success': False, 'error': 'Error uploading images to FastAPI server'})

    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Employee does not exist'})

    except Exception as e:
        return JsonResponse({'success': False, 'error': f'An unexpected error occurred: {str(e)}'})


@csrf_exempt
def delete_images(request, pincode=None):
    try:
        pincode = request.POST.get('pincode')
        employee = Employee.objects.get(pincode=pincode)
        employee_id = employee.id
        url = f'http://localhost:8000/delete_images/?id={employee_id}'
        response = requests.post(url)
        response_json = response.json()
        message = response_json.get('message')
        return JsonResponse({'success': True, 'message': message})
    except:
        return JsonResponse({'success': False, 'error': 'Could not reach FastAPI server'})


@csrf_exempt
def delete_files(request):
    try:
        pincode = request.POST.get('pincode')
        filenames = request.POST.getlist('filenames')
        employee = Employee.objects.get(pincode=pincode)
        employee_id = employee.id
        str_id = f'{employee_id}'
        # FastAPI endpoint URL
        fastapi_url = f"http://localhost:8000/delete_files/?id={str_id}"
        print(str_id)
        # Send a POST request to the FastAPI endpoint with the filenames
        payload = filenames
        response = requests.post(fastapi_url, data=json.dumps(payload))

        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse({'error': 'Could not delete files'})
    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee not found'})
    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'})


@csrf_exempt
def has_images(request, pincode=None):
    try:
        pincode = request.POST.get('pincode')
        employee = Employee.objects.get(pincode=pincode)
        employee_id = employee.id
        url = f'http://localhost:8000/has_images/?id={employee_id}'
        response = requests.get(url)

        if response.status_code == 200:
            has_images = response.json().get('has_images')
            return JsonResponse({'has_images': has_images})
        else:
            return JsonResponse({'error': 'Could not check for images'})
    except:
        return JsonResponse({'error': 'Employee not found'})


@csrf_exempt
def get_images(request):
    try:
        # Get the ID from the request parameters
        pincode = request.GET.get('pincode')
        employee = Employee.objects.get(pincode=pincode)

        employee_id = employee.id

        # Build the request URL
        url = f'http://localhost:8000/get_images/?id={employee_id}'

        # Send the request
        response = requests.get(url)

        if response.status_code == 200:
            # Parse the response as a dictionary of image filenames and their corresponding Base64-encoded strings
            encoded_images = response.json()

            # Build a list of dictionaries containing the filename and image data
            images = []
            for filename, data in encoded_images.items():
                images.append({
                    'filename': filename,
                    'image': data,
                })

            # Return the list of images as a JsonResponse
            return JsonResponse(images, safe=False)
        else:
            return JsonResponse({'error': 'Could not get images'})

    except Employee.DoesNotExist:
        return JsonResponse({'error': 'Employee does not exist'})

    except Exception as e:
        return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'})


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


@require_GET
def health_check(request):
    try:
        # Check the health of the FastAPI application
        response = requests.get('http://localhost:8000/health')
        response.raise_for_status()
        fastapi_status = 'ok'
    except:
        fastapi_status = 'error'

    # Check the health of the Django application
    django_status = 'ok'

    # Check the health of the PostgreSQL database
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT 1')
        database_status = 'ok'
    except:
        database_status = 'error'

    return JsonResponse({
        'django_status': django_status,
        'fastapi_status': fastapi_status,
        'database_status': database_status,
    })
