from django.urls import path
from . import views

urlpatterns = [
    # path('hello/', views.say_hello),
    # path('fff/', views.get_data_from_fastapi),
    # path('object-detection/', views.get_object_detection),
    # path('object-classification/', views.get_object_classification),
    # path('face-recognition/', views.get_face_recognition),
    path('frame_post/', views.frame_post)

]
