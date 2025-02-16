from django.urls import path
from . import views

urlpatterns = [
    path('photo/', views.corr_photo)
]