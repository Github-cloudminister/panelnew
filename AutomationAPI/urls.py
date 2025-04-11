from django.urls import path
from AutomationAPI.tasks import *

app_name = "AutomationAPI"

urlpatterns = [

    path('client-surveys-pull', ClientSurveyFetchAPI),

    path('final-ids-send', FinalIdsSendTwiceInWeekAPI),

    path('daily-work-status-email', DailyWorkStatusEmail),

]