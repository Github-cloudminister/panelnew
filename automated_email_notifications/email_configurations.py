# ***************** Django Libraris *****************
from django.http import JsonResponse

# ***************** in-project imports *****************
from Project.models import *
from Surveyentry.custom_function import get_object_or_none

# third-party Libraries
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient



def sendEmailSendgripAPIIntegration(*args,**kwargs):

    try:
        from_email = kwargs['from_email']
    except:
        from_email = ('noreply@panelviewpoint.com','noreply')
    
    message = Mail(
        from_email = from_email,
        to_emails = kwargs['to_emails'],
        # to_emails = ['projectmanagement@panelviewpoint.com'],
        subject = kwargs['subject'],
        html_content = kwargs['html_message']
        )
    
    try:
        message.add_cc(kwargs['cc_emails'])
    except:
        pass

    try:
        message.add_cc(kwargs['proj_manager_cc_email'])
    except:
        pass

    try:
        message.attachment = kwargs['attachedFile']
    except:
        pass
        
    try:
        sg = SendGridAPIClient('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')
        response = sg.send(message)
        return JsonResponse({'message': 'Emails sent successfully in email confuguration..!'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

