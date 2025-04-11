import os
from celery import Celery
from celery.schedules import crontab
from django.apps import apps 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

app = Celery('myproject')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks(lambda: [n.name for n in apps.get_app_configs()])

app.conf.beat_schedule = {

    'ClientAcceptSurveyTolunaFetchList':{
        'task': 'AutomationAPI.tasks.ClientSurveyFetchAPI',
        'schedule': crontab(minute="*/15"),
    },
    'DeleteAllPast3MonthsLogs':{
        'task': 'AutomationAPI.tasks.DeletePast3MonthsLogs',
        'schedule': crontab(day_of_month="1"),
    },
    'SurveyPrioritySet':{
        'task': 'AutomationAPI.tasks.survey_priority_set',
        'schedule': crontab(minute="*/10"),
    },
    'FinalIdsSendTwiceInWeek':{
        'task': 'AutomationAPI.tasks.FinalIdsSendTwiceInWeekAPI',
        'schedule': crontab(hour=0, minute=1, day_of_week=0),
    },
    'DailyWorkStatusEmail':{
        'task': 'AutomationAPI.tasks.DailyWorkStatusEmail',
        'schedule': crontab(hour=0, minute=1),
    }
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
