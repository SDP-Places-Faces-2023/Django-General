from django.urls import path
from . import views
from .views import add_employee, delete_employee, upload_images, delete_images, record_attendance, list_employees, \
    list_attendance, list_raw_attendance, edit_employee, get_employee, get_attendance, get_images, has_images, \
    delete_files

urlpatterns = [
    # path('hello/', views.say_hello),
    # path('fff/', views.get_data_from_fastapi),
    # path('object-detection/', views.get_object_detection),
    # path('object-classification/', views.get_object_classification),
    # path('face-recognition/', views.get_face_recognition),
    path('frame_post/', views.frame_post, name='frame_post'),
    path('add_employee/', add_employee, name='add_employee'),
    path('list_employees/', list_employees, name='list_employees'),
    path('get_employee/', get_employee, name='get_employee'),
    path('list_attendance/', list_attendance, name='list_attendance'),
    path('list_raw_attendance/', list_raw_attendance, name='list_raw_attendance'),
    path('delete_employee/', delete_employee, name='delete_employee'),
    path('edit_employee/', edit_employee, name='edit_employee'),
    path('upload_images/', upload_images, name='upload_images'),
    path('get_images/', get_images, name='get_images'),
    path('has_images/', has_images, name='has_images'),
    path('delete_images/', delete_images, name='delete_images'),
    path('delete_files/', delete_files, name='delete_files'),
    path('record_attendance/', record_attendance, name='record_attendance'),
    path('get_attendance/', get_attendance, name='get_attendance'),

]
