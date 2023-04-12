import datetime
import json
import base64
import requests
import subscription
from model_api_connection.models import Employee, Attendance
from django.core import serializers
from django.db import connection
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.utils import timezone
from datetime import date
from threading import Thread

employee_attendance_cache = {}
current_frame_data = {}
last_recognized_data = None


@csrf_exempt
def start_subscription(request):
    try:
        # Start the subscription loop in a separate thread
        t = Thread(target=subscription.start_subscription)
        t.start()
        return JsonResponse({'success': True, 'response': {'message': 'Subscription started successfully'}})
    except:
        return JsonResponse({'success': False, 'response': {'message': 'Error starting subscription'}})


@csrf_exempt
def stop_subscription(request):
    try:
        subscription.stop_subscription()
        return JsonResponse({'success': True, 'response': {'message': 'Subscription stopped successfully'}})
    except:
        return JsonResponse({'success': False, 'response': {'message': 'Error stopping subscription'}})


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

            return JsonResponse({'success': True, 'response': data}, safe=False)
        else:
            return JsonResponse({'success': False, 'response': {'error': 'Failed to retrieve data from FastAPI'}},
                                status=500)
    return JsonResponse({'success': False, 'response': {'error': 'Invalid request method'}}, status=400)


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
            return JsonResponse({'success': True, 'response': response_data}, safe=False)
        else:
            return JsonResponse({'success': False, 'response': {'error': 'No recognized frame available'}}, status=404)
    else:
        return JsonResponse({'success': False, 'response': {'error': 'Invalid request method'}}, status=400)


@csrf_exempt
def training_status(request):
    try:
        if request.method == 'GET':
            url = 'http://localhost:8000/training_status/'
            response = requests.get(url)

            if response.status_code == 200:
                return JsonResponse({'success': True, 'response': response.json()}, safe=False)
            else:
                return JsonResponse(
                    {'success': False, 'response': {'error': 'Error retrieving training status from FastAPI server'}})
        else:
            return JsonResponse({'success': False, 'response': {'error': 'Invalid request method'}})
    except:
        return JsonResponse({'success': False, 'response': {'error': 'Could not reach FastAPI'}})


@csrf_exempt
def train_model(request):
    try:
        if request.method == 'POST':
            url = 'http://localhost:8000/train_model/'
            response = requests.post(url)

            if response.status_code == 200:
                return JsonResponse({'success': True, 'response': response.json()}, safe=False)
            else:
                return JsonResponse({'success': False, 'error': 'Error training model on FastAPI server'})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid request method'})
    except:
        return JsonResponse({'success': False, 'response': {'error': 'Could not reach FastAPI'}})


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
            return JsonResponse(
                {'success': False, 'response': {'error': 'Employee with the same pincode already exists'}})
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
            return JsonResponse({'success': True, 'response': {'employee': data}})
        except (Employee.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'success': False, 'response': {'error': 'Employee does not exist'}})
    else:
        return JsonResponse({'success': False, 'response': {'error': 'Invalid request method'}})


@csrf_exempt
def list_employees(request):
    name = request.POST.get('name')
    surname = request.POST.get('surname')
    department = request.POST.get('department')
    pincode = request.POST.get('pincode')
    employees = Employee.objects.all()

    if name:
        employees = employees.filter(name__icontains=name)
    if surname:
        employees = employees.filter(surname__icontains=surname)
    if pincode:
        employees = employees.filter(pincode__icontains=pincode)
    if department:
        employees = employees.filter(department__icontains=department)

    data = serializers.serialize('json', employees)
    formatted_data = json.dumps(json.loads(data), indent=4)
    return HttpResponse(formatted_data, content_type='application/json')


def list_raw_attendance(request):
    attendance = Attendance.objects.all()
    data = serializers.serialize('json', attendance)
    formatted_data = json.dumps(json.loads(data), indent=4)
    return HttpResponse(formatted_data, content_type='application/json')


@csrf_exempt
def list_attendance(request):
    date_str = request.POST.get('date')
    start_date_str = request.POST.get('start_date')
    end_date_str = request.POST.get('end_date')
    name = request.POST.get('name')
    surname = request.POST.get('surname')
    pincode = request.POST.get('pincode')
    department = request.POST.get('department')

    attendance = Attendance.objects.select_related('employee')

    if date_str:
        date = datetime.datetime.fromisoformat(date_str).date()
        attendance = attendance.filter(date__date=date)
    elif start_date_str and end_date_str:
        start_date = datetime.datetime.fromisoformat(start_date_str).date()
        end_date = datetime.datetime.fromisoformat(end_date_str).date()
        attendance = attendance.filter(date__date__range=(start_date, end_date))

    if name:
        attendance = attendance.filter(employee__name__icontains=name)
    if surname:
        attendance = attendance.filter(employee__surname__icontains=surname)
    if pincode:
        attendance = attendance.filter(employee__pincode__icontains=pincode)
    if department:
        attendance = attendance.filter(employee__department__icontains=department)

    attendance = attendance.values(
        'id', 'date',
        'employee__id', 'employee__name', 'employee__surname', 'employee__patronymic',
        'employee__pincode', 'employee__department'
    )
    attendance_list = list(attendance)

    return JsonResponse({'success': True, 'response': attendance_list}, safe=False)


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
                    return JsonResponse({'success': False, 'response': {'error': "Error deleting employee's images"}})

            # Delete the employee
            employee.delete()
            return JsonResponse({'success': True, 'response': {'deleted': pincode}})
        except (Employee.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'success': False, 'response': {'error': 'Employee does not exist'}})
    else:
        return JsonResponse({'success': False, 'response': {'error': 'Invalid request method'}})


@csrf_exempt
def edit_employee(request):
    try:
        employee_id = request.POST['employee_id']
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'response': {'message': 'Employee not found'}})

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
        return JsonResponse({'success': True, 'response': {'employee': data}})


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
            return JsonResponse({'success': True, 'response': {'added images to': employee_id}})
        else:
            return JsonResponse({'success': False, 'response': {'error': 'Error uploading images to FastAPI server'}})

    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'response': {'error': 'Employee does not exist'}})

    except:
        return JsonResponse(
            {'success': False,
             'response': {'error': 'An unexpected error occurred, make sure target application is running'}})


@csrf_exempt
def delete_images(request, pincode=None):
    try:
        pincode = request.POST.get('pincode')
        try:
            employee = Employee.objects.get(pincode=pincode)
        except:
            return JsonResponse({'success': False, 'response': {'error': 'Employee not found'}})
        employee_id = employee.id
        url = f'http://localhost:8000/delete_images/?id={employee_id}'
        response = requests.post(url)
        response_json = response.json()
        message = response_json.get('message')
        return JsonResponse({'success': True, 'response': {'message': message}})
    except:
        return JsonResponse({'success': False, 'response': {'error': 'Could not reach FastAPI server'}})


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
            return JsonResponse({'success': True, 'response': response.json()})
        else:
            return JsonResponse({'success': False, 'response': {'error': 'Could not delete files'}})
    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'response': {'error': 'Employee not found'}})
    except:
        return JsonResponse({'success': False, 'response': {
            'error': 'An unexpected error occurred, make sure target application is running'}})


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
            return JsonResponse({'success': True, 'response': {'has_images': has_images}})
        else:
            return JsonResponse({'success': False, 'response': {'error': 'Could not check for images'}})
    except:
        return JsonResponse({'success': False, 'response': {'error': 'Employee not found'}})


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
            return JsonResponse({'success': True, 'response': images}, safe=False)
        else:
            return JsonResponse({'success': False, 'response': {'error': 'Could not get images'}})

    except Employee.DoesNotExist:
        return JsonResponse({'success': False, 'response': {'error': 'Employee does not exist'}})

    except:
        return JsonResponse({'success': False, 'response': {
            'error': 'An unexpected error occurred, make sure target application is running'}})


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
            return JsonResponse({'success': False, 'response': {'error': 'Employee ID is missing'}})

        # Check if the employee exists
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return JsonResponse({'success': False, 'response': {'error': 'Employee does not exist'}})

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
        return JsonResponse({'success': True, 'response': {'employee_id': employee_id, 'date': now.date()}})
    else:
        return JsonResponse({'success': False, 'response': {'error': 'Invalid request method'}})


@csrf_exempt
def get_attendance(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        try:
            employee = Employee.objects.get(id=employee_id)
            attendance_records = Attendance.objects.filter(employee=employee)
            data = serializers.serialize('json', attendance_records)
            return JsonResponse({'success': True, 'response': {'attendance': data}})
        except (Employee.DoesNotExist, ValueError, TypeError):
            return JsonResponse({'success': False, 'response': {'error': 'Employee does not exist'}})
    else:
        return JsonResponse({'success': False, 'response': {'error': 'Invalid request method'}})


@require_GET
def health_check(request):
    try:
        # Check the health of the FastAPI application
        response = requests.get('http://localhost:8000/health')
        response.raise_for_status()
        fastapi_status = True
    except:
        fastapi_status = False

    # Check the health of the Django application
    django_status = True

    # Check the health of the PostgreSQL database
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT version();')
        database_status = True
    except:
        database_status = False

    return JsonResponse({'success': True, 'response': {
        'django_status': django_status,
        'fastapi_status': fastapi_status,
        'database_status': database_status, }
                         })
