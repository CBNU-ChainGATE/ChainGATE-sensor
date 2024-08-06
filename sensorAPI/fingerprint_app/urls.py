from django.urls import path
from . import views

urlpatterns = [
    path('enroll/', views.enroll_finger, name='enroll_finger'),
    path('find/', views.find_finger, name='find_finger'),
    path('delete/', views.delete_finger, name='delete_finger'),
    path('clear/', views.clear_library, name='clear_library'),
    path('save_image/', views.save_fingerprint_image, name='save_fingerprint_image'),
]

