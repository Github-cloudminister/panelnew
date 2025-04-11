from django.http import HttpResponse
from django.db.models import *
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import Coalesce

# rest_framework imports
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

# third_party module imports
from knox.auth import TokenAuthentication
from hashlib import blake2b
from copy import deepcopy
import random,string, csv, pandas as pd,concurrent.futures

# in-project imports
from ClientSupplierAPIIntegration.TolunaClientAPI.views import CustomerAuthPermission
from Logapp.views import *
from Invoice.models import DraftInvoice
from Project.common import CountryViewSet, LanguageViewSet, ProjectGroupSupplierViewSet, ProjectGroupViewSet, ProjectViewSet, project_group_statistics_create, project_group_statistics_update
from Project.models import *
from Project.serializers import *
from SupplierAPI.lucid_supplier_api.buyer_surveys import update_lucid_survey_Qualifications
from Surveyentry.models import RespondentDetail as RespondentDetailsRelationalfield
from Project.permissions import *
from Prescreener.models import ProjectGroupPrescreener
from django.conf import settings
from Project.panel_view import *
from SupplierAPI.disqo_supplier_api.create_or_update_project import *
from Project.paginations import *
from Questions.models import *
from Prescreener.models import *
from affiliaterouter.models import RountingPriority
from automated_email_notifications.project_custom_functions import update_status
from datetime import datetime, date, timedelta
from Bid.models import Bid

max_workers = 10 if settings.SERVER_TYPE == 'localhost' else 50

class CountryView(APIView):

    '''
        method to get the list of all country objects.
    '''
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, CountryPermission) 
    common_class = CountryViewSet

    def get(self, request):

        country_list = self.common_class.country_list().values()
        return Response(country_list,status=status.HTTP_200_OK)


class LanguageView(APIView):

    '''
        method to get the list of all language objects.
    '''
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, LanguagePermission)
    common_class = LanguageViewSet

    def get(self, request):

        language_list = self.common_class.language_list().values()
        return Response(language_list,status=status.HTTP_200_OK)


class ProjectView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, ProjectPermission)
    serializer_class = ProjectSerializer
    common_class = ProjectViewSet
    '''
        method to get the list of all project objects.
    '''

    def get(self, request):
        try:
            pageNumber = int(request.GET.get('page'))
        except:
            pageNumber = 1
        
        startproject = (pageNumber-1)*20
        endproject = (pageNumber)*20

        project_obj_list = self.common_class.project_list()[startproject:endproject].values()
        return Response(project_obj_list, status=status.HTTP_200_OK)


    def post(self, request):
        try:
            project_obj = self.common_class.project_create(request,**request.data)
            serializer = self.serializer_class(project_obj)
            project_log(serializer.data,'',project_obj.project_status,project_obj.id,request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as error:
            project_error_log(error,request.user)
            return Response({'error': f'{error} Error Found In Project..!'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, ProjectUpdatePermission)
    serializer_class = ProjectSerializer
    common_class = ProjectViewSet

    '''
        method to get the one project group objects.
    '''

    def get(self, request, project_id):
        
        try:
            project_obj = self.common_class.project_get(project_id)
            serializer = self.serializer_class(project_obj)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except:
            return Response({'error': 'No data found for the provided Project-ID..!'}, status=status.HTTP_400_BAD_REQUEST)

    '''
        method to get the one project group update.
    '''

    def put(self, request, project_id):

        try:
            project_obj = self.common_class.project_update(request,project_id,**request.data)
            serializer = self.serializer_class(project_obj)
            project_log('',serializer.data,project_obj.project_status,project_obj.id,request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as error:
            project_error_log(error,request.user)
            return Response({'error': f'{error} Error Found In Project..!'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectListStatistics2View(APIView, MyPaginationMixin):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        filtered_data = dict(request.data)
        try:
            last_day_from = filtered_data['last_day_from']
        except:
            last_day_from = None
        
        total_visits_query = Q(respondentdetailsrelationalfield__respondent__url_type='Live')
        last_24hr_visits_query = Q(respondentdetailsrelationalfield__respondent__url_type='Live', respondentdetailsrelationalfield__respondent__end_time__gte=datetime.now() - timedelta(hours = 24))
        starts_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[3,4,5,6,7,8,9], respondentdetailsrelationalfield__respondent__url_type='Live')
        completes_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,9], respondentdetailsrelationalfield__respondent__url_type='Live')
        last_24hr_completes_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,9], respondentdetailsrelationalfield__respondent__url_type='Live', respondentdetailsrelationalfield__respondent__end_time__gte=datetime.now() - timedelta(hours = 24))
        incompletes_query = Q(respondentdetailsrelationalfield__respondent__resp_status=3, respondentdetailsrelationalfield__respondent__url_type='Live')
        terminates_query = Q(respondentdetailsrelationalfield__respondent__resp_status=5, respondentdetailsrelationalfield__respondent__url_type='Live')
        quota_full_query = Q(respondentdetailsrelationalfield__respondent__resp_status=6, respondentdetailsrelationalfield__respondent__url_type='Live')
        security_terminate_query = Q(respondentdetailsrelationalfield__respondent__resp_status=7, respondentdetailsrelationalfield__respondent__url_type='Live')
        revenue_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,9], respondentdetailsrelationalfield__respondent__url_type='Live')
        
        if last_day_from != None:
            noofdays = int(last_day_from)
            today = date.today()
            timeframe = today - timedelta(days=noofdays)
            
            start_time_query = Q(respondentdetailsrelationalfield__respondent__start_time__date__range=(timeframe,today))
            
            total_visits_query = total_visits_query & start_time_query
            starts_query = starts_query & start_time_query
            completes_query = completes_query & start_time_query
            incompletes_query = incompletes_query & start_time_query
            terminates_query = terminates_query & start_time_query
            quota_full_query = quota_full_query & start_time_query
            security_terminate_query = security_terminate_query & start_time_query
            revenue_query = revenue_query & start_time_query
            
        project_list = Project.objects.all().order_by('-id')

        try:
            project_search = filtered_data['project_search']
            if project_search not in [None, '']:
                project_list1 = project_list.filter(Q(project_name__icontains = project_search) | Q(project_number__icontains = project_search))
                if not project_list1:
                    project_list2 = project_list.filter(group_project__project_group_number=project_search).distinct()

                project_list = project_list1 if project_list1 else project_list2
                
        except:
            pass
        try:
            project_manager = filtered_data['project_manager']
            if project_manager not in [None, '', [], ['']]:
                project_list = project_list.filter(project_manager__in = project_manager)
        except:
            pass
        try:
            project_status = filtered_data['project_status']
            if project_status not in [None, '', [], ['']]:
                project_list = project_list.filter(project_status__in = project_status)
        except:
            pass
        try:
            project_customer = filtered_data['project_customer']
            if project_customer not in [None, '', [], ['']]:
                project_list = project_list.filter(project_customer__in = project_customer)
        except:
            pass

        project_list = project_list.select_related('respondentdetailsrelationalfield')\
            .values(
                'id',
                'project_name',
                'project_number', 
                'project_type', 
                'project_revenue_month', 
                'project_revenue_year', 
                'project_status', 
                'project_customer', 
                'project_manager',
                'created_at',
                'project_criticality_level',
                'project_list_notes'
            ).distinct()\
            .annotate(
                total_visits = Count('respondentdetailsrelationalfield', filter=total_visits_query, distinct=True), 
                starts = Count('respondentdetailsrelationalfield', filter=starts_query, distinct=True),
                completes = Count('respondentdetailsrelationalfield', filter=completes_query, distinct=True),
                incompletes = Count('respondentdetailsrelationalfield', filter=incompletes_query, distinct=True), 
                terminates = Count('respondentdetailsrelationalfield', filter=terminates_query, distinct=True), 
                quota_full = Count('respondentdetailsrelationalfield', filter=quota_full_query, distinct=True), 
                security_terminate = Count('respondentdetailsrelationalfield', filter=security_terminate_query, distinct=True),
                last_24hr_completes_query = Count('respondentdetailsrelationalfield', filter=last_24hr_completes_query, distinct=True),
                last_24hr_visits_query = Count('respondentdetailsrelationalfield', filter=last_24hr_visits_query, distinct=True),
            )

        project_list = project_list.annotate(revenue = Sum('respondentdetailsrelationalfield__respondent__project_group_cpi',filter=revenue_query))
        return Response(project_list, status=status.HTTP_200_OK)


class ProjectStatusUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectSerializer
    common_class = ProjectViewSet

    def get(self, request, project_id):

        try:
            project_obj = self.common_class.project_get(project_id)
            serializer = self.serializer_class(project_obj)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except:
            return Response({'error': 'No data found for the provided Project-ID..!'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, project_id):

        project_obj = self.common_class.project_get(project_id)

        if project_obj != None:
                # Not Allowed to Change the Status if not Live Or Paused
            if request.data['project_status'] not in ('Live','Paused','Closed','Cancel','Reconciled'):

                if request.data['project_status'] == 'Archived' and project_obj.project_status in ('Closed','Reconciled'):
                    # UPDATE COMPLETED RESPONDENTS TO CLIENT REJECTED WHENEVER THE PROJECT GOES INTO ARCHIVE
                    RespondentDetail.objects.filter(project_number=project_obj.project_number, resp_status='4').update(resp_status='8')                        
                else:
                    return Response(data={'message':'You are not allowed to change the status except for "Live", "Paused","Closed","Reconciled" Or "Cancel"'}, status=status.HTTP_406_NOT_ACCEPTABLE)

            project_status = request.data['project_status']
            project_status_dict = dict(Project._meta.get_field('project_status').choices)
            project_status_list = list(project_status_dict.keys())

            if project_status in project_status_list:
                project_obj.modified_by=request.user
                project_obj.save()
                update_status(project_id, project_status, action='change-project-status',user=request.user)
                return Response({'project_status': project_status}, status=status.HTTP_200_OK)
            else:
                return Response({'error':'This action is restricted..!'}, status=status.HTTP_400_BAD_REQUEST)                    
        else:
            return Response({'error': 'No data found for the provided Project-ID..!'}, status=status.HTTP_400_BAD_REQUEST)

class ProjectGroupView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, ProjectGroupPermission)
    serializer_class = ProjectGroupSerializer
    common_class = ProjectGroupViewSet

    '''
        method to get the list of all Project Group objects.
    '''

    def get(self, request):
        country_code = request.GET.get('country_code','').strip()
        language_code = request.GET.get('language_code','').strip()
        status = request.GET.get('status', '').strip()

        project_group_obj = self.common_class.project_group_list().select_related('project', 'project_group_country', 'project_group_language')
        if country_code not in ['', None]:
            project_group_obj = project_group_obj.filter(project_group_country__country_code__in = country_code)
        if language_code not in ['', None]:
            project_group_obj = project_group_obj.filter(project_group_language__language_code = language_code)
        if status not in ['', None]:
            project_group_obj = project_group_obj.filter(project_group_status__in = status)

        group_list = project_group_obj.values(
            'project_group_number',
            'project_group_name',
            'created_at',
            project_group_id=F('id'),
            project_group_country_code=F('project_group_country__country_code'),
            project_group_language_code=F('project_group_language__language_code'),
            project_number=F('project__project_number'),
            completes=F('project_group_completes'),
            incidence=F('project_group_incidence'),
            loi=F('project_group_loi'),
            cpi=F('project_group_cpi'),
            status=F('project_group_status'),
            project_notes=F('project__project_list_notes'),
            project_customer=F('project__project_customer__cust_org_name'),
            ).order_by('-project')
        return Response(group_list)
    
    '''
        method to create the Project Group.
    '''

    def post(self, request):

        try:
            # Project Group create
            if not(request.data['project_group_enddate'] <= request.data['project_group_startdate']) and not(request.data['project_group_enddate'] <= str(date.today())):
                project_group_obj = self.common_class.project_group_create(request,**request.data)

                if project_group_obj and project_group_obj.project_group_country.country_code == 'US' and project_group_obj.project_group_language.language_code == 'en':
                        # Add Defualt Questions when Project-Group Created for US/English
                        self.common_class.project_group_create_update_default_question(project_group_obj)

                serializer = self.serializer_class(project_group_obj)
                projectgroup_log(serializer.data,'',project_group_obj.project_group_status,project_group_obj.id,request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({"error":"end date must be greater than currentdate.! OR end date must be greater than startdate.!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            project_group_error_log(error,request.user)
            return Response({'error': f'{error} Error Found in ProjectGroup..!'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectGroupUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, ProjectGroupUpdatePermission)
    serializer_class = ProjectGroupGetSerializer
    common_class = ProjectGroupViewSet

    '''
        class to get a single instance of Project Group object and to update it.
    '''

    def get(self, request, project_group_id):

        try:
            project_group_obj = self.common_class.project_group_get(project_group_id)
            serializer = self.serializer_class(project_group_obj)
            return Response(serializer.data,status=status.HTTP_200_OK)
        except:
            return Response({'error': 'No data found for the provided ProjectGroup-ID..!'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, project_group_id):

        try:
            if not(request.data['project_group_enddate'] <= request.data['project_group_startdate']) and not(request.data['project_group_enddate'] <= str(date.today())):
                project_group_obj = self.common_class.project_group_update(request,project_group_id,**request.data)
                serializer = self.serializer_class(project_group_obj)
                projectgroup_log('',serializer.data,project_group_obj.project_group_status,project_group_obj.id,request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error":"end date must be greater than currentdate.! OR end date must be greater than startdate.!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            project_group_error_log(error,request.user)
            return Response({'error': f'{error} Error Found in ProjectGroup..!'}, status=status.HTTP_400_BAD_REQUEST)

class ProjectGroupStatusUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectGroupStatusUpdateSerializer
    serializer_class = ProjectGroupSerializer
    common_class = ProjectGroupViewSet

    def get(self, request, project_group_id):

        project_group_obj = self.common_class.project_group_get(project_group_id)
        if project_group_obj != None:
            serializer = self.serializer_class(project_group_obj)
            return Response(serializer.data)
        else:
            return Response({'error': 'No data found for the provided ProjectGroup-ID..!'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, project_group_id):

        try:
            project_group_obj = self.common_class.project_group_get(project_group_id)   
            # Not Allowed to Change the Status if not Live Or Paused
            if request.data['project_group_status'] not in ('Live','Paused'):
                return Response(data={'message':'You are not allowed to change the status except for "Live" or "Paused"'}, status=status.HTTP_406_NOT_ACCEPTABLE)

            project_group_status = request.data['project_group_status']
            project_group_status_dict = dict(ProjectGroup._meta.get_field('project_group_status').choices)
            project_group_status_list = list(project_group_status_dict.keys())

            if project_group_status in project_group_status_list:
                project_group_obj.modified_by = request.user
                project_group_obj.save()
                
                update_status(project_group_id, project_group_status, action='change-projectgroup-status',user=request.user)

                if project_group_status != 'Live' and project_group_status == 'Live':
                    project_group_obj.prjgrp_status_setLive_timestamp = datetime.now()
                    project_group_obj.save()
                return Response({'project_group_status': project_group_status}, status=status.HTTP_200_OK)
            else:
                return Response({'error':'This action is restricted..!'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as error:
            project_group_error_log(error,request.user)
            return Response({'error': f'{error} Error Found in ProjectGroup..!'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectGroupSupplierStatusUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectGroupSupplierStatusUpdateSerializer
    common_class = ProjectGroupSupplierViewSet


    def get(self, request, supplier_id):

        try:
            project_group_supplier_obj = self.common_class.project_group_supplier_get(supplier_id)
            serializer = self.serializer_class(project_group_supplier_obj)
            return Response(serializer.data)
        except:
            return Response({'error': 'No data found for the provided ProjectGroupSupplier-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, supplier_id):

        try:
            project_group_supp_obj = self.common_class.project_group_supplier_get(supplier_id)
            if request.data['supplier_status'] == 'Reconciled' or request.data['supplier_status'] == 'Invoiced':
                return Response({'error':'This action is restricted..!'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                supplier_status = request.data['supplier_status']
                update_status(project_group_supp_obj.id, supplier_status, action='change-projectgroupsupplier-status')
                return Response({'supplier_status': supplier_status}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'No data found for the provided ProjectGroupSupplier-ID..!'}, status=status.HTTP_404_NOT_FOUND)


class ProjectDetailGroup(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_id):

        ip_check_survey_data = self.request.GET.get('ip_check_survey')
        project_group_number = self.request.GET.get('project_group_number',None)
        project_group_status = self.request.GET.get('project_group_status',None)

        # create manual pagination for project group list
        page = int(self.request.GET.get('page',1))
        end = 15*page
        start = end-15

        if project_group_number and project_group_status == None:
            project_list = ProjectGroup.objects.filter(project__id=project_id,project_group_number=project_group_number).order_by('-id')[start:end]
        if project_group_status and project_group_number == None:
            project_list = ProjectGroup.objects.filter(project__id=project_id,project_group_status=project_group_status).order_by('-id')[start:end]
        if project_group_status and project_group_number:
            project_list = ProjectGroup.objects.filter(project__id=project_id,project_group_status=project_group_status,project_group_number=project_group_number).order_by('-id')[start:end]
        if project_group_number == None and project_group_status == None:
            project_list = ProjectGroup.objects.filter(project__id=project_id).order_by('-id')[start:end]

        total_visits_query =  Q(respondentdetailsrelationalfield__respondent__url_type='Live')
        starts_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[3,4,5,6,7,8,9], respondentdetailsrelationalfield__respondent__url_type='Live')
        completes_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,9], respondentdetailsrelationalfield__respondent__url_type='Live')
        incompletes_query = Q(respondentdetailsrelationalfield__respondent__resp_status=3, respondentdetailsrelationalfield__respondent__url_type='Live')
        terminates_query = Q(respondentdetailsrelationalfield__respondent__resp_status=5, respondentdetailsrelationalfield__respondent__url_type='Live')
        quota_full_query = Q(respondentdetailsrelationalfield__respondent__resp_status=6, respondentdetailsrelationalfield__respondent__url_type='Live')
        security_terminate_query = Q(respondentdetailsrelationalfield__respondent__resp_status=7, respondentdetailsrelationalfield__respondent__url_type='Live')
        revenue_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,9], respondentdetailsrelationalfield__respondent__url_type='Live')

        if ip_check_survey_data == "1":
            project_list = project_list.values('id','project_group_number','project_group_name')
        else:
            project_list = project_list.select_related('respondentdetailsrelationalfield')\
                .values(
                    'id',
                    'project_group_number',
                    'client_survey_number',
                    'project_group_name', 
                    'project_audience_type', 
                    'project_group_loi', 
                    'project_group_completes', 
                    'project_group_cpi', 
                    'project_group_startdate', 
                    'project_group_enddate',
                    'project_group_status',
                    'excluded_project_group',
                    'project_group_surveyurl',
                    'project_device_type',
                    'project_group_client_url_type',
                    'project_group_clicks',
                    'enable_panel',
                    'project_group_liveurl',
                    'project_group_testurl',
                    'project_group_incidence'
                ).annotate(
                    total_visits = Count('respondentdetailsrelationalfield', filter=total_visits_query, distinct=True), 
                    starts = Count('respondentdetailsrelationalfield', filter=starts_query, distinct=True),
                    completes = Count('respondentdetailsrelationalfield', filter=completes_query, distinct=True),
                    incompletes = Count('respondentdetailsrelationalfield', filter=incompletes_query, distinct=True), 
                    terminates = Count('respondentdetailsrelationalfield', filter=terminates_query, distinct=True), 
                    quota_full = Count('respondentdetailsrelationalfield', filter=quota_full_query, distinct=True), 
                    security_terminate = Count('respondentdetailsrelationalfield', filter=security_terminate_query, distinct=True),
                    revenue = Sum('respondentdetailsrelationalfield__respondent__project_group_cpi',filter=revenue_query),
                    median_LOI = ExpressionWrapper(
                            Value(
                                round(
                                    float(
                                        median_value(
                                            RespondentDetail.objects.filter(
                                                resp_status__in=[4,9], 
                                                url_type='Live', 
                                                project_group_number=F('project_group_number'), 
                                                source=F('source')
                                            ),'duration'
                                        )
                                    ),0
                                )
                            ), output_field=models.FloatField()
                        )                
                )
        if project_list:
            return Response(project_list, status=status.HTTP_200_OK)
        else:
            return Response({'message':"No More Data Available.!"}, status=status.HTTP_400_BAD_REQUEST)



class ProjectGroupSupplierView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, ProjectGroupSupplierPermission)
    serializer_class = ProjectGroupSupplierSerializer
    common_class = ProjectGroupSupplierViewSet

    '''
        method to get the list of all project group supplier objects.
    '''

    def get(self, request):

        grp_supp_list = self.common_class.project_group_supplier_list()
        serializer = self.serializer_class(grp_supp_list, many=True)
        return Response(serializer.data)

    '''
        method to Create the Project Group Supplier objects.
    '''

    def post(self, request):
        
        try:
            project_group_supplier_obj = self.common_class.project_group_supplier_create(request,**request.data)
            serializer = self.serializer_class(project_group_supplier_obj)
            projectgroupsupplier_log(request.data,'',project_group_supplier_obj,project_group_supplier_obj.supplier_org.id,project_group_supplier_obj.project_group.id,project_group_supplier_obj.supplier_status,request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except:
            return Response(data={'error': 'Supplier not Add into Survey, Need to Live First..!'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectGroupSupplierUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, ProjectGroupSupplierUpdatePermission)
    serializer_class = ProjectGroupSupplierSerializer
    common_class = ProjectGroupSupplierViewSet

    '''
        class to get a single instance of project group supplier object and to update it.
    '''

    def get(self, request, proj_grp_supp_id):

        try:
            proj_grp_supp_id = self.common_class.project_group_supplier_get(proj_grp_supp_id)
            serializer = self.serializer_class(proj_grp_supp_id)
            return Response(serializer.data)
        except:
            return Response({'error': 'No data found for the provided ProjectGroup-Supplier-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, proj_grp_supp_id):

        try:
            proj_grp_supp_obj = self.common_class.project_group_supplier_update(request,proj_grp_supp_id,**request.data)
            serializer = self.serializer_class(proj_grp_supp_obj)
            projectgroupsupplier_log('',request.data,proj_grp_supp_obj,proj_grp_supp_obj.supplier_org.id,proj_grp_supp_obj.project_group.id,proj_grp_supp_obj.supplier_status,request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'No data found for the provided ProjectGroup-ID..!'}, status=status.HTTP_400_BAD_REQUEST)

class ProjectRespondentDetailView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_number):

        filtered_data = dict(request.data)
        project_list = Project.objects.only('project_number').filter(project_number = project_number)
        
        total_visits_query =  Q(respondentdetailsrelationalfield__respondent__url_type='Live')
        starts_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[3,4,5,6,7,8,9], respondentdetailsrelationalfield__respondent__url_type='Live')
        completes_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,9], respondentdetailsrelationalfield__respondent__url_type='Live')
        incompletes_query = Q(respondentdetailsrelationalfield__respondent__resp_status=3, respondentdetailsrelationalfield__respondent__url_type='Live')
        terminates_query = Q(respondentdetailsrelationalfield__respondent__resp_status=5, respondentdetailsrelationalfield__respondent__url_type='Live')
        quota_full_query = Q(respondentdetailsrelationalfield__respondent__resp_status=6, respondentdetailsrelationalfield__respondent__url_type='Live')
        security_terminate_query = Q(respondentdetailsrelationalfield__respondent__resp_status=7, respondentdetailsrelationalfield__respondent__url_type='Live')
        revenue_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,9], respondentdetailsrelationalfield__respondent__url_type='Live')

       

        project_list = project_list.only(
            'id',
            'project_name',
            'project_number', 
            'project_type', 
            'project_revenue_month', 
            'project_revenue_year', 
            'project_status', 
            'project_customer', 
            'project_manager',
            'created_at',
            'project_criticality_level',
            'project_list_notes'
        ).select_related('respondentdetailsrelationalfield')\
            .values(
                'id',
                'project_name',
                'project_number', 
                'project_type', 
                'project_revenue_month', 
                'project_revenue_year', 
                'project_status', 
                'project_customer', 
                'project_manager',
                'created_at',
                'project_criticality_level',
                'project_list_notes'
            ).distinct()\
            .annotate(
                total_visits = Count('respondentdetailsrelationalfield', filter=total_visits_query, distinct=True), 
                starts = Count('respondentdetailsrelationalfield', filter=starts_query, distinct=True),
                completes = Count('respondentdetailsrelationalfield', filter=completes_query, distinct=True),
                incompletes = Count('respondentdetailsrelationalfield', filter=incompletes_query, distinct=True), 
                terminates = Count('respondentdetailsrelationalfield', filter=terminates_query, distinct=True), 
                quota_full = Count('respondentdetailsrelationalfield', filter=quota_full_query, distinct=True), 
                security_terminate = Count('respondentdetailsrelationalfield', filter=security_terminate_query, distinct=True),
                expense = Coalesce(
                        Sum(
                            'respondentdetailsrelationalfield__respondent__supplier_cpi', 
                            filter=Q(respondentdetailsrelationalfield__respondent__resp_status=4, respondentdetailsrelationalfield__respondent__url_type='Live')
                        ), 0.0
                    ),
                median_LOI = ExpressionWrapper(
                        Value(
                            round(
                                float(
                                    median_value(
                                        RespondentDetail.objects.filter(
                                            resp_status__in=[4,9], 
                                            url_type='Live', 
                                            project_group_number=F('project_group_number'), 
                                            source=F('source')
                                        ),'duration'
                                    )
                                ),0
                            )
                        ), output_field=models.FloatField()
                    )                
            )

        project_list = project_list.annotate(revenue = Sum('respondentdetailsrelationalfield__respondent__project_group_cpi',filter=revenue_query))
        return Response(project_list, status=status.HTTP_200_OK)


class ProjectGroupRespondentDetailView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectGroupResponseSerializer

    def get(self, request, project_group_num):

        project_group_respondent_data = RespondentDetail.objects.filter(project_group_number=project_group_num, url_type="Live")
        try:
            if project_group_respondent_data:
                serializer = self.serializer_class(project_group_respondent_data)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'error': "No data found for the provided ProjectGroup-Number..!"}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({'error': 'Please proivde a valid entry...!'}, status=status.HTTP_404_NOT_FOUND)


class SupplierRespondentDetailView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectGroupSupplierResponseSerializer

    #Fixed by Narendra July 21, 2021
    def get(self, request, supplier_id, project_group_num):
        supplier_respondent_data = RespondentDetail.objects.filter(
            source=supplier_id, project_group_number=project_group_num, url_type='Live').exclude(source=0)
        try:
            if supplier_respondent_data:
                serializer = self.serializer_class(supplier_respondent_data)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'error': "No data found for the provided ProjectGroup-Number..!"}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({'error': 'Please proivde a valid entry...!'}, status=status.HTTP_404_NOT_FOUND)
         

class ProjectDetailedView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectDetailSerializer

    def get(self, request, project_id):

        try:
            project_group_detail_list = Project.objects.get(id=project_id)
            if project_group_detail_list:
                serializer = self.serializer_class(project_group_detail_list)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({'error': "No data found for the provided ProjectID..!"}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({'error': 'Please proivde a valid entry...!'}, status=status.HTTP_404_NOT_FOUND)


class DashboardView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        project_obj = Project.objects.filter(project_manager=request.user).aggregate(
            live_projects = Count('project_status',filter=Q(project_status='Live')),
            paused_projects = Count('project_status',filter=Q(project_status='Paused')),
            closed_projects = Count('project_status',filter=Q(project_status='Closed')),
            total_projects = Count('project_status',filter=Q(project_status='Live')) + Count('project_status',filter=Q(project_status='Paused')) + Count('project_status',filter=Q(project_status='Closed'))
        )
        return Response([project_obj], status=status.HTTP_200_OK)


class SupplierWithStatisticsView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    common_class = ProjectGroupSupplierViewSet

    def get(self, request, project_group_num):

        try:
            sup_type = request.GET.get('sup_type', '1')
            grp_supp_list = self.common_class.project_group_supplier_statistics(project_group_num,sup_type)

            if grp_supp_list.exists():
                return Response(grp_supp_list, status=status.HTTP_200_OK)
            else:
                return Response({'message': "No data found for the provided ProjectGroup-Number"}, status=status.HTTP_404_NOT_FOUND)
        except:
            return Response({'message': "No data found for the provided ProjectGroup-Number"}, status=status.HTTP_404_NOT_FOUND)


class SubSupplierWithStatisticsView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    common_class = ProjectGroupSupplierViewSet

    def get(self, request, project_group_num):

        try:
            sup_type = request.GET.get('sup_type', '5')
            sup_supplier_id = request.GET.get('sup_supplier_id')
           
            grp_supp_list = self.common_class.project_group_sub_supplier_stats(project_group_num,sup_type,sup_supplier_id)

            if grp_supp_list:
                projectgroupsubsupplierobj = ProjectGroupSubSupplier.objects.filter(
                    project_group__project_group_number = project_group_num,sub_supplier_org__id = sup_supplier_id).last()
                grp_supp_list['sub_supplier_survey_url'] = projectgroupsubsupplierobj.sub_supplier_survey_url
                return Response(grp_supp_list, status=status.HTTP_200_OK)
            else:
                return Response({'message': "No data found for the provided ProjectGroup-Number"}, status=status.HTTP_200_OK)
        except:
            return Response({'message': "No data found for the provided ProjectGroup-Number"}, status=status.HTTP_200_OK)


class SupplierWiseProjectGroupView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request,project_no,supplier_id):

        project_group_supplier_obj = ProjectGroupSupplier.objects.filter(project_group__project__project_number=project_no,supplier_org=supplier_id).values(
            'id',
            'project_group__project__project_number',
            'project_group',
            'supplier_org',
            'clicks',
            'cpi',
            'supplier_survey_url',
            'supplier_internal_terminate_redirect_url',
            'supplier_terminate_no_project_available',
            'supplier_status',
            supplier_complete_url = F('supplier_completeurl'),
            supplier_terminate_url = F('supplier_terminateurl'),
            supplier_quotafull_url = F('supplier_quotafullurl'),
            supplier_securityterminate_url = F('supplier_securityterminateurl'),
            supplier_postback_url = F('supplier_postbackurl'),
            total_N=F('completes'),
        )

        return Response({"project_group_supplier_obj":project_group_supplier_obj})


class ProjectGroupCopyView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, project_group_id):

        try:
            project_group_obj = ProjectGroup.objects.get(id=project_group_id)
            new_project_group = deepcopy(project_group_obj)
            new_project_group.id=None
            new_project_group.project_device_type = project_group_obj.project_device_type
            new_project_group.enable_panel = False    ## OpinionsDeal Panel 
            new_project_group.ad_enable_panel = False    ## AD Panel 
            new_project_group.save()
            new_project_group.project_group_number = 1000000 + int(new_project_group.id)
            new_project_group.excluded_project_group = project_group_obj.excluded_project_group + [str(new_project_group.project_group_number)]
            

            key_value = 'LTauDqcaX4PdeBANhj3eLfkfrN65QEjhJ'

            h = blake2b(digest_size=25)
            h1 = blake2b(digest_size=25)
            grp_num = bin(int(new_project_group.project_group_number))
            h.update(grp_num.encode())
            val = h.hexdigest() + key_value
            h1.update(val.encode())

            new_project_group.project_group_redirectID = project_group_obj.project.project_redirectID
            S_value = h.hexdigest()
            R_value = h1.hexdigest()
            new_project_group.project_group_encodedS_value = S_value
            new_project_group.project_group_encodedR_value = R_value
            new_project_group.project_group_surveyurl = settings.SURVEY_URL+"survey?glsid=" + new_project_group.project_group_encodedS_value
            new_project_group.project_group_status = 'Booked'
            new_project_group.project_group_name = "Copy of "+ new_project_group.project_group_name
            new_project_group.save()
            projectgroup_log(f'Copy Project From {project_group_obj.project_group_number}','',new_project_group.project_group_status,new_project_group.id,request.user)
            prescreener_questions_obj = ProjectGroupPrescreener.objects.filter(
                project_group_id = project_group_obj,is_enable = True,translated_question_id__is_active = True)
            
            for question in prescreener_questions_obj:
                ProjectGroupPrescreener_obj = ProjectGroupPrescreener.objects.create(
                    sequence = question.sequence,
                    project_group_id = new_project_group,
                    translated_question_id = question.translated_question_id)
                if question.translated_question_id.parent_question.parent_question_type in ['SS','MS','CTZIP']:
                    ProjectGroupPrescreener_obj.allowedoptions.add(*list(question.allowedoptions.values_list('id', flat=True)))
                if question.translated_question_id.parent_question.parent_question_type in ['NU','ZIP']:
                    ProjectGroupPrescreener_obj.allowedRangeMin = question.allowedRangeMin
                    ProjectGroupPrescreener_obj.allowedRangeMax = question.allowedRangeMax
                    ProjectGroupPrescreener_obj.allowed_zipcode_list = question.allowed_zipcode_list
                ProjectGroupPrescreener_obj.save()

            return Response({'msg':'Project Group copied successfully..!', 'id':new_project_group.id}, status=status.HTTP_200_OK)
        except Exception as error:
            project_group_error_log(error,request.user)
            return Response({'error':'Given Project Group ID does not exist..!'}, status=status.HTTP_404_NOT_FOUND)


class ZipCodeView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_group_number):

        zipcode_list = ZipCode.objects.filter(project_group_id__project_group_number=project_group_number)
        serializer = ZipCodeSerializer(zipcode_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, project_group_number):

        csv_file = request.FILES['file'] if request.FILES else None

        try:
            project_obj = ProjectGroup.objects.get(project_group_number = project_group_number)
            question_obj = TranslatedQuestion.objects.get(
                apidbcountrylangmapping__lanugage_id__language_code = project_obj.project_group_language.language_code,
                apidbcountrylangmapping__country_id__country_code = project_obj.project_group_country.country_code,
                parent_question_type = 'ZIP')
            projectgroupsupplierlist = ProjectGroupSupplier.objects.filter(project_group = project_obj)
            if csv_file and csv_file.name.endswith('.csv'):
                detail_list = list(map(str, pd.read_csv(csv_file).ZIP_code.to_list()))
                project_grp_pre_obj,created = ProjectGroupPrescreener.objects.update_or_create(
                    project_group_id = project_obj,
                    translated_question_id = question_obj,
                    defaults={'is_enable' : True,'allowed_zipcode_list' : detail_list})
                if projectgroupsupplier := projectgroupsupplierlist.filter(supplier_org__supplier_url_code = 'lucid').first():
                    update_lucid_survey_Qualifications(projectgroupsupplier,project_grp_pre_obj.id)     
                if projectgroupsupplier := projectgroupsupplierlist.filter(supplier_org__supplier_url_code = 'disqo').first():
                    DisqoAPIUpdateProjectFunc(projectgroupsupplier)     
                return Response({'success':'Data upload success...!'}, status=status.HTTP_201_CREATED)
            else:
                detail_list = []
                ProjectGroupPrescreener.objects.update_or_create(
                        project_group_id = project_obj,
                        translated_question_id = question_obj,
                        defaults={'is_enable' : True,'allowed_zipcode_list' : detail_list})
                return Response({'success':'Data upload success...!'}, status=status.HTTP_201_CREATED)    
        except:
            return Response({'error':'Please Enter Valid Format/Values...!'}, status=status.HTTP_400_BAD_REQUEST)


class MultipleURLView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, project_group_number):
        try:
            group_project = ProjectGroup.objects.get(project_group_number=project_group_number)
            if group_project.project_group_client_url_type == "2":
                try:
                    client_urls_csv = request.FILES['multiple_urls']
                    if not client_urls_csv.name.endswith('.csv'):
                        return Response({'error':'Please upload a CSV file format..!'}, status=status.HTTP_400_BAD_REQUEST)

                    # Read CSV for Multiple URLs
                    csv_dataframe = pd.read_csv(client_urls_csv)
                    for i,j in csv_dataframe.iterrows():
                        try:
                            multiple_url_obj = MultipleURL.objects.get(client_url_id=j[0], project_group__project_group_number = project_group_number)
                            multiple_url_obj.client_url = j[1]
                            multiple_url_obj.save()
                        except ObjectDoesNotExist:
                            multiple_url_obj = MultipleURL(project_group=group_project, client_url=j[1], client_url_id=j[0])
                            multiple_url_obj.save()
                    return Response({'msg': 'Multiple URL added Successfully..!'}, status=status.HTTP_200_OK)
                except:
                    return Response({'error': 'Please upload a CSV file..!'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Please change client url type..!'}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error': 'Invalid Project Group Number..!'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectListStatisticsExcelDownloadView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        filtered_data = dict(request.data)

        try:
            last_day_from = filtered_data['last_day_from']
        except:
            last_day_from = None
        
        total_visits_query = Q(respondentdetailsrelationalfield__respondent__url_type='Live')
        starts_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[3,4,5,6,7,8,9], respondentdetailsrelationalfield__respondent__url_type='Live')
        completes_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,9], respondentdetailsrelationalfield__respondent__url_type='Live')
        incompletes_query = Q(respondentdetailsrelationalfield__respondent__resp_status=3, respondentdetailsrelationalfield__respondent__url_type='Live')
        terminates_query = Q(respondentdetailsrelationalfield__respondent__resp_status=5, respondentdetailsrelationalfield__respondent__url_type='Live')
        quota_full_query = Q(respondentdetailsrelationalfield__respondent__resp_status=6, respondentdetailsrelationalfield__respondent__url_type='Live')
        security_terminate_query = Q(respondentdetailsrelationalfield__respondent__resp_status=7, respondentdetailsrelationalfield__respondent__url_type='Live')
        avg_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,9], respondentdetailsrelationalfield__respondent__url_type='Live')
        
        if last_day_from != None:
            noofdays = int(last_day_from)
            today = date.today()
            timeframe = today - timedelta(days=noofdays)
            
            start_time_query = Q(respondentdetailsrelationalfield__respondent__start_time__date__range=(timeframe,today))
            
            total_visits_query = total_visits_query & start_time_query
            starts_query = starts_query & start_time_query
            completes_query = completes_query & start_time_query
            incompletes_query = incompletes_query & start_time_query
            terminates_query = terminates_query & start_time_query
            quota_full_query = quota_full_query & start_time_query
            security_terminate_query = security_terminate_query & start_time_query
            avg_query = avg_query & start_time_query

        project_list = Project.objects.all()

        try:
            project_search = filtered_data['project_search']
            if project_search not in [None, '']:
                project_list = project_list.filter(Q(project_name__icontains = project_search) | Q(project_number__icontains = project_search))
        except:
            pass
        try:
            project_manager = filtered_data['project_manager']
            if project_manager not in [None, '', [], ['']]:
                project_list = project_list.filter(project_manager__in = project_manager)
        except:
            pass
        try:
            project_status = filtered_data['project_status']
            if project_status not in [None, '', [], ['']]:
                project_list = project_list.filter(project_status__in = project_status)
        except:
            pass
        try:
            project_customer = filtered_data['project_customer']
            if project_customer not in [None, '', [], ['']]:
                project_list = project_list.filter(project_customer__in = project_customer)
        except:
            pass

        project_list = project_list.select_related('respondentdetailsrelationalfield')\
            .values(
                'project_name',
                'project_number', 
                'project_revenue_month', 
                'project_revenue_year', 
                'project_status', 
                'project_customer__cust_org_name', 
                'project_manager__first_name',
                'project_manager__last_name',
                'created_at'
            ).distinct()\
            .annotate(
                total_visits = Count('respondentdetailsrelationalfield', filter=total_visits_query), 
                starts = Count('respondentdetailsrelationalfield', filter=starts_query),
                completes = Count('respondentdetailsrelationalfield', filter=completes_query),
                incompletes = Count('respondentdetailsrelationalfield', filter=incompletes_query), 
                terminates = Count('respondentdetailsrelationalfield', filter=terminates_query), 
                quota_full = Count('respondentdetailsrelationalfield', filter=quota_full_query), 
                security_terminates = Count('respondentdetailsrelationalfield', filter=security_terminate_query), 
                revenue = Sum('respondentdetailsrelationalfield__respondent__project_group_cpi',filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,9], respondentdetailsrelationalfield__respondent__url_type='Live')), 
                cpi = Avg('respondentdetailsrelationalfield__respondent__project_group_cpi',filter=avg_query), 
            )
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=project_stats.csv'
        writer = csv.writer(response)

        header = ["Project Number", "Project Name", "Project Created Date", "Project Revenue Month", "Project Revenue Year", "Project Status", 
        "Project Customer", "Project Manager", "Total Visits", "Starts", "Completes",  "Incompletes", "Terminates", "Security Terminate", "Quota Full", "CPI"]

        writer.writerow(header)
        for project_obj in project_list:
            project_number = project_obj['project_number']
            project_name = project_obj['project_name']
            project_created_date = project_obj['created_at']
            # project_type = project_obj['project_type']
            project_revenue_month = project_obj['project_revenue_month']
            project_revenue_year = project_obj['project_revenue_year']
            project_status = project_obj['project_status']
            project_customer = project_obj['project_customer__cust_org_name']
            project_manager = f"{project_obj['project_manager__first_name']} {project_obj['project_manager__last_name']}"
            total_visits = project_obj['total_visits']
            starts = project_obj['starts']
            completes = project_obj['completes']
            incompletes = project_obj['incompletes']
            terminates = project_obj['terminates']
            security_terminates = project_obj['security_terminates']
            quota_full = project_obj['quota_full']
            revenue = project_obj['revenue']
            cpi = project_obj['cpi']

            content = [project_number, project_name, project_created_date, project_revenue_month, project_revenue_year, project_status, project_customer, project_manager, total_visits, starts, completes, incompletes, terminates, security_terminates, quota_full, cpi, ]
            writer.writerow(content)

        return response


class ZipCodeDownloadAPIView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_group_number):
        resp_obj = list(ZipCode.objects.filter(
            project_group_id__project_group_number=project_group_number).values_list(
                'zip_code',flat=True)) + ProjectGroupPrescreener.objects.get(
            translated_question_id__Internal_question_id = "112498",
            project_group_id__project_group_number=project_group_number,
            ).allowed_zipcode_list
        
        try:
            if len(resp_obj) > 0:
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename=' + str(project_group_number) + '.csv'
                writer = csv.writer(response)
                
                count = 0
                for resp in resp_obj:
                    if count == 0:
                        writer.writerow(["ZIP_code"])
                        count += 1
                    writer.writerow([resp])
                return response
            else:
                return Response({'error': 'There is no zipcode available in this survey'}, status=status.HTTP_400_BAD_REQUEST)
        except:
                return Response({'error': 'Question Have Some Error Please Remove Question and Add Again'}, status=status.HTTP_400_BAD_REQUEST)


class MultipleURLDownloadAPIView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_group_number):
    
        resp_obj = MultipleURL.objects.filter(project_group__project_group_number=project_group_number)

        if len(resp_obj) > 0:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=' + str(project_group_number) + '.csv'
            writer = csv.writer(response)
            
            header = ["ClientURL", "ClientURLId", "IsUsed"]
            
            count = 0
            for resp in resp_obj:
                try:
                    client_url_data = resp.client_url
                except:
                    client_url_data = 'N/A'
                try:
                    client_url_id_data = resp.client_url_id
                except:
                    client_url_id_data = 'N/A'
                try:
                    is_used_data = resp.is_used
                except:
                    is_used_data = 'N/A'
                    
                content = [client_url_data, client_url_id_data, is_used_data]
                if count == 0:
                    writer.writerow(header)
                    count += 1
                writer.writerow(content)
            return response
        else:
            return Response({'error': 'Invalid Project Group Number..!'}, status=status.HTTP_400_BAD_REQUEST)


class projectAddNotes(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_number):
        try:
            project_notes = ProjectNotesConversation.objects.filter(
                project__project_number=project_number).values(
                    'notes','created_at','created_by__first_name','created_by__last_name')
            return Response(project_notes, status=status.HTTP_200_OK)
        except:
            return Response({'message':'Project number is not correct.!'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, project_number):

        try:
            data = request.data
            critical_level = data.get('project_criticality_level',None)
            project_list_notes = data.get('project_list_notes', None)
            project_obj = Project.objects.get(project_number = project_number)
            project_obj.project_criticality_level = critical_level
            project_obj.save()
            ProjectNotesConversation.objects.create(project=project_obj,notes=project_list_notes,created_by=request.user)
            return Response({'message':'Project Notes has been updated.!'}, status=status.HTTP_200_OK) 
        except:
            return Response({'message':'Project number is not correct.!'}, status=status.HTTP_400_BAD_REQUEST)

    
class ExcludedProjectGroupGetApi(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):

        project_or_survey_no = request.data['project_or_survey_no']
        
        if 'PVP' in project_or_survey_no[0]:
            project_group_obj = ProjectGroup.objects.filter(project__project_number__in = project_or_survey_no).values('project_group_name','project_group_number')
            
            return Response({'survey-list':project_group_obj}, status=status.HTTP_200_OK)

        else:
            project_group_obj = ProjectGroup.objects.filter(project_group_number__in = list(project_or_survey_no)).values('project_group_name','project_group_number')
            
            return Response({'survey-list':project_group_obj}, status=status.HTTP_200_OK)
            

class PreLanchingSurveyCheckListApi(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, project_group_number):

        project_group_obj = ProjectGroup.objects.get(project_group_number = project_group_number)
        resp_obj = RespondentDetail.objects.filter(project_group_number = project_group_obj.project_group_number,url_type = "Test").aggregate(
            in_complete = Count('resp_status',filter=Q(resp_status = "3")),
            complete = Count('resp_status',filter=Q(resp_status = "4")),
            terminate = Count('resp_status',filter=Q(resp_status = "5")),
            quotafull = Count('resp_status',filter=Q(resp_status = "6")),
        )
        prescreener_question_obj = ProjectGroupPrescreener.objects.filter(project_group_id = project_group_obj.id, is_enable = True).values(
            question_text = F('translated_question_id__translated_question_text')
        )

        return Response({'Prescreener':prescreener_question_obj,'Test-Hits':resp_obj}, status=status.HTTP_200_OK)


class RespondentDetailCPIUpdateSupplierLevelAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, project_group_number, supplier_id):

        resp_invoice_row_details = RespondentDetail.objects.filter(
            project_group_number = project_group_number,
            respondentdetailsrelationalfield__source_id = supplier_id
        ).only('supplier_cpi','id').values(cpi = F('supplier_cpi')).annotate(
            completes = Count('id',filter=Q(resp_status__in = ['4','8','9'])))
        return Response(resp_invoice_row_details, status=status.HTTP_200_OK)


    def post(self, request,project_group_number, supplier_id):

        try:
            oldcpi = request.data['oldcpi']
            newcpi = request.data['newcpi']

            RespondentDetail.objects.filter(
                respondentdetailsrelationalfield__source_id = supplier_id,
                project_group_number = project_group_number,
                supplier_cpi = oldcpi
            ).update(supplier_cpi = newcpi)

            ProjectGroupSupplier.objects.filter(id = supplier_id,cpi = oldcpi).update(cpi=newcpi)
            return Response({'success':'Supplier CPI Update Successfully..!'}, status=status.HTTP_200_OK)
        except:
            return Response({'error':'Something Went Wrong..!'}, status=status.HTTP_400_BAD_REQUEST)

class RespondentDetailCPIUpdateProjectLevelAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, project_number, supplier_id):

        resp_invoice_row_details = RespondentDetail.objects.filter(
            project_number = project_number,
            respondentdetailsrelationalfield__source_id = supplier_id
        ).only('supplier_cpi','id').values(cpi = F('supplier_cpi')).annotate(
            surveynumber = F('project_group_number'),
            completes = Count('id',filter=Q(resp_status__in = ['4','8','9'])))
        return Response(resp_invoice_row_details, status=status.HTTP_200_OK)


    def post(self, request,project_number, supplier_id):

        try:
            for data in request.data:
                oldcpi = data['oldcpi']
                newcpi = data['newcpi']
                surveynumber = data['surveynumber']

                RespondentDetail.objects.filter(
                    respondentdetailsrelationalfield__source_id = supplier_id,
                    project_number = project_number,
                    supplier_cpi = oldcpi,
                    project_group_number = surveynumber
                ).update(supplier_cpi = newcpi)
                ProjectCPIApprovedManager.objects.filter(project__project_number = project_number).delete()
                project_supplier_cpi_update_log(oldcpi,newcpi,supplier_id,project_number,surveynumber,request.user)
            return Response({'success':'Supplier CPI Update Successfully..!'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error':'Something Went Wrong..!'}, status=status.HTTP_400_BAD_REQUEST)

class ProjectGroupStatisticsCreate(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self,request,project_number):
        
        try:
            project_group_statistics_create(project_number)
            return Response({"message":"Project Statistics Successfully Create..."}, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something Want Wrong..."}, status=status.HTTP_400_BAD_REQUEST)
        
class ProjectGroupStatisticsUpdate(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self,request,project_number):
        
        try:
            project_group_statistics_update(project_number)
            return Response({"message":"Project Statistics Successfully Updated..."}, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something Want Wrong..."}, status=status.HTTP_400_BAD_REQUEST)


class ProjectGroupSurveyPriority(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        
        try:
            project_group_list = ProjectGroup.objects.only('project_group_number').filter(project_group_status = 'Live').values("project_group_number")
            return Response(project_group_list, status=status.HTTP_200_OK)
        except:
            return Response({"message":"No Project Available..."}, status=status.HTTP_200_OK)


class Project24HrStats(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request,project_number):
        data = RespondentDetail.objects.filter(
            project_number = project_number,
            url_type='Live',
            end_time__gte=datetime.now() - timedelta(hours = 24)
        ).aggregate(
            starts = Count('id',filter=Q(resp_status__in=[3,4,5,6,7,8,9])),
            completes = Count('id',filter=Q(resp_status__in=[4,9])),
            incompletes = Count('id',filter=Q(resp_status__in=[3])),
            quota_full = Count('id',filter=Q(resp_status__in=[6])),
            client_terminates = Count('id',filter=Q(resp_status__in=[5])),
            internal_terminate = Count('id',filter=Q(resp_status__in=[2])),
            security_terminate = Count('id',filter=Q(resp_status__in=[7]))
        )
        return Response(data, status=status.HTTP_200_OK)


class ProjectCPIApprovedByManager(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request,project):

        try:
            draftinvoice = False
            projectmanager_approved = False 
            if project in list(DraftInvoice.objects.filter(project = project).values_list('project_id',flat=True)):
                draftinvoice = True
            projectmanagername = ProjectCPIApprovedManager.objects.filter(project_id=project)
            if len(projectmanagername) != 0:
                projectmanager_approved = True
                return Response({'draftinvoice':draftinvoice,'projectmanager_approved':projectmanager_approved,'approvedby':f"{projectmanagername.first().approved_by.first_name} {projectmanagername.first().approved_by.last_name}"}, status=status.HTTP_200_OK)
            else:
                return Response({'draftinvoice':draftinvoice,'projectmanager_approved':projectmanager_approved,'approvedby': None}, status=status.HTTP_200_OK)
        except:
                return Response({'error': 'Something Went Wrong'}, status=status.HTTP_400_BAD_REQUEST)
            
        
    def post(self,request,project):
        try:
            ProjectCPIApprovedManager.objects.create(
                project_id = project,
                approved_by = request.user
            )
            project = Project.objects.get(id = project)
            if project.project_status =='Reconciled':
                project.project_status = 'ReadyForAudit'
                # project.project_status = 'ReadyForInvoice'
                project.save()
                ProjectGroup.objects.filter(project = project).update(project_group_status = 'ReadyForAudit')
                # ProjectGroup.objects.filter(project = project).update(project_group_status = 'ReadyForAudit')
            return Response({'message': f'Project-{project.project_number} Approved Successfully'}, status=status.HTTP_200_OK)
        except:
            return Response({'error': f'Project Already Approved'}, status=status.HTTP_400_BAD_REQUEST)


class RespondentDummyDataCreate(APIView):

    def post(self,request,projectgroupsupplier):
        totalcompletes = request.data['totalcompletes']
        projectgroupsupplierobj = ProjectGroupSupplier.objects.get(id = projectgroupsupplier)
        resprelationdata = []
        respurldetails = []
        respreconcilation = []
        resppagedetails = []
        respdevicedetail = []

        def create_data(count):
            PID = ''.join(random.choices(string.ascii_lowercase +string.digits, k=25))
            resp = RespondentDetail.objects.create(
                source = projectgroupsupplierobj.supplier_org_id,
                url_type = 'Live',
                project_group_number = projectgroupsupplierobj.project_group.project_group_number,
                project_number = projectgroupsupplierobj.project_group.project.project_number,
                project_group_cpi = projectgroupsupplierobj.project_group.project_group_cpi,
                supplier_cpi = projectgroupsupplierobj.cpi,
                resp_status = '4',
            )
            resprelationdata.append(RespondentDetailsRelationalfield(respondent = resp,source = projectgroupsupplierobj.supplier_org,project = projectgroupsupplierobj.project_group.project,project_group = projectgroupsupplierobj.project_group,project_group_supplier = projectgroupsupplierobj))
            respurldetails.append(RespondentURLDetail(respondent = resp,pid = PID,RID = PID))
            # respreconcilation.append(RespondentReconcilation(respondent = resp,verified = '1'))
            resppagedetails.append(RespondentPageDetails(respondent = resp))
            respdevicedetail.append(RespondentDeviceDetail(respondent = resp,desktop=True))

        with concurrent.futures.ThreadPoolExecutor(max_workers = max_workers) as executor:
            yield_results = list(executor.map(create_data, range(totalcompletes)))

        RespondentDetailsRelationalfield.objects.bulk_create(resprelationdata)
        RespondentURLDetail.objects.bulk_create(respurldetails)
        # RespondentReconcilation.objects.bulk_create(respreconcilation)
        RespondentPageDetails.objects.bulk_create(resppagedetails)
        RespondentDeviceDetail.objects.bulk_create(respdevicedetail)
        return Response({"status":"Data Created Successfully..!"}, status=status.HTTP_200_OK)
    

class CeleryConversionCalculation(APIView):
    permission_classes = (CustomerAuthPermission,)

    def post(self,request):

        annotated_queryset = ProjectGroup.objects.filter(
            project_group_status='Live'
        ).annotate(
            visits = Count('respondentdetailsrelationalfield__id'),
            completes = Count('respondentdetailsrelationalfield__id', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=['4', '8', '9'])),
            conversion = Case(When(Q(visits=0),then=0), default=(100*F('completes'))/F('visits'))
        )
        ProjectGroupPriorityStats.objects.exclude(project_group__project_group_status = 'Live').delete()
        project_number_list = list(ProjectGroupPriorityStats.objects.values_list('project_group__project_group_number',flat=True))
        bulk_update_surveys = []
        bulk_created_surveys = []

        def multithred_survey_create(pg_obj):
            if pg_obj.project_group_number in project_number_list:
                pg_priority_obj = ProjectGroupPriorityStats.objects.get(project_group = pg_obj)
                pg_priority_obj.internal_conversion = pg_obj.conversion
                pg_priority_obj.visits = pg_obj.visits
                pg_priority_obj.completes = pg_obj.completes
                bulk_update_surveys.append(pg_priority_obj)
            else:
                bulk_created_surveys.append(ProjectGroupPriorityStats(
                    project_group = pg_obj,
                    internal_conversion = pg_obj.conversion,
                    visits = pg_obj.visits,
                    completes = pg_obj.completes,
                ))
        with concurrent.futures.ThreadPoolExecutor(max_workers = max_workers) as executor:
            yield_results = list(executor.map(multithred_survey_create, annotated_queryset))
            
        ProjectGroupPriorityStats.objects.bulk_update(bulk_update_surveys,['internal_conversion','visits','completes'])
        ProjectGroupPriorityStats.objects.bulk_create(bulk_created_surveys)
        return Response({"status":"Data Created Successfully..!"}, status=status.HTTP_200_OK)


class SurveyPriorityCelery(APIView):
    permission_classes = (CustomerAuthPermission,)

    def post(self,request):
        try:
            projectlist1 = ProjectGroup.objects.annotate(
                prescreener_count =  Count('projectgroupprescreener'),
                total_completes = Count('respondentdetailsrelationalfield',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='4'))
            ).filter(
                project__project_customer__customer_url_code = 'toluna',
                project_group_status = 'Live',
                prescreener_count = 3
            ).order_by('-project_group_incidence')[0:3]

            projectlist2 = ProjectGroup.objects.annotate(
                prescreener_count =  Count('projectgroupprescreener'),
                total_completes = Count('respondentdetailsrelationalfield',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='4'))
            ).filter(
                total_completes__lt = 10,
                project__project_customer__customer_url_code = 'zamplia',
                project_group_status = 'Live',
                prescreener_count = 3
            ).order_by('-project_group_incidence')[0:3]

            projectlist4 = ProjectGroup.objects.annotate(
                prescreener_count =  Count('projectgroupprescreener'),
                total_completes = Count('respondentdetailsrelationalfield',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='4'))
            ).filter(
                total_completes__lt = 10,
                project__project_customer__customer_url_code = 'sago',
                project_group_status = 'Live',
                prescreener_count = 3
            ).order_by('-project_group_incidence')[0:3]
            
            projectlist3 = ProjectGroup.objects.annotate(
                prescreener_count =  Count('projectgroupprescreener',filter=(Q(projectgroupprescreener__is_enable = True))),
                total_completes = Count('respondentdetailsrelationalfield',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='4'))
            ).filter(
                project__project_customer__customer_url_code__in = ['toluna','zamplia','sago'],
                project_group_status = 'Live',
                prescreener_count = 3
            ).exclude(
                total_completes__gt = 10,
                project__project_type = '13',
                projectgroupprioritystats__internal_conversion = 0
            ).order_by('-projectgroupprioritystats__internal_conversion')[0:3]

            projectlist = (projectlist1.union(projectlist2)).union(projectlist3).union(projectlist4)

            if len(projectlist) != 0:
                RountingPriority.objects.all().delete()
                for survey in projectlist:
                    RountingPriority.objects.update_or_create(
                        project_group = survey
                    )
            return Response({"status":"success"}, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something Want Wrong"}, status=status.HTTP_400_BAD_REQUEST)

class ProjectCreateBidEmailLink(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, LanguagePermission)

    def get(self,request,bidid):
        try:
            bidobj = Bid.objects.get(id = bidid)
            if bidobj.bid_status == '4':
                return Response({"error":"Bid Cancelled"}, status=status.HTTP_400_BAD_REQUEST)
            project = Project.objects.filter(bid=bidobj)
            if not project.exists():
                projectdata = {
                    'project_name': bidobj.bid_name,
                    'project_type': bidobj.bid_type,
                    'project_client_contact_person': bidobj.client_contact.id,
                    'project_customer': bidobj.customer.id,
                    'project_currency': bidobj.bid_currency.id,
                    'project_redirectID': None,
                    'project_category': bidobj.bid_category,
                    'project_notes':bidobj.bid_description,
                    'project_manager': bidobj.project_manager.id,
                    'secondary_project_manager': bidobj.secondary_project_manager.id,
                    'project_sales_person': bidobj.created_by.id,
                    'project_redirect_type': '1',
                    'project_client_invoicing_contact_person': request.user.id,
                    'Bid_number': bidobj.bid_number,
                    'project_po_number': ''
                }
                return Response(projectdata, status=status.HTTP_200_OK)
            else:
                return Response({"error":"Project Already Exist","projectid":project.first().id}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"error":"Something Want Wrong"}, status=status.HTTP_400_BAD_REQUEST)


class ProjectAddForBackup(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            backup_project_list = ProjectBackup.objects.values('project__project_number','project__project_name','project__project_status','Backup_status','project__project_manager__first_name','project__project_manager__last_name','project__created_at__date','project__project_revenue_month','project__project_revenue_year')
            return Response(backup_project_list, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something Want Wrong"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self,request):
        try:
            projectobj = Project.objects.get(id = request.data['project'])
            if projectobj.project_status in ['Cancel','Invoiced','Archived'] and request.user.email in ['narendra@panelviewpoint.com','sahil@panelviewpoint.com','sanket@panelviewpoint.com']:
                ProjectBackup.objects.update_or_create(project = projectobj)
                projectobj.project_status = 'Backup'
                projectobj.save()
                project_log(f'{projectobj.project_number} Project Added For Backup','',projectobj.project_status,projectobj.id,request.user)
                return Response({"status":f"{projectobj.project_number} Project Added For Backup"}, status=status.HTTP_200_OK)
            else:
                return Response({"error":"Invalid Project Status"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"error":"Something Want Wrong"}, status=status.HTTP_400_BAD_REQUEST)