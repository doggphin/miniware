from django.urls import path
from . import views

urlpatterns = [
    path('slides/<str:from_folder>/<str:to_folder>/', views.correct_slides),
    path('prints/<str:from_folder>/<str:to_folder>/', views.correct_prints),
    path('audio/<str:from_folder>/<str:to_folder>/', views.correct_audio),
]