from django.urls import path
from . import views

urlpatterns = [
    path('manualFinalCheck/<str:folder_path>/', views.manual_final_check),
    path('deleteFiles/<str:folder_path>/', views.delete_files),
]
