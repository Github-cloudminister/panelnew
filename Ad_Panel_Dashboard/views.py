from Logapp.views import sub_supplier_enable_disable_log
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework import permissions
from rest_framework.views import APIView
from django.db.models import Case, Value, When, Q, Count, F, ExpressionWrapper
from django.db.models.functions import Cast, Coalesce
from rest_framework.permissions import IsAuthenticated
from Project.serializers import CountrySerializer, LanguageSerializer, median_value
from Supplier.permissions import SupplierPermission
from Supplier_Final_Ids_Email.models import supplierFinalIdsDeploy
from django.core.exceptions import ObjectDoesNotExist
from .serializers import *
from django.conf import settings
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from supplierdashboard.paginations import *
from datetime import datetime, date, timedelta
from knox.auth import TokenAuthentication
import requests
from automated_email_notifications.email_configurations import sendEmailSendgripAPIIntegration

# Create your views here.

header = {'Static-Token':'qS)55DWNBsBSTVcVTFsD25srN-)jy-SZ'}

class SubSupplierAuthPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        auth_token = request.META.get('HTTP_AUTHORIZATION')
        if auth_token != None:
            if settings.AD_PANEL_DASHBOARD_AUTH_KEY in auth_token.split('Token '):
                return True
        return False

class SubSupplierContactDashboardRegistrationView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierPermission)

    def post(self, request, supp_contact_id):
        supplier_dashboard = request.GET.get('ad_dashboard')
        supp_contact_obj = SubSupplierContact.objects.get(id=supp_contact_id)
        serializer = SupplierContactSerializer(supp_contact_obj)
        if supplier_dashboard == 'register':

            if supp_contact_obj.subsupplier_dashboard_registration == True:
                return Response({'message': 'User is Already Registered on Supplier Dashboard'}, status=status.HTTP_208_ALREADY_REPORTED)

            final_dict_data = serializer.data
            
            data = {
                'company_name':supp_contact_obj.subsupplier_id.sub_supplier_name
                } 
            final_dict_data.update(data)
            final_dict_data.update(**request.data)
            response = requests.post(settings.AD_PANEL_DASHBOARD_URL + 'user-register-panelviewpoint', json=final_dict_data, headers=header)

            if response.status_code == 201:
                supp_contact_obj.subsupplier_dashboard_registration = True                                                                                                                                                                                                                                                                      
                supp_contact_obj.subsupplier_mail_sent = True
                supp_contact_obj.save()
                html_message = render_to_string('supplierdashboard/emailtemplates/new_user_set_password.html', {
                        'firstname': supp_contact_obj.subsupplier_firstname,
                        'username':final_dict_data['email'],
                        'password_set_url':f"{settings.AD_PANEL_DASHBOARD_FRONTEND_URL}#/authentication/set-password/{response.json()['user_token']}"
                        })
                sendEmailSendgripAPIIntegration(to_emails=supp_contact_obj.subsupplier_email, subject='User Registration Mail', html_message=html_message)

                sub_supplier_enable_disable_log("Enabled","",supp_contact_obj.subsupplier_id.id,request.user)

                return Response({'message': 'User has been Registered Successfully & The Password Setting Email has been sent'}, status=status.HTTP_201_CREATED)
            
            elif response.status_code == 400:
                return Response(response.json(), status=status.HTTP_400_BAD_REQUEST)
            
            elif response.status_code == 208:
                supp_contact_obj.subsupplier_dashboard_registration = True
                supp_contact_obj.save()
                return Response({'message': 'User is Already Registered on Supplier Dashboard'}, status=status.HTTP_208_ALREADY_REPORTED)
            
            elif response.status_code == 200:
                supp_contact_obj.subsupplier_dashboard_registration = True
                supp_contact_obj.save()
                return Response({'message': 'User Status Turned Active From Inactive'}, status=status.HTTP_200_OK)
            
            elif response.status_code == 401:
                return Response({'message':'Static Token to access Supplier Dashboard is Incorrect'}, status=status.HTTP_401_UNAUTHORIZED)
            
            else:
                return Response({'message':'Supplier Dashboard URL Not Found'}, status=status.HTTP_404_NOT_FOUND)

        elif supplier_dashboard == 'deregister':
            if supp_contact_obj.subsupplier_dashboard_registration == False:
                return Response({'message': 'User is Already De-Registered on Supplier Dashboard'}, status=status.HTTP_208_ALREADY_REPORTED)

            supp_contact_obj.subsupplier_dashboard_registration = False
            supp_contact_obj.save()

            response = requests.post(settings.AD_PANEL_DASHBOARD_URL + 'user-de-register-panelviewpoint', json=serializer.data, headers=header)

            if response.status_code == 200:
                sub_supplier_enable_disable_log("Disabled","Enabled",supp_contact_obj.subsupplier_id.id,request.user)
                return Response({'message': 'User Successfully De-Registered on Supplier Dashboard'}, status=status.HTTP_200_OK)
            
            elif response.status_code == 400:
                return Response({'message': 'User Not Already Registered on Supplier Dashboard'}, status=status.HTTP_400_BAD_REQUEST)
            
            elif response.status_code == 401:
                return Response({'message':'Static Token to access Supplier Dashboard is Incorrect'}, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({'message':'Supplier Dashboard URL Not Found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'message':'Please pass supplier_dashboard URL Parameter & pass its value to either register or deregister'}, status=status.HTTP_400_BAD_REQUEST)


class sub_supplierUserRegistrationReSendEmailPasswordLink(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierPermission)

    def post(self,request, supp_contact_id):
        supp_contact_obj = SubSupplierContact.objects.get(id=supp_contact_id)
        serializer = SupplierContactSerializer(supp_contact_obj)

        final_dict_data = serializer.data

        response = requests.post(settings.AD_PANEL_DASHBOARD_URL + 'user-resetPassword-internal', json={'email':supp_contact_obj.subsupplier_email}, headers=header)
        user_token = response.json()
        if response.status_code == 200:
            supp_contact_obj.subsupplier_dashboard_registration = True
            supp_contact_obj.subsupplier_mail_sent = True
            supp_contact_obj.save()
            html_message = render_to_string('AD_dashboard/emailtemplates/new_user_set_password.html', {
                    'firstname': supp_contact_obj.subsupplier_firstname,
                    'username':final_dict_data['email'],
                    'password_set_url':f"{settings.AD_PANEL_DASHBOARD_FRONTEND_URL}#/authentication/set-password/{response.json()['user_token']}"
                    })
            sendEmailSendgripAPIIntegration(to_emails=supp_contact_obj.subsupplier_email, subject='User Registration Mail', html_message=html_message)

            return Response({"message":"Password Link Has Sent Been Email Successfully.! "}, status=status.HTTP_200_OK)
        elif response.status_code == 401:
            return Response({'message':'Static Token to access Supplier Dashboard is Incorrect'}, status=status.HTTP_401_UNAUTHORIZED)
        elif response.status_code == 404:
            return Response({'message':'No User Found with this Email ID'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'message':'Supplier Dashboard URL Not Found'}, status=status.HTTP_404_NOT_FOUND)



class projectList(ModelViewSet):
    permission_classes = (SubSupplierAuthPermission,)
    serializer_class = LiveProjectListSubSupplierSerializer
    pagination_class = MyPageNumberPagination
    
    def get_queryset(self):
        query_param = self.request.GET
        if query_param.get('project_no'):
            return ProjectGroupSubSupplier.objects.filter(sub_supplier_status = 'Live', sub_supplier_org__sub_supplier_code = self.kwargs['sub_sup_code'], created_at__date__gte = '2021-4-15', project_group__project__project_number=query_param.get('project_no'))
        elif query_param.get('survey_no'):
            return ProjectGroupSubSupplier.objects.filter(sub_supplier_status = 'Live', sub_supplier_org__sub_supplier_code = self.kwargs['sub_sup_code'], created_at__date__gte = '2021-4-15', project_group__project_group_number=query_param.get('survey_no'))
        else:
            return ProjectGroupSubSupplier.objects.filter(sub_supplier_status = 'Live', sub_supplier_org__sub_supplier_code = self.kwargs['sub_sup_code'], created_at__date__gte = '2021-4-15').order_by("-id")


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, context = {'sub_source':self.kwargs['sub_sup_code']}, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, context = {'sub_source':self.kwargs['sub_sup_code']}, many=True)
        return Response(serializer.data)
    


class closedprojectList(ModelViewSet):
    permission_classes = (SubSupplierAuthPermission,)
    serializer_class = ClosedProjectGroupSubSupplierSerializer
    pagination_class = MyPageNumberPagination
    
    def get_queryset(self):
        query_params = self.request.GET
        # project_group__project_group_status__in = ['Closed','Paused', 'Reconciled', 'ReadyForInvoiceApproved','Invoiced']
        query_list = ProjectGroupSubSupplier.objects.filter(sub_supplier_org__sub_supplier_code = self.kwargs['sub_sup_code']).exclude(project_group__project__supplieridsmarks__final_ids_sent=True).exclude(project_group__project_group_status__in = ["Booked","Live"])

        if query_params.get('project_no'):
            query_list = query_list.filter(project_group__project__project_number=query_params.get('project_no'))
        
        if query_params.get('survey_no'):
            query_list = query_list.exclude(~Q(project_group__project_group_number__icontains=query_params.get('survey_no')))
        
        return query_list


    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, context = {'sub_source':self.kwargs['sub_sup_code']}, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, context = {'sub_source':self.kwargs['sub_sup_code']}, many=True)
        return Response(serializer.data)
    

class finalizedprojectList(ModelViewSet):
    permission_classes = (SubSupplierAuthPermission,)
    pagination_class = MyPageNumberPagination

    def list(self, request, sub_sup_code, *args, **kwargs):
        project_number = request.GET.get('project_no')
        
        query_list = ProjectGroupSubSupplier.objects.filter(project_group__project_group_status__in = ['Invoiced'], sub_supplier_org__sub_supplier_code = self.kwargs['sub_sup_code'], project_group__project__supplieridsmarks__final_ids_sent=True)

        if project_number:
            query_list = query_list.filter(project_group__project__project_number__icontains = project_number)
            
        progrp_supp = query_list.values(project_group_number = F('project_group__project_group_number'))

        queryset = RespondentDetail.objects.filter(respondenturldetail__sub_sup_id = sub_sup_code, url_type = 'Live', project_group_number__in = progrp_supp).values('project_number').annotate(
            completes = Count('resp_status', filter=Q(resp_status='4')),
            cpi = Avg('supplier_cpi', filter=Q(resp_status='4')),
            total_expense = Sum('supplier_cpi', filter=Q(resp_status='4')))

        return Response(queryset, status=status.HTTP_200_OK)
    


class SubSupplierStatsAggregateCountsAPI(APIView):
    permission_classes = (SubSupplierAuthPermission,)


    def get(self, request, sub_sup_code):

        live_surveys = ProjectGroupSubSupplier.objects.filter(sub_supplier_org__sub_supplier_code = sub_sup_code, sub_supplier_status = 'Live').exclude(project_group__respondentdetailsrelationalfield__respondent__resp_status__in = ['1','2','3','4','5','6','7','8','9']).count()
        running_surveys = ProjectGroupSubSupplier.objects.filter(sub_supplier_status = 'Live', sub_supplier_org__sub_supplier_code = self.kwargs['sub_sup_code'], created_at__date__gte = '2021-4-15').count()

        till_today = date.today()
        first_day = till_today - timedelta(days=(till_today.day - 1))

        stats_count = RespondentDetail.objects.filter(respondenturldetail__sub_sup_id = sub_sup_code, url_type = 'Live',resp_status = '4').aggregate(
            current_month_completes=Count('id', filter=Q(resp_status='4', end_time_day__range=(first_day,till_today))), 
            current_year_completes=Count('id', filter=Q(resp_status='4', end_time_day__year=date.today().year)), 
            total_month_earnings=Cast(Sum('supplier_cpi', filter=Q(resp_status='4',end_time_day__range=(first_day,till_today),respondentdetailsrelationalfield__project__project_status = "Invoiced",respondentdetailsrelationalfield__project__scrubproject = True)), output_field=models.DecimalField(max_digits=10, decimal_places=2)),
            total_earnings=Cast(Sum('supplier_cpi', filter=Q(resp_status='4',respondentdetailsrelationalfield__project__project_status = "Invoiced",respondentdetailsrelationalfield__project__scrubproject = True)), output_field=models.DecimalField(max_digits=10, decimal_places=2))
        )
        stats_count.update({'live_surveys':live_surveys,'running_surveys':running_surveys})

        return Response(data=stats_count)
    


class SurveyPreScreenerListView(APIView):

    permission_classes = (SubSupplierAuthPermission,)
    serializer_class = SurveyPrescreenerViewSerializer

    def get(self, request, survey_number):

        prescreener_obj = ProjectGroupPrescreener.objects.filter(project_group_id__project_group_number=survey_number,is_enable = True)
        serializer = self.serializer_class(prescreener_obj, many=True)
        return Response({"message":serializer.data}, status=status.HTTP_200_OK)
    


class ProjectFinalidsDataView(APIView):

    def get(self,request,project_id,supplier_id):
        project_final_ids_obj = RespondentDetail.objects.filter(url_type='Live',resp_status='4',project_number = project_id, source = supplier_id).values('id').annotate(
            pid = F('respondenturldetail__pid'),
            cpi = F('supplier_cpi')
        )
        return Response({"Project_Final_ids":project_final_ids_obj}, status=status.HTTP_200_OK)
    

class finalidsProjectListView(APIView):

    permission_classes = (SubSupplierAuthPermission,)

    def get(self, request, supcode, project_list_code):
        completes_query = Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4], respondentdetailsrelationalfield__respondent__url_type='Live')
        supplier_finalids_deploy_obj = supplierFinalIdsDeploy.objects.get(project_list_code=project_list_code, supplier__supplier_code = supcode)

        _table_data = RespondentDetail.objects.filter(project_number__in = supplier_finalids_deploy_obj.project_list, url_type='Live', respondentdetailsrelationalfield__source__supplier_code = supcode).values('source','respondentdetailsrelationalfield__source__supplier_name', 'project_number', 'respondentdetailsrelationalfield__project').annotate(completes=Count('project_number', filter=Q(resp_status='4'))).order_by('source')
        return Response({'project_list': _table_data}, status=status.HTTP_200_OK)
    

class SupplierDashboardCountryView(APIView):

    '''
        method to get the list of all country objects.
    '''
    permission_classes = (SubSupplierAuthPermission,)
    serializer_class = CountrySerializer

    def get(self, request):

        country_list = Country.objects.all()
        serializer = self.serializer_class(country_list, many=True)
        return Response(serializer.data)
    


class SupplierDashboardLanguageView(APIView):

    '''
        method to get the list of all language objects.
    '''
    permission_classes = (SubSupplierAuthPermission,)
    serializer_class = LanguageSerializer

    def get(self, request):

        language_list = Language.objects.all()
        serializer = self.serializer_class(language_list, many=True)
        return Response(serializer.data)
    


class subsupplierupdate(ModelViewSet):
    permission_classes = (SubSupplierAuthPermission,)
    serializer_class = subsupplierAddSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = ProjectGroupSubSupplier.objects.get(sub_supplier_org__sub_supplier_code = self.kwargs['sub_sup_code'], project_group__project_group_number = self.kwargs['project_group_number'])
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
            instance = ProjectGroupSubSupplier.objects.get(sub_supplier_org__sub_supplier_code = self.kwargs['sub_sup_code'], project_group__project_group_number = self.kwargs['project_group_number'])
            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status.HTTP_200_OK)
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_400_BAD_REQUEST)
        


class NewProjectSurveyAvailableList(ModelViewSet):
    # permission_classes = (SubSupplierAuthPermission,)
    serializer_class = ProjectGroupNewSurveyAvailableSerializer
    pagination_class = MyPageNumberPagination
    
    def get_queryset(self, sub_sup_code):
        query_params = self.request.GET
        project_number = query_params.get('projectnumber')
        
        project_group_obj = ProjectGroup.objects.filter(project_groups__sub_supplier_status = 'Live',created_at__date__gte = '2023-01-01', show_on_DIY=True,project_groups__sub_supplier_org__sub_supplier_code = self.kwargs['sub_sup_code']).exclude(respondentdetailsrelationalfield__respondent__resp_status__in = ['1','2','3','4','5','6','7','8','9']).exclude(project__project_type = '12')

        if sub_sup_code == '163':
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
        queryset = self.filter_queryset(self.get_queryset(kwargs['sub_sup_code']))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.serializer_class(page, context = {'sub_source':self.kwargs['sub_sup_code']}, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(queryset, context = {'sub_source':self.kwargs['sub_sup_code']}, many=True)
        return Response(serializer.data)
    


class StatsCountCompleteClicksView(APIView):


    def get(self, request, sub_sup_code):
        
        todays_date = datetime.now().date()

        seven_days_ago = todays_date - timedelta(days=7)

        resp_obj = RespondentDetail.objects.filter(respondenturldetail__sub_sup_id = sub_sup_code, url_type='Live', end_time_day__lte=todays_date, end_time_day__gte=seven_days_ago).values('end_time_day').annotate(
            day_wise_completes=Count('resp_status', filter=Q(resp_status='4')),
            day_wise_clicks=Count('resp_status', filter=Q(resp_status__in=['1','2','3','4','5','6','7','8','9'])),
        )

        return Response(resp_obj,status=status.HTTP_200_OK)
    


class ProjectGroupADEnabledList(APIView):
    # serializer_class = ProjectGroupNewSurveyAvailableSerializer

    # def get_queryset(self):
    #     queryset = ProjectGroup.objects.filter(ad_enable_panel = True)
    #     return queryset

    def get(self, request):
        page = self.request.GET.get('page',1)
        search_by_project = self.request.GET.get('project_number')
        search_by_survey = self.request.GET.get('survey_number')

        ad_project_group_obj = ProjectGroup.objects.filter(project_group_status__in = ["Live","Paused"] ,ad_enable_panel = True).values(
                "id",
                project_number = F("project__project_number"),
                survey_number = F("project_group_number"),
                survey_name = F("project_group_name"),
                cpi = F("project_group_cpi"),
                incidence = F("project_group_incidence"),
                loi = F("project_group_loi"),
                completes = F("project_group_completes"),
                country = F("project_group_country__country_name"),
                language = F("project_group_language__language_name"),
                targeting_description = F("project__project_notes"),
                prjgrp_status_setLive_time = F("prjgrp_status_setLive_timestamp"),
            ).exclude(project__project_customer__customer_url_code__in = ["toluna","zamplia"])
        # .annotate(
        #     cpi = Cast(F('project_group_cpi') * 0.60, output_field=models.FloatField())
        # )

        if search_by_project not in ['', None]:
            ad_project_group_obj = ProjectGroup.objects.filter(project__project_number = search_by_project,project_group_status__in = ["Live","Paused"] ,ad_enable_panel = True).values(
                "id",
                project_number = F("project__project_number"),
                survey_number = F("project_group_number"),
                survey_name = F("project_group_name"),
                cpi = F("project_group_cpi"),
                incidence = F("project_group_incidence"),
                loi = F("project_group_loi"),
                completes = F("project_group_completes"),
                country = F("project_group_country__country_name"),
                language = F("project_group_language__language_name"),
                targeting_description = F("project__project_notes"),
                prjgrp_status_setLive_time = F("prjgrp_status_setLive_timestamp"),
            ).exclude(project__project_customer__customer_url_code__in = ["toluna","zamplia"])

        if search_by_survey not in ['', None]:
            ad_project_group_obj = ProjectGroup.objects.filter(project_group_number = search_by_survey,project_group_status__in = ["Live","Paused"] ,ad_enable_panel = True).values(
                "id",
                project_number = F("project__project_number"),
                survey_number = F("project_group_number"),
                survey_name = F("project_group_name"),
                cpi = F("project_group_cpi"),
                incidence = F("project_group_incidence"),
                loi = F("project_group_loi"),
                completes = F("project_group_completes"),
                country = F("project_group_country__country_name"),
                language = F("project_group_language__language_name"),
                targeting_description = F("project__project_notes"),
                prjgrp_status_setLive_time = F("prjgrp_status_setLive_timestamp"),
            ).exclude(project__project_customer__customer_url_code__in = ["toluna","zamplia"])

        paginator = Paginator(ad_project_group_obj,10)
        try:
            ad_project_group_obj = paginator.page(page)
        except PageNotAnInteger:
            ad_project_group_obj = paginator.page(1)
        except EmptyPage:
            ad_project_group_obj = {"message":"No More Data Available.!"}
            return Response(ad_project_group_obj, status=status.HTTP_400_BAD_REQUEST)

        return Response(ad_project_group_obj.object_list, status=status.HTTP_200_OK)

class SubSupplierList(APIView):

    def get(self, request):

        sub_supplier_obj = SubSupplierOrganisation.objects.only(
            "sub_supplier_name",
            "sub_supplier_rate",
            "sub_supplier_rate_model"
        ).all().values(
            "id",
            "sub_supplier_name",
            "sub_supplier_rate",
            "sub_supplier_rate_model"
        ).order_by("sub_supplier_name")

        return Response(sub_supplier_obj, status=status.HTTP_200_OK)
    

class ADPanelSupplierADD(APIView):

    def get(self, request, project_group_id):

        projct_grp_sub_supplier = ProjectGroupSupplier.objects.only('id','project_group','clicks','cpi','supplier_org','completes').filter(project_group = project_group_id, supplier_org__supplier_type = '5')\
        .values(
            'id',
            'project_group',
            'clicks',
            'cpi',
            supplier_id = F('supplier_org'),
            total_N = F('completes'),
                )
        
        return Response(projct_grp_sub_supplier, status=status.HTTP_200_OK)
    

    def post(self, request, project_group_id):

        data = request.data
        # ad_enabled = data['ad_enable_panel']
        cpi = data.get('cpi',0)
        completes = data.get('total_N',0)
        clicks = data.get('clicks',0)
        project_group = ProjectGroup.objects.get(id = project_group_id)
        suppgrp = SupplierOrganisation.objects.get(supplier_type = '5')
        project_grp_supplier = ProjectGroupSubSupplier.objects.filter(project_group_id=project_group.id)
        project_grp_supplier.update(sub_supplier_status = 'Paused')
        
        if project_group.project_group_status != "Booked":
            # if ad_enabled == True:
            obj, created = ProjectGroupSupplier.objects.update_or_create(project_group = project_group, supplier_org = suppgrp, defaults={'project_group':project_group, 'supplier_org':suppgrp, 'completes':completes, 'clicks':clicks, 'cpi': cpi ,'supplier_status':'Live','supplier_survey_url':project_group.project_group_surveyurl+"&source="+str(suppgrp.id)+"&PID=%%PID%%",'supplier_completeurl':suppgrp.supplier_completeurl,'supplier_terminateurl':suppgrp.supplier_terminateurl,'supplier_quotafullurl':suppgrp.supplier_quotafullurl,'supplier_securityterminateurl':suppgrp.supplier_securityterminateurl,'supplier_postbackurl':suppgrp.supplier_postbackurl,'supplier_internal_terminate_redirect_url':suppgrp.supplier_internal_terminate_redirect_url,'supplier_terminate_no_project_available':suppgrp.supplier_terminate_no_project_available})

            for d in data['sub_supplier']:
                try:
                    grp_sub_supplier = ProjectGroupSubSupplier.objects.get(sub_supplier_org = d['sub_supplier_org'], project_group_id = project_group.id)
                    grp_sub_supplier.sub_supplier_status = "Live"
                    grp_sub_supplier.completes = d['total_N']
                    grp_sub_supplier.clicks = d['clicks']
                    grp_sub_supplier.cpi = d['cpi']
                    grp_sub_supplier.sub_supplier_completeurl = grp_sub_supplier.sub_supplier_completeurl
                    grp_sub_supplier.sub_supplier_terminateurl = grp_sub_supplier.sub_supplier_terminateurl
                    grp_sub_supplier.sub_supplier_quotafullurl = grp_sub_supplier.sub_supplier_quotafullurl
                    grp_sub_supplier.sub_supplier_securityterminateurl = grp_sub_supplier.sub_supplier_securityterminateurl
                    grp_sub_supplier.sub_supplier_postbackurl = grp_sub_supplier.sub_supplier_postbackurl
                    grp_sub_supplier.sub_supplier_internal_terminate_redirect_url = grp_sub_supplier.sub_supplier_internal_terminate_redirect_url
                    grp_sub_supplier.sub_supplier_terminate_no_project_available = grp_sub_supplier.sub_supplier_terminate_no_project_available
                    grp_sub_supplier.save(force_update=True)
                    project_group.ad_enable_panel = True
                    project_group.save(force_update=True)
                
                except Exception as e:
                    sup_obj = SubSupplierOrganisation.objects.get(id=d['sub_supplier_org'])
                    projcvt_grp_sub_supplier = ProjectGroupSubSupplier.objects.create(project_group_id = project_group.id,project_group_supplier_id = obj.id,sub_supplier_org_id = sup_obj.id,completes = d['total_N'],clicks = d['clicks'], cpi = d['cpi'])

                    projcvt_grp_sub_supplier.sub_supplier_survey_url = obj.supplier_survey_url.replace("PID=%%PID%%",f"sub_sup={str(projcvt_grp_sub_supplier.sub_supplier_org.sub_supplier_code)}&PID=%%PID%%")

                    projcvt_grp_sub_supplier.sub_supplier_completeurl = sup_obj.sub_supplier_completeurl 
                    projcvt_grp_sub_supplier.sub_supplier_terminateurl = sup_obj.sub_supplier_terminateurl 
                    projcvt_grp_sub_supplier.sub_supplier_quotafullurl = sup_obj.sub_supplier_quotafullurl 
                    projcvt_grp_sub_supplier.sub_supplier_securityterminateurl = sup_obj.sub_supplier_securityterminateurl 
                    projcvt_grp_sub_supplier.sub_supplier_postbackurl = sup_obj.sub_supplier_postbackurl 
                    projcvt_grp_sub_supplier.sub_supplier_internal_terminate_redirect_url = sup_obj.sub_supplier_terminate_no_project_available 
                    projcvt_grp_sub_supplier.sub_supplier_terminate_no_project_available = sup_obj.sub_supplier_terminate_no_project_available
                    projcvt_grp_sub_supplier.save() 

                    project_group.ad_enable_panel = True
                    project_group.save(force_update=True)

            # else:
            #     ProjectGroupSupplier.objects.filter(project_group = project_group).update(supplier_status = 'Paused')
                
            #     project_group.ad_enable_panel = False
            #     project_group.save(force_update=True, update_fields=['ad_enable_panel'])
        
            return Response({"message":"AD Panel Update Successfully..!"},status=status.HTTP_200_OK)
        else:
            return Response({"error":"Please Survey Live First.!"}, status=status.HTTP_400_BAD_REQUEST)
        


class ADPanelSubSupplierWithStat2View(APIView):

    def get(self, request, project_group_num):
        # sup_type = request.GET.get('sup_type', '')
        # if sup_type == '':
        #     sup_type = '5'
        grp_supp_list = ProjectGroupSubSupplier.objects.select_related('project_group', 'sub_supplier_org', 'respondentprojectgroupsubsupplier__respondent').filter(project_group__project_group_number=project_group_num, sub_supplier_org__supplier_org_id__supplier_type = "5").values(
            'id',
            'project_group', 
            'sub_supplier_org',
            'clicks',
            'cpi',
            'sub_supplier_survey_url',
            'sub_supplier_internal_terminate_redirect_url',
            'sub_supplier_terminate_no_project_available',
            'sub_supplier_status',
            sub_supplier_complete_url = F('sub_supplier_completeurl'),
            sub_supplier_terminate_url = F('sub_supplier_terminateurl'),
            sub_supplier_quotafull_url = F('sub_supplier_quotafullurl'),
            sub_supplier_securityterminate_url = F('sub_supplier_securityterminateurl'),
            sub_supplier_postback_url = F('sub_supplier_postbackurl'),
            total_N=F('completes'),
            ).annotate(
                completes = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[4], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                incompletes = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[3,9], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                terminates = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[5], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                security_terminate = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[7], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                quota_full = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[6], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                starts = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[3,4,5,6,7,8,9], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                total_visits = Count('respondentprojectgroupsubsupplier',filter=Q(respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                incidence = Case(
                        When(Q(completes=0), then=Cast(0.0, output_field=models.DecimalField(max_digits=7,decimal_places=2))), 
                        default=Cast((100 * F('completes') / Count(
                                'respondentprojectgroupsubsupplier', 
                                filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[4,5], respondentprojectgroupsubsupplier__respondent__url_type='Live')
                            )
                        ), output_field=models.DecimalField(max_digits=7,decimal_places=2))
                    ),
                median_LOI = ExpressionWrapper(
                        Value(
                            round(
                                float(
                                    median_value(
                                        RespondentDetail.objects.filter(
                                            resp_status__in=[4], 
                                            url_type='Live', 
                                            project_group_number=F('project_group_number'), 
                                            source=F('source')
                                        ),'duration'
                                    )
                                ),0
                            )
                        ), output_field=models.FloatField()
                    ),
                revenue = Coalesce(
                        Sum(
                            'respondentprojectgroupsubsupplier__respondent__project_group_cpi', 
                            filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[4], respondentprojectgroupsubsupplier__respondent__url_type='Live')
                        ), 0.0
                    ),
                expense = Coalesce(
                        Sum(
                            'respondentprojectgroupsubsupplier__project_group_sub_supplier__cpi', 
                            filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status=4, respondentprojectgroupsubsupplier__respondent__url_type='Live')
                        ), 0.0
                    ),
                margin= Case(
                        When(Q(revenue=0.0) | Q(revenue=None), then=Cast(0.0, output_field=models.DecimalField(max_digits=7,decimal_places=2))), 
                        default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'), output_field=models.DecimalField(max_digits=7,decimal_places=2)),
                    ),
            )
        if grp_supp_list.exists():
            return Response(grp_supp_list)
        else:
            return Response({'message': "No data found for the provided ProjectGroup-Number"}, status=status.HTTP_404_NOT_FOUND)
        

class SubSupplierRedirectUrlView(APIView):

    def get(self, request, project_group_sub_supplier_id):

        sub_supplier_obj = ProjectGroupSubSupplier.objects.only(
            "sub_supplier_completeurl",
            "sub_supplier_terminateurl",
            "sub_supplier_quotafullurl",
            "sub_supplier_securityterminateurl",
            "sub_supplier_internal_terminate_redirect_url",
            "sub_supplier_terminate_no_project_available",
            "sub_supplier_postbackurl"
        ).filter(id = project_group_sub_supplier_id).values(
            completeurl = F("sub_supplier_completeurl"),
            terminateurl = F("sub_supplier_terminateurl"),
            quotafullurl = F("sub_supplier_quotafullurl"),
            securityterminateurl = F("sub_supplier_securityterminateurl"),
            internal_terminate_redirect_url = F("sub_supplier_internal_terminate_redirect_url"),
            terminate_no_project_available = F("sub_supplier_terminate_no_project_available"),
            postbackurl = F("sub_supplier_postbackurl")
        )

        return Response(sub_supplier_obj, status=status.HTTP_200_OK)
    

    def put(self, request, project_group_sub_supplier_id):
        data = request.data

        completeurl = data.get("sub_supplier_complete_url","")
        terminateurl = data.get("sub_supplier_terminate_url","")
        quotafullurl = data.get("sub_supplier_quotafull_url","")
        securityterminateurl = data.get("sub_supplier_securityterminate_url","")
        internal_terminate_redirect_url = data.get("sub_supplier_internal_terminate_redirect_url","")
        terminate_no_project_available = data.get("sub_supplier_terminate_no_project_available","")
        postbackurl = data.get("sub_supplier_postback_url","")

        try:
            sub_supplier_obj = ProjectGroupSubSupplier.objects.get(id = project_group_sub_supplier_id)
            sub_supplier_obj.sub_supplier_completeurl = completeurl 
            sub_supplier_obj.sub_supplier_terminateurl = terminateurl 
            sub_supplier_obj.sub_supplier_quotafullurl = quotafullurl 
            sub_supplier_obj.sub_supplier_securityterminateurl = securityterminateurl
            sub_supplier_obj.sub_supplier_internal_terminate_redirect_url = internal_terminate_redirect_url 
            sub_supplier_obj.sub_supplier_terminate_no_project_available = terminate_no_project_available 
            sub_supplier_obj.sub_supplier_postbackurl = postbackurl

            sub_supplier_obj.save()

            return Response({"message":"Supplier Redirect Url Update Successfully.!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error":"No data found for this Supplier.!"}, status=status.HTTP_400_BAD_REQUEST)



class SubSupplierReportwithDate(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        sub_supplier_id = request.data.get('sub_supplier_id', None)
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)
        project_no = request.data.get('project_no', None)
        converted_start_date = None
        converted_end_date = None


        if start_date and end_date:
            converted_start_date = datetime.strptime(start_date, "%d-%m-%Y").date()
            converted_end_date = datetime.strptime(end_date, "%d-%m-%Y").date()

        resp_group_sub_supplier_obj = RespondentProjectGroupSubSupplier.objects.select_related('respondent').values(
            project_number = F('respondent__respondentdetailsrelationalfield__project__project_number'), 
            sub_supplier_name = F('project_group_sub_supplier__sub_supplier_org__sub_supplier_name'),
        ).filter(
            Q(respondent__end_time__date__range = [converted_start_date, converted_end_date]) if converted_start_date and converted_end_date else Q(),
            respondent__resp_status__in=[4,8,9],
            respondent__url_type='Live', 
        ).distinct().annotate(
            total_collected_completes = Count('project_group_sub_supplier', filter=Q(respondent__resp_status__in=[4,8,9])), 
            accepted_completes = Count('project_group_sub_supplier', filter=Q(respondent__resp_status__in=[4,9])), 
            rejected_completes = Count('project_group_sub_supplier', filter=Q(respondent__resp_status__in=[8,9])), 
            revenue = Sum('respondent__project_group_cpi', filter=Q(respondent__resp_status__in=[4,9])), 
            expense = Sum('respondent__supplier_cpi', filter=Q(respondent__resp_status__in=[4]))
        )

        if project_no not in ['', None]:
            resp_group_sub_supplier_obj = resp_group_sub_supplier_obj.filter(respondent__respondentdetailsrelationalfield__project__project_number = project_no)

        if sub_supplier_id:
            resp_group_sub_supplier_obj = resp_group_sub_supplier_obj.filter(project_group_sub_supplier__sub_supplier_org=sub_supplier_id)
        
        return Response(list(resp_group_sub_supplier_obj), status=status.HTTP_200_OK)
        
class ADPanelProjectGroupSubJsonDataApiView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    # permission_classes = (SubSupplierAuthPermission,)

    def get(self, request, project_number):

        resp_status = self.request.GET.get('status')

        project_rep_obj = RespondentProjectGroupSubSupplier.objects.filter(
            respondent__project_number = project_number).only("respondent__project_number","respondent__url_type","respondent__project_group_number","respondent__project_group_cpi","respondent__supplier_cpi","respondent__resp_status","respondent__final_detailed_reason","respondent__start_time","respondent__end_time","respondent__duration","respondent__respondenturldetail__pid","respondent__respondenturldetail__RID","respondent__respondentreconcilation__verified_at","respondent__respondenturldetail__ip_address","respondent__respondentdevicedetail", "project_group_sub_supplier__sub_supplier_org__sub_supplier_name","respondent__respondentpagedetails__last_page_seen").values(
            project_number = F("respondent__project_number"),
            url_type = F("respondent__url_type"),
            project_group_number = F("respondent__project_group_number"),
            project_group_cpi = F("respondent__project_group_cpi"),
            supplier_cpi = F("respondent__supplier_cpi"),
            sub_supplier_cpi = F("project_group_sub_supplier__cpi"),
            resp_status = F("respondent__resp_status"),
            final_detailed_reason = F("respondent__final_detailed_reason"),
            start_time = F("respondent__start_time"),
            end_time = F("respondent__end_time"),
            duration = F("respondent__duration"),
            ).annotate(SubSuppliername = F('project_group_sub_supplier__sub_supplier_org__sub_supplier_name'),
                       PID = F('respondent__respondenturldetail__pid'), RID = F('respondent__respondenturldetail__RID'),
                       Ip = F('respondent__respondenturldetail__ip_address'), last_seen = F("respondent__respondentpagedetails__last_page_seen"),
                       Device = Case(
                           When(respondent__respondentdevicedetail__mobile = True,then=Value('Mobile')),
                           When(respondent__respondentdevicedetail__tablet = True,then=Value('Tablet')),
                           When(respondent__respondentdevicedetail__desktop = True,then=Value('Desktop/Laptop'))
                        )
            ).order_by('-id')
            
        if resp_status not in ['', None]:
            project_rep_obj = project_rep_obj.filter(respondent__resp_status__in = list(resp_status))

        if project_rep_obj.exists():
            return Response(project_rep_obj)
        else:
            return Response({'message': "No data found for the provided Project-Number Or With Status"}, status=status.HTTP_404_NOT_FOUND)

