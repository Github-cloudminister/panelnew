from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from knox.auth import TokenAuthentication
from SupplierInviteOnProject.models import *
from SupplierInviteOnProject.serializers import *
from Surveyentry.custom_function import get_object_or_none
from Surveyentry.models import RespondentDetail
from automated_email_notifications.supplier_invite_custom_functions import *

# Create your views here.
class SupplierInvoiceView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 

    def post(self, request, project_number, *args, **kwargs):
        data = request.data

        invalid_data = []
        is_valid = True

        incidence = data.get('incidence', '')
        loi = data.get('loi', '')
        country = data.get('country', '')
        message = data.get('message', '')
        supplier_invite_detail = data.get('supplier_invite_detail', [])

        if incidence in ['', None]:
            is_valid = False
        if loi in ['', None]:
            is_valid = False
        if country in ['', None, [], ['']]:
            is_valid = False
        if message in ['', None]:
            is_valid = False
        if supplier_invite_detail in ['', None, [''], []]:
            is_valid = False

        if is_valid:
            project_obj = Project.objects.filter(project_number=project_number, project_status__in=['Booked', 'Live', 'Paused']).exists()
            if not project_obj:
                return Response({'error': 'Project is not Booked, Live or Paused..!'}, status=status.HTTP_400_BAD_REQUEST)
            
            for supplier_invite in data['supplier_invite_detail']:
                supplier_org = supplier_invite.get('supplier_org', '')
                supplier_contact = supplier_invite.get('supplier_contact', '')
                budget = supplier_invite.get('budget', '')
                completes = supplier_invite.get('completes', '')
                if supplier_org in ['', None]:
                    is_valid = False
                if supplier_contact in ['', None]:
                    is_valid = False
                if budget in ['', None]:
                    is_valid = False
                if completes in ['', None]:
                    is_valid = False
                    
                if not is_valid:
                    break

                if is_valid:
                    had_supplier = ProjectGroupSupplier.objects.filter(supplier_org__id = supplier_org, project_group__project__project_number=project_number).exists()

                    if had_supplier:
                        invalid_data.append(supplier_invite)
                        data['supplier_invite_detail'].remove(supplier_invite)

        if not is_valid:
            return Response({'error':"All fields are required...!"}, status=status.HTTP_400_BAD_REQUEST)

        email_invite_sent_count = len(data['supplier_invite_detail'])
        
        if not isinstance(country, list):
            data['country'] = country.split(',')
            
        t = sendSupplierInviteOnProject(data=data,project_number=project_number)
                

        return Response({'msg':'Supplier Invite sent successfully..!', 'email_invite_sent_to_supplier':email_invite_sent_count, 'duplicates_count':len(invalid_data), 'duplicates':invalid_data}, status=status.HTTP_201_CREATED)


class SuppliersReminderView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, project_number):
        data = request.data
        supplier_remind_detail = data.get('supplier_remind_detail', [])
        project_obj = Project.objects.filter(project_number=project_number, project_status__in=['Booked', 'Live', 'Paused'])
        if not project_obj.exists():
            return Response({'error': 'Project is not Booked, Live or Paused'}, status=status.HTTP_400_BAD_REQUEST)
        
        if supplier_remind_detail in ['', None, [''], []]:
            return Response({'error':"All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            for supplier_detail_dict in supplier_remind_detail:
                if supplier_detail_dict['supplier_org'] in ['', None] or supplier_detail_dict['supplier_contact'] in ['', None, [''], []] or supplier_detail_dict['message'] in ['', None]:
                    return Response({'error':"All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

                # The counts of qs will always be the same of project_grp_supp_qs & resp_stats_surveyWise
                supplier_org_obj = SupplierOrganisation.objects.get(id=supplier_detail_dict['supplier_org'])
                project_grp_supp_qs = ProjectGroupSupplier.objects.filter(supplier_org_id=supplier_detail_dict['supplier_org'])
                project_group_numbers = [item.project_group.project_group_number for item in project_grp_supp_qs]
                resp_stats_surveyWise = RespondentDetail.objects.filter(source=supplier_detail_dict['supplier_org'], project_group_number__in=project_group_numbers, url_type='Live').values('project_group_number').annotate(completes=Count('id', filter=Q(resp_status='4')), visits=Count('id'), incompletes=Count('id',filter=Q(resp_status='3')), terminates=Count('resp_status',filter=Q(resp_status='5')),quota_full=Count('resp_status',filter=Q(resp_status='6')), security_terminate=Count('resp_status',filter=Q(resp_status='7'))
                )

                supplier_stats_list = zip(project_grp_supp_qs,resp_stats_surveyWise)

                html_message = render_to_string('SupplierInviteOnProject/email_reminder.html', {
                    'supplier_stats_list': supplier_stats_list,
                    'message': supplier_detail_dict['message']
                })

                supplier_contact_list = SupplierContact.objects.filter(supplier_id=supplier_detail_dict['supplier_org'], id__in=supplier_detail_dict['supplier_contact'].split(','), send_supplier_updates=True)
                supplier_contact_email_list = list(supplier_contact_list.values_list('supplier_email', flat=True))

                from_email = 'supply@panelviewpoint.com'
                to_emails = supplier_contact_email_list
                subject=f'RFQ || {project_obj[0].project_number} | {supplier_org_obj.supplier_name}'

                if settings.SERVER_TYPE == 'production':
                    cc_emails = 'projects@panelviewpoint.com'
                else:
                    cc_emails = 'tech@panelviewpoint.com'

                sendEmailSendgripAPIIntegration.delay(from_email=from_email,to_emails=to_emails, subject=subject, html_message=html_message, cc_emails = cc_emails, proj_manager_cc_email=project_obj[0].project_manager.email)

        return Response({'msg':'Supplier Update Reminder sent successfully'}, status=status.HTTP_200_OK)


class SuppliersMidfieldUpdateView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SuppliersMidfieldUpdateSerializer

    def get(self, request, project_group_number):
        progrp_supp = ProjectGroupSupplier.objects.filter(project_group__project_group_number=project_group_number)
        serializer = self.serializer_class(progrp_supp, many=True)
        return Response({'supplier_midfield_details':serializer.data}, status=status.HTTP_200_OK)

    def post(seld, request, project_group_number):
        data = request.data
        supplier_midfield_details = data.get('supplier_midfield_details', [])
        proj_grp_obj = get_object_or_none(ProjectGroup, project_group_number=project_group_number, project__project_status__in=['Booked', 'Live', 'Paused'])
        if not proj_grp_obj:
            return Response({'error': 'Project is not Booked, Live or Paused'}, status=status.HTTP_400_BAD_REQUEST)
        
        if supplier_midfield_details in ['', None, [''], []]:
            return Response({'error':"All fields are required"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            for supplier_midfield_dict in supplier_midfield_details:
                supplier_org_id = supplier_midfield_dict.get('supplier_org')
                supplier_contacts = supplier_midfield_dict.get('supplier_contacts')
                notes = supplier_midfield_dict.get('notes')

                if supplier_org_id in ['', None] or supplier_contacts in ['', None, [''], []] or notes in ['', None]:
                    return Response({'error':"All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

                t = sendSupplierSuppliersMidfieldUpdate.delay(project_group_number, project_number=proj_grp_obj.project.project_number,supplier_midfield_dict=supplier_midfield_dict, project_manager_email=proj_grp_obj.project.project_manager.email)
                
        return Response({'msg':'Supplier Midfield Updates sent successfully'}, status=status.HTTP_200_OK)