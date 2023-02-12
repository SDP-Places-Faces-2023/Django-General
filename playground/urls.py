from django.urls import path
from . import views

urlpatterns = [
    path('hello/', views.say_hello),
    path('fff/', views.get_data_from_fastapi),
    path('objectdetection/', views.get_object_detection, name='get_object_detection_results'),
    path('objectclassification/', views.get_object_classification, name='get_object_detection_asdfasdf')

]
