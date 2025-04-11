from django.urls import path
from email_template_app.views import *


app_name = "email_template_app"

urlpatterns = [

    path('email-template', EmailTemplateView.as_view()),
    path('edit/email-template/<int:email_template_id>',EditEmailTemplate.as_view()),

    path('mass-email-send',MassEmailSendAPI.as_view()),

]