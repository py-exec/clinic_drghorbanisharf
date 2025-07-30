from django.urls import path
from . import views

app_name = "backup"

urlpatterns = [
    path('manual/', views.manual_backup_view, name='manual_backup'),
]