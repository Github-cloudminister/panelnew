from django.urls import path
from AutomationAPI.tasks import *
from backup.views import Backupdata

app_name = "backup"

urlpatterns = [

    path('backupdata', Backupdata.as_view(), name="Backupdata"),
]