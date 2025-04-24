from django.urls import path
from . import views

urlpatterns = [
    # Endpoints for correcting all files in a folder
    path('slides/<str:from_folder>/<str:to_folder>/', views.correct_slides),
    path('prints/<str:from_folder>/<str:to_folder>/', views.correct_prints),
    path('audio/<str:from_folder>/<str:to_folder>/', views.correct_audio),
    path('vhs/<str:from_folder>/<str:to_folder>/', views.correct_vhs),
    path('all/<str:project_folder>/', views.correct_all),
    
    # Endpoints for correcting single files
    path('slides/single/<str:file_path>/<str:to_folder>/', views.correct_single_slide),
    path('prints/single/<str:file_path>/<str:to_folder>/', views.correct_single_print),
    path('audio/single/<str:file_path>/<str:to_folder>/', views.correct_single_audio),
    path('vhs/single/<str:file_path>/<str:to_folder>/', views.correct_single_vhs),
]
