from django.shortcuts import render

from automated_email_notifications.email_configurations import sendEmailSendgripAPIIntegration
from .models import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import  status
from knox.auth import TokenAuthentication
# Create your views here.



class EmailTemplateView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        email_obj = EmailTemplateData.objects.all().values()

        return Response(email_obj)
    

    def post(self, request):
        data = request.data

        template_name = data.get('template_name')
        subject_line = data.get('subject_line')
        template_body = data.get('template_body')

        if template_name in ['',None] or subject_line in ['', None] or template_body in ['', None]:
            return Response({"error":"All fields are required.!"})
        
        else:
            email_template_create = EmailTemplateData.objects.create(
                template_name = template_name,
                subject_line = subject_line,
                template_body = template_body,
                created_by = self.request.user
            )
            
            return Response({"success":"Email template create successfully..!"})
        

class EditEmailTemplate(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, email_template_id):

        email_obj = EmailTemplateData.objects.filter(id = email_template_id).values()

        return Response(email_obj)
    

    def put(self, request, email_template_id):
        data = request.data

        template_name = data.get('template_name')
        subject_line = data.get('subject_line')
        template_body = data.get('template_body')

        email_template_obj = EmailTemplateData.objects.get(id = email_template_id)
        email_template_obj.template_name = template_name
        email_template_obj.subject_line = subject_line
        email_template_obj.template_body = template_body
        email_template_obj.modified_by = self.request.user
        email_template_obj.save()

        return Response({"message":"Email Template Update Successfully.!"})



class MassEmailSendAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        data = request.data

        to_emails = data.get('to_emails')
        cc_emails = data.get('cc_emails')
        subject_line = data.get('subject_line')
        template_body = data.get('template_body')

        try:
            # email_obj = EmailTemplateData.objects.get(id = email_template)

            # if settings.SERVER_TYPE == 'production':
            #         cc_emails = 'projectmanagement@panelviewpoint.com'
            # else:
            #     cc_emails = 'pythonteam@slickservices.in'
            
            # email_sent_successfully = True
            # subject = f'Final Ids - PANEL VIEWPOINT: {sup.supplier_name} - {timezone.now().date()}'
            for emails in to_emails:
                sendEmail = sendEmailSendgripAPIIntegration(from_email = ('invitations@panelviewpoint.com', 'Survey Invitations'),to_emails=emails, subject=subject_line, html_message=template_body, cc_emails = self.request.user.email)

            if sendEmail.status_code in [200, 201]:
                return Response({"message":"Email Invitation Send Successfully.!"})
            
            else:
                return Response({"error":f"{sendEmail.status_code}"})

        except Exception as e:
            return Response({"error":"Email Template given by id does not exists.!"}) 

