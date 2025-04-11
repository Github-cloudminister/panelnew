from django.urls import path
from Notifications import views
from Notifications.views import *

urlpatterns = [

    path('employee-notifications',EmployeeNotificationListAPI.as_view(), name='employee_notification_view')

]