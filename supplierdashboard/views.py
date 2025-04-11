#Rest_framework library
import csv, random, string
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.authtoken.serializers import AuthTokenSerializer

# import django libraries
from django.contrib.auth import login
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.template.loader import render_to_string
from CompanyBankDetails.models import CompanyDetails
from CompanyBankDetails.serializers import CompanyDetailSerializer
from Customer.serializers import CurrencySerializer
from Invoice.models import Invoice
from django.db.models.functions import Cast
from django.db.models import Count, Q, F, Avg
from django.http import HttpResponse
from Logapp.views import employee_login_Log, supplier_invoice_log
from Prescreener.models import ProjectGroupPrescreener
from uuid import uuid4
from django.contrib.auth.hashers import make_password
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# import models and serialiizers
from Supplier.models import SupplierOrganisation
from SupplierInvoice.models import InvoiceFileData, SupplierInvoice, SupplierInvoiceRow
from SupplierInvoice.serializers import SupplierInvoiceRetrieveUpdateSerializer
from Supplier_Final_Ids_Email.models import supplierFinalIdsDeploy
from supplierdashboard.serializers import *
from Project.models import ProjectGroup, ProjectGroupSupplier
from Project.serializers import CountrySerializer, LanguageSerializer
from Surveyentry.models import *
from supplierdashboard.serializers import SurveyPrescreenerViewSerializer

# import custom pagination file
from .paginations import *

# automated email notifications imports
from automated_email_notifications.email_configurations import *

# third party libraries
from datetime import date, timedelta
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView


# Create your views here.
class SupplierAuthPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        auth_token = request.META.get('HTTP_AUTHORIZATION')
        if auth_token != None:
            if settings.SUPPLIER_DASHBOARD_AUTH_KEY in auth_token.split('Token '):
                return True
        return False

class SupplierEmployeePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            user_type = request.user.emp_type
            if user_type in ['10','12']:
                return True
            else:
                return False
        except:
            return False
        
class AdminSupplierEmployeePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        try:
            user_type = request.user.emp_type
            if user_type in ['12']:
                return True
            else:
                return False
        except:
            return False

class SupplierDashboardLoginApiView(KnoxLoginView):

    permission_classes = (permissions.AllowAny,)
    serializer_class = AuthTokenSerializer

    def post(self, request, format=None):
        
        username = request.data['username'].lower()
        password = request.data['password']
        serializer = self.serializer_class(data={'username':username,'password':password})
        # serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        employee_login_Log(request.user)
        temp_list=super(SupplierDashboardLoginApiView, self).post(request, format=None)
        temp_list.data['id'] = user.id
        temp_list.data['first_name'] = user.first_name
        temp_list.data['last_name'] = user.last_name
        temp_list.data['user_type'] = user.emp_type
        if user.emp_type in ['10','12']:
            return Response({"Data":temp_list.data})
        else:
            return Response({"error":"You do not have permission to access this tool."}, status=status.HTTP_400_BAD_REQUEST)




class supplierList(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (AdminSupplierEmployeePermission,)
    queryset = SupplierOrganisation.objects.filter(supplier_status = '1',suppliercontact__supplier_dashboard_registration = True).distinct()
    serializer_class = supplierDashboardSupplierListSerializer

class supplierDetail(ModelViewSet):
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    queryset = SupplierOrganisation.objects.filter(supplier_status = '1')
    serializer_class = supplierDashboardSupplierListSerializer
    lookup_field = 'pk'

class projectList(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = LiveProjectListSerializer
    pagination_class = MyPageNumberPagination
    
    def get_queryset(self):
        query_param = self.request.GET
        sup_code = self.request.user.source_id
        todays_date = datetime.now().date()
        two_days_ago = todays_date - timedelta(days=2)

        if query_param.get('project_no'):
            return ProjectGroupSupplier.objects.filter(project_group__project_group_status = 'Live', supplier_org__id = sup_code, created_at__date__gte = '2021-4-15', project_group__project__project_number=query_param.get('project_no'))
        elif query_param.get('survey_no'):
            return ProjectGroupSupplier.objects.filter(project_group__project_group_status = 'Live', supplier_org__id = sup_code, created_at__date__gte = '2021-4-15', project_group__project_group_number=query_param.get('survey_no'))
        else:
            return ProjectGroupSupplier.objects.filter(project_group__project_group_status = 'Live', supplier_org__id = sup_code, created_at__date__gte = two_days_ago)


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        sup_code = self.request.user.source_id
        if page is not None:
            serializer = self.serializer_class(page, context = {'source':sup_code}, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, context = {'source':sup_code}, many=True)
        return Response(serializer.data)

class supplierAdd(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)
    # permission_classes = (SupplierAuthPermission,)
    serializer_class = supplierAddSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            sup_code = self.request.user.source_id
            instance = ProjectGroupSupplier.objects.get(supplier_org__id = sup_code, project_group__project_group_number = self.kwargs['project_group_number'])
            serializer = self.serializer_class(instance)
            response_data = serializer.data
            response_data.update({
                'survey_number':self.kwargs['project_group_number'],
                'country':instance.project_group.project_group_country.country_name,
                'language':instance.project_group.project_group_language.language_name,
                'modified_at':instance.modified_at,
                'created_at':instance.created_at,
                'project_manager':instance.project_group.project.project_manager.full_name(),
                'project_manager_email':instance.project_group.project.project_manager.email
                })
            return Response(response_data, status.HTTP_200_OK)
        except:
            return Response({"detail": "Not found."},status.HTTP_400_BAD_REQUEST)
        

    def put(self, request, *args, **kwargs):
        try:
            sup_code = self.request.user.source_id
            instance = ProjectGroupSupplier.objects.get(supplier_org__id = sup_code, project_group__project_group_number = self.kwargs['project_group_number'])
            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status.HTTP_200_OK)
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_400_BAD_REQUEST)

class awardedprojectList(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = AwardedProjectGroupSerializer
    pagination_class = MyPageNumberPagination
    
    def get_queryset(self, sup_code):
        query_params = self.request.GET
        project_number = query_params.get('projectnumber')
        sup_code = self.request.user.source_id

        project_group_obj = ProjectGroup.objects.filter(project_group_status = 'Live',created_at__date__gte = '2023-01-01', show_on_DIY=True).exclude(project_group__supplier_org__id = sup_code).exclude(project__project_type = '12')

        if sup_code == '163':
            project_group_obj = project_group_obj.exclude(project__project_customer__id__in  = ['9','24','32','69'])
        else:
            project_group_obj = project_group_obj.exclude(project__project_customer__id__in  = ['24','32','69'])
        
        
        if project_number:
            project_group_obj = project_group_obj.filter(project__project_number=project_number)


        if query_params.get('project_no'):
            project_group_obj = project_group_obj.filter(project__project_number=query_params.get('project_no'))

        elif query_params.get('survey_no'):
            project_group_obj = project_group_obj.filter(project_group_number=query_params.get('survey_no'))
        
        return project_group_obj

    def list(self, request, *args, **kwargs):
        sup_code = self.request.user.source_id
        queryset = self.filter_queryset(self.get_queryset(sup_code))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, context = {'source':sup_code}, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, context = {'source':sup_code}, many=True)
        return Response(serializer.data)


class closedprojectList(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = ClosedProjectGroupSerializer
    pagination_class = MyPageNumberPagination
    
    def get_queryset(self):
        query_params = self.request.GET
        sup_code = self.request.user.source_id
        query_list = ProjectGroupSupplier.objects.filter(project_group__project_group_status__in = ['Closed','Paused', 'Reconciled', 'ReadyForInvoiceApproved','Invoiced'], supplier_org__id = sup_code).exclude(project_group__project__supplieridsmarks__final_ids_sent=True)

        if query_params.get('project_no'):
            query_list = query_list.filter(project_group__project__project_number=query_params.get('project_no'))
        
        if query_params.get('survey_no'):
            query_list = query_list.exclude(~Q(project_group__project_group_number__icontains=query_params.get('survey_no')))
        
        return query_list


    def list(self, request, *args, **kwargs):
        sup_code = self.request.user.source_id
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, context = {'source':sup_code}, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, context = {'source':sup_code}, many=True)
        return Response(serializer.data)


class finalizedprojectList(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    pagination_class = MyPageNumberPagination

    def list(self, request, *args, **kwargs):

        page = self.request.GET.get('page',1)
        project_number = request.GET.get('project_no')
        sup_code = self.request.user.source_id
        # query_list = ProjectGroupSupplier.objects.filter(project_group__project_group_status__in = ['Invoiced','Archived'], supplier_org__id = sup_code, project_group__project__supplieridsmarks__final_ids_sent=True)

        # if project_number:
        #     query_list = query_list.filter(project_group__project__project_number__icontains = project_number)
            
        # progrp_supp = query_list.values(project_group_number = F('project_group__project_group_number'))

        archived_queryset = RespondentDetail.objects.filter(source = sup_code, url_type = 'Live', respondentdetailsrelationalfield__project_group__project_group_status__in = ['Archived']).values('project_number').annotate(
            completes = Count('resp_status', filter=Q(resp_status='4')),
            rejected_completes = Count('resp_status', filter=Q(resp_status__in=['8','9'])),
            cpi = Avg('supplier_cpi', filter=Q(resp_status='4')),
            total_expense = Sum('supplier_cpi', filter=Q(resp_status='4')),
            final_ids_sent = F("respondentdetailsrelationalfield__project_group__project__supplieridsmarks__final_ids_sent_date")
            )
        
        invoiced_queryset = RespondentDetail.objects.filter(source = sup_code, url_type = 'Live', respondentdetailsrelationalfield__project_group__project_group_status__in = ['Invoiced'],respondentdetailsrelationalfield__project_group__project__supplieridsmarks__final_ids_sent=True).values('project_number').annotate(
            completes = Count('resp_status', filter=Q(resp_status='4')),
            rejected_completes = Count('resp_status', filter=Q(resp_status__in=['8','9'])),
            cpi = Avg('supplier_cpi', filter=Q(resp_status='4')),
            total_expense = Sum('supplier_cpi', filter=Q(resp_status='4')),
            final_ids_sent = F("respondentdetailsrelationalfield__project_group__project__supplieridsmarks__final_ids_sent_date")
            )
        
        if project_number:
            archived_queryset = archived_queryset.filter(respondentdetailsrelationalfield__project__project_number = project_number)

            invoiced_queryset = invoiced_queryset.filter(respondentdetailsrelationalfield__project__project_number = project_number)


        finalized_invoice_data = invoiced_queryset.union(archived_queryset)

        paginator = Paginator(finalized_invoice_data,15)
        try:
            finalized_invoice_data = paginator.page(page)
        except PageNotAnInteger:
            finalized_invoice_data = paginator.page(1)
        except EmptyPage:
            finalized_invoice_data = {"message":"No More Data Available.!"}
            return Response(finalized_invoice_data, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(finalized_invoice_data.object_list, status=status.HTTP_200_OK)


class acceptSupplierProject(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = AcceptSupplierSerializer
    
    def get_queryset(self):
        sup_code = self.request.user.source_id
        return ProjectGroupSupplier.objects.filter(project_group__project_group_number = self.kwargs['project_group_number'], supplier_org__id = sup_code)

    def create(self, request, *args, **kwargs):
        try:
            sup_code = self.request.user.source_id
            suppgrp = SupplierOrganisation.objects.get(id=sup_code)
            progroup = ProjectGroup.objects.get(project_group_number=self.kwargs['project_group_number'])
            had_supplier = ProjectGroupSupplier.objects.filter(project_group=progroup, supplier_org=suppgrp).exists()
            if not had_supplier:
                supplier_survey_url = settings.SURVEY_URL+"survey?glsid="+progroup.project_group_encodedS_value + "&source="+str(suppgrp.id)+"&PID=XXXXX"

                default_complete = suppgrp.max_completes_on_diy
                accepted_cpi = round(progroup.project_group_cpi*0.60, 2) if round(progroup.project_group_cpi*0.60, 2) < suppgrp.max_authorized_cpi else suppgrp.max_authorized_cpi
                projectgroup_supplier_obj = ProjectGroupSupplier.objects.create(project_group=progroup, supplier_org=suppgrp,completes=default_complete, clicks=progroup.project_group_clicks, cpi=accepted_cpi , supplier_completeurl=suppgrp.supplier_completeurl, supplier_terminateurl=suppgrp.supplier_terminateurl, supplier_quotafullurl=suppgrp.supplier_quotafullurl, supplier_securityterminateurl=suppgrp.supplier_securityterminateurl, supplier_internal_terminate_redirect_url = suppgrp.supplier_internal_terminate_redirect_url,  supplier_terminate_no_project_available = suppgrp.supplier_terminate_no_project_available, supplier_survey_url=supplier_survey_url,supplier_postbackurl = suppgrp.supplier_postbackurl, supplier_status="Live")

                if suppgrp.supplier_type == '1':
                    # ****************************************
                    # START::Send Email on Project Accept
                    # ****************************************
                    html_message = render_to_string('supplierdashboard/emailtemplates/emailconfirmation.html', {
                        'project_number': progroup.project.project_number,
                        'survey_number': progroup.project_group_number,
                        'ir': progroup.project_group_incidence,
                        'loi': progroup.project_group_loi,
                        'complete': default_complete,
                        'cpi': accepted_cpi,
                        'complete_url': projectgroup_supplier_obj.supplier_completeurl,
                        'terminate_url': projectgroup_supplier_obj.supplier_terminateurl,
                        'quotafull_url': projectgroup_supplier_obj.supplier_quotafullurl,
                        'security_term_url': projectgroup_supplier_obj.supplier_securityterminateurl,
                        'survey_live_url': supplier_survey_url,
                        'postback_url': projectgroup_supplier_obj.supplier_postbackurl
                        })

                    # FETCH ALL SUPPLIER CONTACTS FROM THAT SUPPLIER ORG AND SEND THEM THIS EMAIL TO ALL AT ONCE  
                    supp_contact_list = list(SupplierContact.objects.filter(supplier_id=suppgrp).values_list('supplier_email', flat=True))

                    subject=f'{progroup.project.project_number} | {progroup.project_group_number} - {progroup.project_group_name} | {suppgrp.supplier_name} [Accepted from EngineX]'

                    if settings.SERVER_TYPE == 'production':
                        cc_emails = 'projects@panelviewpoint.com'
                    else:
                        cc_emails = 'tech@panelviewpoint.com'

                    sendEmailSendgripAPIIntegration(to_emails=supp_contact_list, subject=subject, html_message=html_message, cc_emails = cc_emails, proj_manager_cc_email=progroup.project.project_manager.email)
                    # ****************************************
                    # END::Send Email on Project Accept
                    # ****************************************

                if request.user.is_authenticated:
                    projectgroup_supplier_obj.created_by = request.user
                else:
                    projectgroup_supplier_obj.created_from_supplier_dashboard = True
                projectgroup_supplier_obj.save()
                
                return Response({'message': 'Supplier Project Accepted successfully..!'}, status=status.HTTP_200_OK)
            return Response({'message': 'Supplier Project Already Accepted..!'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_400_BAD_REQUEST)


class downloadFinalIds(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
         
    def list(self, request, *args, **kwargs):

        resp_type = request.query_params.get('resp_type')
        projectnumber = request.query_params.get('projectnumber')
        sup_code = request.user.source_id
        # sup_code = request.query_params.get('sup_code') # This is the Supplier ID from the Frontend, not the Supplier Code
        if sup_code in ['', None]:
            return Response({'error': 'Supplier code should not be blank'}, status=status.HTTP_400_BAD_REQUEST)

        if projectnumber in ['', None]:
            return Response({'error': 'Project number should not be blank'}, status=status.HTTP_400_BAD_REQUEST)

        invoice_obj = Invoice.objects.filter(invoice_project__project_number=projectnumber, created_at__date__gte = '2021-8-1').exists()
        if not invoice_obj:
            return Response({'error':'Please contact the project manager'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = RespondentURLDetail.objects.filter(respondent__source = sup_code, respondent__project_number = projectnumber, respondent__resp_status='4', respondent__url_type='Live').values('pid', cpi=F('respondent__supplier_cpi'))

        if resp_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=' + 'Final IDs' + '.csv'
            writer = csv.writer(response)
            header = ["PID", "CPI"]

            count = 0
            for data in queryset:
                pid = data['pid']
                cpi = data['cpi']
                content = [pid, cpi]

                if count == 0:
                    writer.writerow(header)
                    count += 1
                writer.writerow(content)

            return response

        return Response(queryset, status=status.HTTP_200_OK)


class SearchProjectListView(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    pagination_class = MyPageNumberPagination
    serializer_class = SearchProjectListSerializer

    def list(self, request, *args, **kwargs):
        project_number = request.GET.get('projectnumber')
        project_status = request.GET.get('status')
        sup_code = request.user.source_id

        if project_number in ['', None]:
            return Response({'error': 'Project number should not be blank..!'}, status=status.HTTP_400_BAD_REQUEST)

        # ****************** Check length of Project Object ******************
        if project_status in ['Live']:
            project_obj_list = ProjectGroupSupplier.objects.filter(supplier_org__id = sup_code, created_at__date__gte = '2021-4-15', project_group__project__project_number__icontains=project_number,project_group__project_group_status__in = ['Live'])
        elif project_status in ['Awarded']:
            project_obj_list = ProjectGroupSupplier.objects.filter(project_group__project__project_number__icontains=project_number,project_group__project_group_status__in = ['Live']).exclude(supplier_org__id = sup_code).order_by().distinct('project_group__project_group_number')
        elif project_status in ['Closed']:
            project_obj_list = ProjectGroupSupplier.objects.filter(project_group__project_group_status__in = ['Closed','Paused', 'Reconciled', 'Invoiced'], supplier_org__id = self.kwargs['sup_code'], project_group__project__project_number=project_number).exclude(project_group__project__supplieridsmarks__final_ids_sent=True)
        elif project_status in ['Finalized']:
            project_obj_list = ProjectGroupSupplier.objects.filter(project_group__project_group_status__in = ['Invoiced'], supplier_org__id = self.kwargs['sup_code'], project_group__project__supplieridsmarks__final_ids_sent=True, project_group__project__project_number__icontains = project_number)

            progrp_supp = project_obj_list.values(project_group_number = F('project_group__project_group_number'))

            queryset = RespondentDetail.objects.filter(source = sup_code, url_type = 'Live', project_group_number__in = progrp_supp).values('project_number').annotate(
                completes = Count('resp_status', filter=Q(resp_status='4')),
                cpi = Avg('supplier_cpi'),
                total_expense = Sum('supplier_cpi', filter=Q(resp_status='4')))
            
            return Response(queryset, status=status.HTTP_200_OK)

        else:
            project_obj_list = ProjectGroupSupplier.objects.filter(supplier_org__id = sup_code, project_group__project__project_number__icontains=project_number)
            

        page = self.paginate_queryset(project_obj_list)
        if page is not None:
            serializer = self.serializer_class(page, context = {'source':sup_code}, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.serializer_class(project_obj_list, context = {'source':sup_code}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class ProjectStatusWiseDataView(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = SearchProjectListSerializer

    def list(self, request, *args, **kwargs):
        project_number = request.GET.get('projectnumber')
        project_status = request.GET.get('status')
        country_obj = request.GET.get('country')
        language_obj = request.GET.get('language')
        sup_code = self.request.user.source_id
        def conditional_project_number_filter(project_number):
            if project_number != None:
                return Q(project_group__project__project_number__icontains=project_number)
            else:
                return Q()
        def conditional_country_obj_filter(country_obj):
            if country_obj != None:
                return Q(project_group__project_group_country=country_obj)
            else:
                return Q()
        def conditional_language_obj_filter(language_obj):
                if language_obj != None:
                    return Q(project_group__project_group_language=language_obj)
                else:
                    return Q()

        # ****************** Check length of Project Object ******************
        if project_status in ['Live']:
            project_obj_list = ProjectGroupSupplier.objects.filter(
                conditional_project_number_filter(project_number),
                conditional_country_obj_filter(country_obj),
                conditional_language_obj_filter(language_obj),
                supplier_org__id = sup_code, created_at__date__gte = '2021-4-15'
                ,project_group__project_group_status__in = ['Live'])

        elif project_status in ['Awarded']:
            project_obj_list = ProjectGroupSupplier.objects.filter(
                conditional_project_number_filter(project_number),
                conditional_country_obj_filter(country_obj),
                conditional_language_obj_filter(language_obj),
                project_group__project_group_status__in = ['Live']
                ).exclude(supplier_org__id = sup_code).order_by().distinct('project_group__project_group_number')

        elif project_status in ['Closed']:
            project_obj_list = ProjectGroupSupplier.objects.filter(
                conditional_project_number_filter(project_number),
                conditional_country_obj_filter(country_obj),
                conditional_language_obj_filter(language_obj),
                project_group__project_group_status__in = ['Closed','Paused', 'Reconciled', 'Invoiced'],
                supplier_org__id = sup_code 
                ).exclude(project_group__project__supplieridsmarks__final_ids_sent=True)

        elif project_status in ['Finalized']:
            project_obj_list = ProjectGroupSupplier.objects.filter(
                conditional_project_number_filter(project_number),
                conditional_country_obj_filter(country_obj),
                conditional_language_obj_filter(language_obj),
                project_group__project_group_status__in = ['Invoiced'],
                supplier_org__id = sup_code,
                project_group__project__supplieridsmarks__final_ids_sent=True)

        elif country_obj not in ['',None]:
            project_obj_list = ProjectGroupSupplier.objects.filter(project_group__project_group_country=country_obj,supplier_org__id = sup_code)

        elif language_obj not in ['',None]:
            project_obj_list = ProjectGroupSupplier.objects.filter(project_group__project_group_language=language_obj,supplier_org__id = sup_code)

        else:
            project_obj_list = ProjectGroupSupplier.objects.filter(supplier_org__id = sup_code)

        page = self.paginate_queryset(project_obj_list)
        if page is not None:
            serializer = self.serializer_class(page, context = {'source':sup_code}, many=True)
            return self.get_paginated_response(serializer.data) 
        serializer = self.serializer_class(project_obj_list, context = {'source':sup_code}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)




class SupplierProjectLiveView(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = SearchProjectListSerializer

    def list(self, request, *args, **kwargs):
        project_status = request.GET.get('status')
        sup_code = self.request.user.source_id

        if project_status:
            project_obj_list = ProjectGroupSupplier.objects.filter(supplier_org__id = sup_code, created_at__date__gte = '2021-4-15',project_group__project_group_status__in = ['Live'])

            progrp_supp = project_obj_list.values(project_group_number = F('project_group__project_group_number'))

            queryset = RespondentDetail.objects.filter(source = sup_code, url_type = 'Live', project_group_number__in = progrp_supp).values('project_number').annotate(
                completes = Count('resp_status', filter=Q(resp_status='4')),
                cpi = Avg('supplier_cpi'),
                total_expense = Sum('supplier_cpi', filter=Q(resp_status='4')))
            
            return Response(queryset, status=status.HTTP_200_OK)
        serializer = self.serializer_class(project_obj_list, context = {'source':sup_code}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class SupplierProjectClosedView(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = SearchProjectListSerializer

    def list(self, request, *args, **kwargs):
        project_status = request.GET.get('status')
        sup_code = self.request.user.source_id

        if project_status:
            project_obj_list = ProjectGroupSupplier.objects.filter(supplier_org__id = sup_code, created_at__date__gte = '2021-4-15',project_group__project_group_status__in = ['Closed','Paused', 'Reconciled', 'Invoiced'])

            progrp_supp = project_obj_list.values(project_group_number = F('project_group__project_group_number'))

            queryset = RespondentDetail.objects.filter(source = sup_code, url_type = 'Live', project_group_number__in = progrp_supp).values('project_number').annotate(
                completes = Count('resp_status', filter=Q(resp_status='4')),
                cpi = Avg('supplier_cpi'),
                total_expense = Sum('supplier_cpi', filter=Q(resp_status='4')))
            
            return Response(queryset, status=status.HTTP_200_OK)
        serializer = self.serializer_class(project_obj_list, context = {'source':sup_code}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SupplierProjectFinalizedView(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = SearchProjectListSerializer

    def list(self, request, *args, **kwargs):
        project_status = request.GET.get('status')
        sup_code = self.request.user.source_id

        if project_status:
            project_obj_list = ProjectGroupSupplier.objects.filter(supplier_org__id = sup_code, created_at__date__gte = '2021-4-15',project_group__project_group_status__in = ['Invoiced'])

            progrp_supp = project_obj_list.values(project_group_number = F('project_group__project_group_number'))

            queryset = RespondentDetail.objects.filter(source = sup_code, url_type = 'Live', project_group_number__in = progrp_supp).values('project_number').annotate(
                completes = Count('resp_status', filter=Q(resp_status='4')),
                cpi = Avg('supplier_cpi'),
                total_expense = Sum('supplier_cpi', filter=Q(resp_status='4')))
            
            return Response(queryset, status=status.HTTP_200_OK)
        serializer = self.serializer_class(project_obj_list, context = {'source':sup_code}, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class SupplierStatsAggregateCountsAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)


    def get(self, request):
        sup_code = self.request.user.source_id
        live_surveys = ProjectGroupSupplier.objects.filter(supplier_org__id=sup_code, supplier_status='Live').count()

        till_today = date.today()
        first_day = till_today - timedelta(days=(till_today.day - 1))

        stats_count = RespondentDetail.objects.filter(source=sup_code, url_type='Live',resp_status='4').aggregate(current_month_completes=Count('id', filter=Q(resp_status='4', end_time_day__range=(first_day,till_today))), current_year_completes=Count('id', filter=Q(resp_status='4', end_time_day__year=date.today().year)), total_earnings=Cast(Sum('supplier_cpi', filter=Q(resp_status='4',respondentdetailsrelationalfield__project__project_status = "Invoiced",respondentdetailsrelationalfield__project__scrubproject = True)), output_field=models.DecimalField(max_digits=10, decimal_places=2))
        )
        stats_count.update({'live_surveys':live_surveys})

        return Response(data=stats_count)



class SupplierDashboardCountryView(APIView):

    '''
        method to get the list of all country objects.
    '''
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = CountrySerializer

    def get(self, request):

        country_list = Country.objects.all()
        serializer = self.serializer_class(country_list, many=True)
        return Response(serializer.data)
    


class SupplierDashboardLanguageView(APIView):

    '''
        method to get the list of all language objects.
    '''
    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = LanguageSerializer

    def get(self, request):

        language_list = Language.objects.all()
        serializer = self.serializer_class(language_list, many=True)
        return Response(serializer.data)



class ZipCodeListView(APIView):

    # permission_classes = (SupplierAuthPermission,)
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)

    def get(self, request, project_group_number):
        zipcode_list = list(ZipCode.objects.filter(project_group_id__project_group_number=project_group_number).values_list('zip_code', flat=True)) + ProjectGroupPrescreener.objects.get(project_group_id__project_group_number=project_group_number).allowed_zipcode_list
        return Response({'zip':zipcode_list}, status=status.HTTP_200_OK)


class SurveyPreScreenerListView(APIView):

    authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = SurveyPrescreenerViewSerializer

    def get(self, request, survey_number):

        prescreener_obj = ProjectGroupPrescreener.objects.filter(project_group_id__project_group_number=survey_number, is_enable = True)
        serializer = self.serializer_class(prescreener_obj, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        

class finalidsProjectListView(APIView):

    # authentication_classes = (TokenAuthentication,)
    # permission_classes = (SupplierAuthPermission,)
    # permission_classes = (SupplierEmployeePermission,)

    def get(self, request, supcode, project_list_code):
        # supcode = self.request.user.source_id
        try:
            completes_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4], respondentdetailsrelationalfield__respondent__url_type='Live')
            supplier_finalids_deploy_obj = supplierFinalIdsDeploy.objects.get(project_list_code=project_list_code, supplier__supplier_code = supcode)

            _table_data = RespondentDetail.objects.filter(project_number__in = supplier_finalids_deploy_obj.project_list, url_type='Live', respondentdetailsrelationalfield__source__supplier_code = supcode).values('source','respondentdetailsrelationalfield__source__supplier_name', 'project_number', 'respondentdetailsrelationalfield__project').annotate(completes=Count('project_number', filter=Q(resp_status='4'))).order_by('source')
            return Response({'project_list': _table_data}, status=status.HTTP_200_OK)
        except:
            return Response({'error':'URL Does not exist.!'}, status=status.HTTP_400_BAD_REQUEST)



class ProjectFinalidsDataView(APIView):
    # authentication_classes = (TokenAuthentication,)

    def get(self,request, project_id, supplier_id):
        # supplier_id = self.request.user.source_id
        project_final_ids_obj = RespondentDetail.objects.filter(url_type='Live',resp_status='4',project_number = project_id, source = supplier_id).values('id').annotate(
            pid = F('respondenturldetail__pid'),
            cpi = F('supplier_cpi')
        )
        return Response({"Project_Final_ids":project_final_ids_obj}, status=status.HTTP_200_OK)


class SupplierInvoiceRowVerificationView(APIView):
    permission_classes = (SupplierEmployeePermission,)

    def post(self, request, supplierOrg_id):
        data = request.data
        supp_inv_data = data.get('supplier_data')
        supp_data_list = []
        if supp_inv_data:
            for inv_obj in supp_inv_data:
                project_number = inv_obj['project_number'].strip()
                supplier_invrow_qs = SupplierInvoiceRow.objects.filter(supplier_org=supplierOrg_id, project__project_number=project_number, cpi=inv_obj['cpi'])
                if supplier_invrow_qs:
                    for supp_invrow_obj in supplier_invrow_qs:
                        inv_data_dict = {'supplierOrg_id':supplierOrg_id, 'project_number':project_number, 'cpi':inv_obj['cpi'], 'completes':inv_obj['completes'], 'suppinv_row_id':supp_invrow_obj.id, 'systemcpi':supp_invrow_obj.cpi, 'systemcompletes':supp_invrow_obj.completes, 'invoice_received':supp_invrow_obj.invoice_received,'data_verified':True}
                        supp_data_list.append(inv_data_dict)
                else:
                    inv_data_dict = {'supplierOrg_id':supplierOrg_id, 'project_number':project_number, 'cpi':inv_obj['cpi'], 'completes':inv_obj['completes'], 'suppinv_row_id':'-', 'systemcpi':0.0, 'systemcompletes':0, 'invoice_received':'-','data_verified':False}
                    supp_data_list.append(inv_data_dict)

            return Response(supp_data_list, status=status.HTTP_200_OK)

        return Response({'message':'Please provide the Supplier Data'}, status=status.HTTP_200_OK)
    


class SupplierInvoiceDataView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)

    def get(self,request):
        supplierOrg_id = self.request.user.source_id
        supplier_invoice_row_obj = SupplierInvoice.objects.filter(supplier_org=supplierOrg_id,created_from = '2').values('id','supplier_org','company','invoice_number','invoice_date','due_date','conversion_rate','taxable_value','tax_amount','total_from_invoice_amount','invoice_status',currency_code = F('currency__currency_iso'),expected_invoice_payment = F('supplierinvoicepayment__expected_invoice_payment'),date_invoice_paid = F('supplierinvoicepayment__date_invoice_paid')).order_by('-invoice_date')

        return Response({"supplier_invoice_data":supplier_invoice_row_obj}, status=status.HTTP_200_OK)



class SupplierWiseSupplierInvoiceRowDataView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)

    def get(self,request):
        supplierOrg_id = self.request.user.source_id
        supplier_invoice_row_obj = SupplierInvoiceRow.objects.filter(
            project__supplieridsmarks__final_ids_sent_date__gte = settings.SUPPLIER_INVOICE_DEPLOYE_DATE,
            project__supplieridsmarks__supplier_ids_approval = True,
            supplier_org=supplierOrg_id,supplier_invoice_id__isnull = True,
            project__supplieridsmarks__final_ids_sent = True).values(
                'id','project','supplier_org','invoice_received','completes','cpi',project_number = F('project__project_number'),
                ).order_by('-project')

        return Response({"supplier_invoice_row":supplier_invoice_row_obj}, status=status.HTTP_200_OK)


class SupplierDashboardSupplierDataView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)

    def get(self,request):
        supplierOrg_id = self.request.user.source_id
        supplier_obj = SupplierOrganisation.objects.filter(id=supplierOrg_id).values('supplier_name','max_completes_on_diy','supplier_address1','supplier_address2','supplier_city','supplier_state','supplier_country','supplier_zip','supplier_TAX_id','supplier_completeurl','supplier_terminateurl','supplier_quotafullurl','supplier_securityterminateurl','supplier_postbackurl','supplier_routerurl','supplier_rate_model','supplier_rate','supplier_paymentdetails','supplier_status','supplier_internal_terminate_redirect_url','supplier_terminate_no_project_available','supplier_url_code','max_authorized_cpi')

        return Response({"supplier_data":supplier_obj}, status=status.HTTP_200_OK)
    

class SupplierDashboardSupplierUpdateView(APIView):
    permission_classes = (SupplierEmployeePermission,)

    def post(self,request,supplierOrg_id):
        data = request.data

        supplier_name = data.get('supplier_name')
        max_completes_on_diy = data.get('max_completes_on_diy')
        supplier_address1 = data.get('supplier_address1')
        supplier_address2 = data.get('supplier_address2')
        supplier_city = data.get('supplier_city')
        supplier_state = data.get('supplier_state')
        supplier_country = data.get('supplier_country')
        supplier_zip = data.get('supplier_zip')
        max_authorized_cpi = data.get('max_authorized_cpi')
        supplier_TAX_id = data.get('supplier_TAX_id')
        supplier_completeurl = data.get('supplier_completeurl')
        supplier_terminateurl = data.get('supplier_terminateurl')
        supplier_quotafullurl = data.get('supplier_quotafullurl')
        supplier_securityterminateurl = data.get('supplier_securityterminateurl')
        supplier_postbackurl = data.get('supplier_postbackurl')
        supplier_terminate_no_project_available = data.get('supplier_terminate_no_project_available')

        supplier_obj = SupplierOrganisation.objects.filter(id=supplierOrg_id).update(
            supplier_name=supplier_name,
            max_completes_on_diy=max_completes_on_diy,
            supplier_address1=supplier_address1,
            supplier_address2=supplier_address2,
            supplier_city=supplier_city,
            supplier_state=supplier_state,
            supplier_country=supplier_country,
            supplier_zip=supplier_zip,
            max_authorized_cpi=max_authorized_cpi,
            supplier_TAX_id=supplier_TAX_id,
            supplier_completeurl=supplier_completeurl,
            supplier_terminateurl=supplier_terminateurl,
            supplier_quotafullurl=supplier_quotafullurl,
            supplier_securityterminateurl=supplier_securityterminateurl,
            supplier_postbackurl=supplier_postbackurl,
            supplier_terminate_no_project_available=supplier_terminate_no_project_available
        )

        return Response({"message":"supplier update successfully.!"}, status=status.HTTP_200_OK)




class SupplierContactDataView(APIView):
    permission_classes = (SupplierEmployeePermission,)

    def get(self,request,supplierOrg_id):

        supplier_conatct_obj = SupplierContact.objects.filter(supplier_id=supplierOrg_id).values('id','supplier_firstname','supplier_lastname','supplier_email','supplier_contactnumber')

        return Response({"supplier_conatct":supplier_conatct_obj}, status=status.HTTP_200_OK)
    


class SupplierContactUpdateDataView(APIView):
    permission_classes = (SupplierEmployeePermission,)

    def post(self,request,supplier_contact_id):

        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")
        contact_number = request.data.get("conatct_number")

        supplier_contact_obj = SupplierContact.objects.filter(id=supplier_contact_id).update(
            supplier_firstname=first_name,
            supplier_lastname=last_name,
            supplier_contactnumber=contact_number
        )

        return Response({"supplier_contact_update":supplier_contact_obj}, status=status.HTTP_200_OK)


class SupplierCompanyDetailsDataView(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)

    serializer_class = CompanyDetailSerializer
    queryset = CompanyDetails.objects.all()


class SupplierInvoiceCreateUpdateDataView(APIView):
   authentication_classes = (TokenAuthentication,)
   permission_classes = (SupplierEmployeePermission,)

   def post(self, request):

        data = request.data
        invoice_row_values = SupplierInvoiceRow.objects.filter(id__in = data.get('invoicerowids').split(","))
        filetypes = ['pdf','jpg','jpeg','png','xls','csv','docx','doc','zip','txt']

        try:
            # if len(invoice_row_values) <= 15:
            # if request.FILES['supplier_invoice_file'].name.split(".")[-1] not in filetypes:
            #     return Response({"error":"Invalid File Format"}, status=status.HTTP_400_BAD_REQUEST)
            supplierOrg_id = self.request.user.source_id
            supplierOrg_obj = get_object_or_none(SupplierOrganisation, id=supplierOrg_id)

            if invoice_row_values.count() in ['',None,0]:
                return Response({'error':'Invoice Row Not Found..!'}, status=status.HTTP_400_BAD_REQUEST)
            
            supplier_inv_obj, created = SupplierInvoice.objects.update_or_create(
                id = data.get('id'),
                defaults = {
                    'supplier_org_id' : supplierOrg_id,
                    'invoice_number' : data.get('invoice_number'),
                    'invoice_date' : data.get('invoice_date'),
                    'due_date' : data.get('due_date'),
                    'conversion_rate' : float(data.get('conversion_rate')),
                    'total_invoice_amount' : float(data.get('total_invoice_amount')),
                    'total_from_invoice_amount' : float(data.get('total_from_invoice_amount')),
                    'currency_id' : supplierOrg_obj.supplier_currency.id,
                    'taxable_value' : float(data.get('taxable_value')),
                    'tax_amount' : float(data.get('tax_amount')),
                    'company' : supplierOrg_obj.company_bank_detail,
                    'created_from' : '2'
                }
            )
            
            if 'supplier_invoice_file' in request.data:
                if request.FILES['supplier_invoice_file'].name.split(".")[-1] not in filetypes:
                    return Response({"error":"Invalid File Format"}, status=status.HTTP_400_BAD_REQUEST)
                
                file = request.FILES['supplier_invoice_file']

                #file name update due to same name file conflict in s3
                file._name = f"{''.join(random.choices(string.ascii_uppercase + string.digits, k = 25))}.{file.name.split('.')[-1]}"

                invoice_file_store = InvoiceFileData.objects.create(file = request.FILES['supplier_invoice_file'])

                request.data['supplier_invoice_file'] = f'https://pvpstatic.s3.us-west-2.amazonaws.com/supplier_invoice_pdf/{file.name}'
                # if settings.SERVER_TYPE in ['production']:
                #     request.data['supplier_invoice_file'] = f'https://pvpstatic.s3.us-west-2.amazonaws.com/supplier_invoice_pdf/{file.name}'
                # else:
                #     request.data['supplier_invoice_file'] = f"{settings.MEDIA_URL}{invoice_file.file}"

            if not created:
                supplier_invoice_log('',data,supplier_inv_obj.id,supplier_inv_obj.supplier_org.supplier_code,None)
                supplier_inv_obj.invoice_status = '6'
                supplier_inv_obj.save()
            if created and 'supplier_invoice_file' not in request.data:
                supplier_inv_obj.delete()
                invoice_row_values.update(invoiced_completes = None,invoiced_cpi = None,total_amount = None,invoice_received = False,supplier_invoice = None)
                return Response({'message':'Invoice File Not Uploaded..!'}, status=status.HTTP_400_BAD_REQUEST)
            
            if 'supplier_invoice_file' in request.data:
                supplier_inv_obj.supplier_invoice_file = request.data['supplier_invoice_file']
                supplier_inv_obj.save()
            invoice_row_values.update(
                invoiced_completes = F('completes'),
                invoiced_cpi = F('cpi'),
                total_amount = F('completes') * F('cpi'),
                invoice_received = True,
                supplier_invoice_id = supplier_inv_obj.id
            )
            supplier_invoice_log(data,'',supplier_inv_obj.id,supplier_inv_obj.supplier_org.supplier_code,None)
            return Response({'message':'Invoice Created Successfully..!'}, status=status.HTTP_200_OK)
            # else:
            #     return Response({'message':'You cannot create an invoice more than 15 Project.!'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            invoice_row_values.update(invoiced_completes = None,invoiced_cpi = None,total_amount = None,invoice_received = False,supplier_invoice = None)
            supplier_inv_obj = SupplierInvoice.objects.filter(id = data.get('id')).delete()
            return Response({'error':'Something Went Wrong. Please try again later!'}, status=status.HTTP_400_BAD_REQUEST)
        

class SupplierInvoiceCurrencyDataView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)
    serializer_class = CurrencySerializer

    def get(self,request):

        queryset = Currency.objects.filter(currency_iso__isnull = False)
        serializer = self.serializer_class(queryset, many= True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    
class SupplierInvoiceGet(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)

    def get(self,request,invoiceid):
        queryset = SupplierInvoice.objects.get(id = invoiceid)
        serializer = SupplierInvoiceRetrieveUpdateSerializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)

class SupplierInvoiceCurrencyGET(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)
    
    def get(self,request):
        try:
            supplierOrg_id = self.request.user.source_id
            supplier_obj = SupplierOrganisation.objects.get(id = supplierOrg_id)
            return Response({'supplier_currency':str(supplier_obj.supplier_currency.currency_iso),'cpi_calculation_method':supplier_obj.cpi_calculation_method}, status=status.HTTP_200_OK)
        except:
            return Response({'error':'Invalid Supplier'}, status=status.HTTP_400_BAD_REQUEST)
        

class StatsLastSevenDayCountCompleteClicksView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)

    def get(self, request):
        
        todays_date = datetime.now().date()
        seven_days_ago = todays_date - timedelta(days=7)
        sup_code = request.user.source_id
        resp_obj = RespondentDetail.objects.filter(source = sup_code, url_type='Live', end_time_day__lte=todays_date, end_time_day__gte=seven_days_ago).values('end_time_day').annotate(
            day_wise_completes=Count('resp_status', filter=Q(resp_status='4')),
            day_wise_clicks=Count('resp_status', filter=Q(resp_status__in=['1','2','3','4','5','6','7','8','9'])),
        )
        return Response(resp_obj, status=status.HTTP_200_OK)
    


class SupplierUserForgotPasswordAPI(APIView):
    # authentication_classes = (TokenAuthentication,)

    def get(self, request):
        
        email = request.GET.get('email')
        user_qs = EmployeeProfile.objects.filter(email=email)
        if user_qs:
            user_token = uuid4().hex
            UserTokenVerifyPasswordReset.objects.update_or_create(user=user_qs[0], user_token = user_token)

            send_email = sendEmailSendgripAPIIntegration(to_emails=user_qs[0].email, subject='Password Reset Mail', html_message=f'<strong> Dear {user_qs[0].first_name},</strong> <br> <strong> Please click the link below to reset your password </strong> : <br> <a href="{settings.SUPPLIER_DASHBOARD_FRONTEND_URL}#/authentication/user-set-password/{user_token}"> Reset Your Password </a> <br><br> Thanks,<br> Project Management Team')

            if send_email.status_code in [200, 201]:
                return Response({'message':'email sent for reset password in user mail id','user_token':user_token}, status=status.HTTP_200_OK)
            else:
                return Response({"error":f"We Can't Send Email Due to SendGrid Response Status-{send_email.status_code}"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message':'No User Found with this Email ID'}, status=status.HTTP_404_NOT_FOUND)
        

class SupplierUserSetPasswordAPI(APIView):
    # authentication_classes = (TokenAuthentication,)

    def post(self, request, token):
        password = request.data.get('password')
        confirmpassword = request.data.get('confirmpassword')
        if password != confirmpassword:
            return Response({'message': 'Password does not match with confirm password'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_token_qs = UserTokenVerifyPasswordReset.objects.get(user_token=token)
            if user_token_qs:
                hashed_password = make_password(password)
                user_obj = user_token_qs.user
                user_obj.password = hashed_password
                user_obj.save(force_update=True, update_fields=['password'])
                user_token_qs.delete()

                return Response({'message':'Password Updated Successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'message':'No User Found with this Token'}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({"error":"This link has been expired..!"}, status=status.HTTP_400_BAD_REQUEST)
        


class SupplierUserChangePasswordAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)

    def put(self, request, user_id):

        try:
            if 'password' in request.data:
                instance = EmployeeProfile.objects.get(id = user_id)
                instance.password = make_password(self.request.data["password"])
                instance.save()
                return Response({'success':'Password Changed Successfully..!'}, status=status.HTTP_200_OK)
            else:
                return Response({"error":"Password Is Required..!"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': 'Given Employee Object not found..!'}, status=status.HTTP_400_BAD_REQUEST)
        

class EngninxSupplierUserRegisterScriptAPI(APIView):
    authentication_classes = (TokenAuthentication,)

    def post(self, request):
        data = request.data

        first_name = data.get('first_name','')
        last_name = data.get('last_name','')
        email = data.get('email','')
        contact_number = data.get('contact_number','')
        supplier_id = data.get('supplier_id','')
        password = data.get('password','')
        date_of_joinig = data.get('date_of_joinig','')
        is_active = data.get('is_active')
        try:
            user_register = EmployeeProfile.objects.create(
                first_name = first_name,
                last_name = last_name,
                email = email.lower(),
                contact_number = contact_number,
                source_id = supplier_id,
                user_type = '2',
                emp_type = '10',
                password = make_password(password),
                date_of_joinig = date_of_joinig,
                created_by = request.user,
                is_active = is_active
            )

            return Response({"message":"Employee Registration On Panel ViewPoint Successfully.!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":f"Exception=={e}"}, status=status.HTTP_400_BAD_REQUEST)


class SupplierDashboardEmployeeListAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (SupplierEmployeePermission,)

    def get(self, request):

        employee_obj = EmployeeProfile.objects.filter(emp_type__in = ['10','12'], user_type = '2').only('id','first_name','last_name','email','source_id').values('id','first_name','last_name','email','source_id')

        return Response(employee_obj, status=status.HTTP_200_OK)



class EmployeeSourceIDUpdateAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (AdminSupplierEmployeePermission,)

    def post(self, request):
        data = request.data

        source_id = data.get('source_id')

        if source_id not in ['', None]:
            employee_obj = EmployeeProfile.objects.filter(email = 'tech@panelviewpoint.com', emp_type = '12', user_type = '2')
            employee_obj.update(source_id = source_id)
            return Response({"message":"User Source Request Update Successfully.!"}, status=status.HTTP_200_OK)
        else:
            return Response({"error":"All Fields Are Required!"}, status=status.HTTP_200_OK)

        
