from django.urls import path
from . import views

urlpatterns = [
    # Endpoints for correcting all files in a folder
    path('slides/<str:from_folder>/<str:to_folder>/', views.correct_slides),
    path('prints/<str:from_folder>/<str:to_folder>/', views.correct_prints),
    path('audio/<str:from_folder>/<str:to_folder>/', views.correct_audio),
    path('vhs/<str:from_folder>/<str:to_folder>/', views.correct_vhs),
    path('all/<str:project_folder>/', views.correct_all),
    
    # Task status endpoints
    path('tasks/<str:task_id>/', views.get_task_status),
    path('tasks/', views.get_all_tasks),
]
