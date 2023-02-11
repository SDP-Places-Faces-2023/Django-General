from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import requests


# Create your views here.
def say_hello(request):
    return HttpResponse('EHLAJFHL')


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
