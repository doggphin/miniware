from django.urls import path
from . import views

urlpatterns = [
    path('photo/'
         '<str:client_first_name>/'
         '<str:client_last_name>/'
         '<str:formatted_project_name>/'
         '<int:dpi>/'
         '<str:photo_type>/', 
         views.fc_photo),
    path('client_info/<str:spreadsheet_id>/', views.client_info),
    path('photo_has_corrected/<str:spreadsheet_id>/', views.photo_has_corrected),
    path('photo_info_normal_row/<str:spreadsheet_id>/<int:group_identifier>/', views.photo_info_normal_row),
    path('photo_row/<str:spreadsheet_id>/<str:group_identifier>/', views.photo_row),
    path('check_photo_row/<str:spreadsheet_id>/<str:group_identifier>/', views.check_photo_row),
    path('check_all_photo_rows/<str:spreadsheet_id>/', views.check_all_photo_rows)
]