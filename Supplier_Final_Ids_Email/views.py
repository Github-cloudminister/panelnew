# django modules imports
from Supplier_Final_Ids_Email.models import SupplierIdsMarks
from django.conf import settings
from django.template.loader import render_to_string

# rest_framework imports
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

# third_party module imports
from knox.auth import TokenAuthentication
import uuid, hashlib, concurrent

# in-project imports
from Project.models import *
from Surveyentry.models import *
from Supplier_Final_Ids_Email.models import *
from automated_email_notifications.email_configurations import sendEmailSendgripAPIIntegration

# automated email notifications imports
from automated_email_notifications.supplier_final_ids_custom_functions import SupplierFinalIdsBySupplierSendEmail

class PendingSupplierFinalIdsView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        suppid_marks_obj_list = SupplierIdsMarks.objects.select_related('project').filter(project__project_status__in=["Invoiced"], final_ids_sent = False,  final_ids_available_by__lte = timezone.now().date(),scrubbed = True).values('project__project_number','final_ids_available_by','supplier_ids_approval_date').order_by('-project')
        return Response({'data':suppid_marks_obj_list},status=status.HTTP_200_OK)


class sendSupplierFinalIdsView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        project_number_list_params = request.data.get('project_number_list')
        project_number_list = project_number_list_params.split(',') if type(project_number_list_params) == str else project_number_list_params
        supplier_id_list = request.data.get('supplier_id_list').split(',') if request.data.get('supplier_id_list') else []

        project_obj = Project.objects.filter(project_number__in = project_number_list, supplieridsmarks__scrubbed = True, supplieridsmarks__final_ids_available_by__lte = timezone.now().date())
        
        if not project_obj.exists():
            return Response({'error':'Final ids are not available for any of the project.'})

        # New code written by Durgesh. Date: 18-04-2023
        # Send a notification email to supplier that final ids are available and can be downloaded from the link provided in the email.

        # New Code written by Durgesh. Send final ids notification to supplier that final ids available.
        # Steps. 
        # 1. Send a notification email to suppliers with code to fetch the list of projects. 
        # 2. Suppliers with open the URL and see the list of projects and number of completes. Create Supplier invoice rows at same time. 
        # 3. Download the final ids from supplier dashboard. 

        currentTime = timezone.now()
        # ****************MADATORY FIELDS IN THIS FUNCTION****************************************
        
        ProjectGroupSupplier_obj = ProjectGroupSupplier.objects.filter(project_group__project__project_number__in = project_number_list, supplier_org__supplier_type = '1')

        if supplier_id_list:
            ProjectGroupSupplier_obj = ProjectGroupSupplier_obj.filter(supplier_org__id__in=supplier_id_list,project_group__project__supplieridsmarks__final_ids_sent = True)
        
        supplier_list = set(list(ProjectGroupSupplier_obj.values_list('supplier_org', flat=True)))

        def parellel_send_final_ids_func(supplier):
            
            sup = SupplierOrganisation.objects.get(id =supplier)
            supplier_email_list = list(SupplierContact.objects.filter(supplier_id__id=supplier, send_final_ids=True).values_list('supplier_email',flat=True).order_by().distinct('supplier_email'))

            project_number_list_for_email = list(set(ProjectGroupSupplier_obj.filter(supplier_org__id = supplier).values_list('project_group__project__project_number', flat=True)))
            uuid4_str = uuid.uuid4().hex
            finalids_project_list_code = hashlib.md5(uuid4_str.encode()).hexdigest()
            final_ids_schedule = supplierFinalIdsDeploy.objects.create(project_list=project_number_list_for_email, supplier = sup, final_ids_deployed_by = request.user, project_list_code = finalids_project_list_code)


            URL = f"{settings.SUPPLIER_DASHBOARD_FRONTEND_URL}#/authentication/finalids/ictXUesVWsi7cKcq30A1XLDkA4w813LuqLph3QpV5W3jFdydmBYi5B/{sup.supplier_code}/{finalids_project_list_code}"

            html_message = render_to_string('supplier_final_ids_email/final_ids_available_email_template.html',{'downloadidsurl':URL, 'projectlist':project_number_list_for_email})
            to_emails = supplier_email_list
            if settings.SERVER_TYPE == 'production':
                cc_emails = 'projectmanagement@panelviewpoint.com'
            else:
                cc_emails = 'tech@panelviewpoint.com'
            
            email_sent_successfully = True
            subject = f'Final Ids - PANEL VIEWPOINT: {sup.supplier_name} - {timezone.now().date()}'
            sendEmail = sendEmailSendgripAPIIntegration(from_email = ('finalids@panelviewpoint.com', 'Final IDs'),to_emails=to_emails, subject=subject, html_message=html_message, cc_emails = cc_emails)

            supplier_sent_status = False

            if sendEmail.status_code in [200, 201]:
                supplier_sent_status = True
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            yield_results = list(executor.map(parellel_send_final_ids_func, supplier_list))
        
        end_time = timezone.now()
        calculated_duration = end_time - currentTime
        duration_in_minutes = calculated_duration.seconds/60.0

        SupplierIdsMarks_obj = SupplierIdsMarks.objects.filter(project__project_number__in = project_number_list)
        SupplierIdsMarks_obj.update(final_ids_sent = True, final_ids_sent_date = timezone.now().date(), final_ids_sent_by = request.user)

        return Response({'msg':'Supplier Final ids have been scheduled!','projectcode':project_number_list}, status=status.HTTP_202_ACCEPTED)


class SupplierFinalIdsView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def post(self, request):
       
        project_number_list = request.data.get('project_number_list', None)
        supplier_id_list = request.data.get('supplier_id_list', None)
        send_to_all = request.GET.get('send_to_all', None)
        exclude_supplier = request.data.get('exclude_supplier', None)

        project_list_obj = Project.objects.filter(project_status__in=["Invoiced"])

        if send_to_all == 'Y':
            project_list_obj = project_list_obj.exclude(supplieridsmarks__supplier_ids_sent = "Yes")
        else:
            if project_number_list in ['', None]:
                return Response({'error': 'Project number should not be blank..!'}, status=status.HTTP_200_OK)

            project_number_list1 = project_number_list.split(',')
            project_list_obj = project_list_obj.filter(project_number__in=project_number_list1)
            
            if supplier_id_list not in [None, '']:
                supplier_id_list1 = supplier_id_list.split(',')
                project_list_obj = project_list_obj.filter(group_project__project_group__supplier_org__id__in = supplier_id_list1, group_project__project_group__supplier_org__supplier_type='1').distinct()

        if project_list_obj.exists():
            send_email = SupplierFinalIdsBySupplierSendEmail(project_number_list=project_number_list, supplier_id_list=supplier_id_list, send_to_all=send_to_all, exclude_supplier=exclude_supplier, user_email=request.user.email)
            return Response({'msg': f'Email has been scheduled..!'}, status=status.HTTP_200_OK)
        else:
            return Response({'msg': 'Please raise correct request..!'}, status=status.HTTP_400_BAD_REQUEST)
            

class ProjectSupplierScrabbedView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self,request,*args,**kwargs):

        project_id = request.data.get('project_id')

        if project_id not in ['',None]:
            supplier_ids_mark_obj = SupplierIdsMarks.objects.filter(project__project_number=project_id).values('project__project_number','reconciled_date','scrubbed','scrubbed_date','final_ids_sent','final_ids_sent_date')
        else:
            return Response({'error':'Project id is required..!'})

        return Response(supplier_ids_mark_obj, status=status.HTTP_200_OK)

