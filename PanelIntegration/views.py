from django.db.models import Count
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import TruncMonth

# rest_framework imports
from ClientSupplierAPIIntegration.TolunaClientAPI.models import ClientDBCountryLanguageMapping
from Logapp.views import projectgroup_panel_log
from affiliaterouter.models import RountingPriority
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.pagination import PageNumberPagination

# third_party module imports
from knox.auth import TokenAuthentication
from datetime import datetime
import requests
import json

# in-project imports
from .models import *
from .serializers import *
from Project.permissions import *
from Prescreener.models import ProjectGroupPrescreener
from django.conf import settings
from Project.panel_view import *


# Create your views here.

ODPanel_Auth_key = "45Mvp7LKKN2837PfXCnif5auts74sXALi05iqBHxuZKSJtd8v0"
class ODPanelAuthPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        auth_token = request.META.get('HTTP_AUTHORIZATION')
        if auth_token != None:
            if ODPanel_Auth_key in auth_token.split('Token '):
                return True
        return False

class ProjectGroupAddPanelView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectGroupAddPanelSerializer

    '''
        class to get a single instance of Project Group object and to update it.
    '''

    def get_object(self, project_group_number):

        try:
            return ProjectGroup.objects.get(project_group_number=project_group_number)
        except ProjectGroup.DoesNotExist:
            return None

    def get(self, request, project_group_number):

        instance = self.get_object(project_group_number)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data)
        else:
            return Response({'error': 'No data found for the provided ProjectGroup-ID..!'}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, project_group_number):

        instance = self.get_object(project_group_number)
        if instance != None:
            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid(raise_exception=True):
                project_group = serializer.save()
                suppgrp = SupplierOrganisation.objects.get(supplier_type = '4')
                if project_group.enable_panel:
                    obj, created =  ProjectGroupSupplier.objects.update_or_create(project_group=instance, supplier_org=suppgrp, defaults={'project_group':instance, 'supplier_org':suppgrp, 'completes':instance.project_group_completes, 'clicks':instance.project_group_clicks, 'cpi':(int(project_group.panel_reward_points)/1000),'supplier_status':'Live'})

                    projectgroup_panel_log(True,False,instance.id,request.user)

                    ## ******* Opinions Deal Side Survey Create Code Has Been Commeted By Durgesh ******* ## 
                    # req = create_panel(project_group)
                    # if req.status_code == 200:
                    #     return Response({'message':'Project added successfully..!'}, status=status.HTTP_200_OK)
                    # else:
                    #     project_group.enable_panel = False
                    #     project_group.save(force_update=True, update_fields=['enable_panel'])
                    #     convert_json = json.loads(req.text)
                    #     return Response(convert_json, status=status.HTTP_400_BAD_REQUEST)
                else:
                    try:
                        sup_obj = ProjectGroupSupplier.objects.get(project_group=instance, supplier_org=suppgrp)
                        sup_obj.supplier_status = 'Paused'
                        sup_obj.save()
                    except:
                        project_group.enable_panel = False
                        project_group.save(force_update=True, update_fields=['enable_panel'])
                        pass
                    req = delete_panel_data(project_group)
                    if req.status_code == 200:
                        pass
                    else:
                        project_group.enable_panel = False
                        project_group.save(force_update=True, update_fields=['enable_panel'])
                        pass

                    projectgroup_panel_log(False,True,instance.id,request.user)
                
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No data found for the provided ProjectGroup-ID..!'}, status=status.HTTP_404_NOT_FOUND)

class EmailSubjectView(viewsets.ModelViewSet):
    queryset = EmailSubject.objects.all()
    serializer_class = EmailSubjectSerializer

class UpdateEmailSubjectView(viewsets.ModelViewSet):
    queryset = EmailSubject.objects.all()
    serializer_class = EmailSubjectSerializer
    lookup_field = 'id'

class EmailInviteCountsView(viewsets.ModelViewSet):
    lookup_field = 'project_group_number'

    def retrieve(self, *args, **kwargs):
        try:
            project_group_number = self.kwargs['project_group_number']
            project_group_obj = ProjectGroup.objects.get(project_group_number = project_group_number)
            survey_screener_list = ProjectGroupPrescreener.objects.filter(project_group_id=project_group_obj,translated_question_id__parent_question__parent_question_prescreener_type = "Standard", is_enable = True).exclude( translated_question_id__parent_question__parent_question_number__in = ["Email","Phone","Address"])
            
            serializer = SelectedQuestionAnswerListSerializer(survey_screener_list, many=True)
            serialized_data = JSONRenderer().render(serializer.data)
            json_data = json.loads(serialized_data)

            req = requests.post(settings.OPINIONSDEALSNEW_BASE_URL+'available-email-invites?survey_number='+ str(project_group_number) +'&country=' + project_group_obj.project_group_country.country_code + '&language=' + project_group_obj.project_group_language.language_code, json=json_data) 
            
            return Response({'no_of_email_invites': req.json()['available_email_invites']}, status=status.HTTP_200_OK)
            # return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'detail': 'Not found..!'}, status=status.HTTP_400_BAD_REQUEST)

class SendInvitesView(viewsets.ModelViewSet):
    queryset = EmailInvite.objects.all()
    serializer_class = EmailInviteSerializer

    def create(self, request, *args, **kwargs):
        # return Response({'error':'The survey invitation for the panel is currently under maintenance. Please check back later.'},status=status.HTTP_400_BAD_REQUEST)
    
        panel_source = SupplierOrganisation.objects.get(supplier_type = "4")
        survey_number = request.data.get('survey_number')
        try:
            project_group_obj = ProjectGroup.objects.get(project_group_number = survey_number)
            if project_group_obj.enable_panel == True:
                survey_screener_list = ProjectGroupPrescreener.objects.filter(project_group_id=project_group_obj,translated_question_id__parent_question__parent_question_prescreener_type = "Standard", is_enable = True).exclude( translated_question_id__parent_question__parent_question_number__in = ["Email","Phone","Address"])
                
                serializer = SelectedQuestionAnswerListSerializer(survey_screener_list, many=True)
                serialized_data = JSONRenderer().render(serializer.data)
                json_data = json.loads(serialized_data)

                if json_data == []:
                    json_data = [
                        {
                            'parent_question_number': 'Age', 
                            'question_category': 'DEMO', 
                            'parent_question_prescreener_type': 'Standard', 
                            'answer_options': [], 
                            'allowedRangeMin': '18', 
                            'allowedRangeMax': '99', 
                            'zipcode_counts': 0
                        },
                        {
                            'parent_question_number': 'Gender', 
                            'question_category': 'DEMO', 
                            'parent_question_prescreener_type': 'Standard', 
                            'answer_options': ['Gender_1', 'Gender_2', 'Gender_3', 'Gender_4'], 
                            'allowedRangeMin': '0', 
                            'allowedRangeMax': '100', 
                            'zipcode_counts': 0
                        } 
                    ]
            
                request.data['survey_number'] = project_group_obj.id
                
                serializer = StoreEmailInviteSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)

                email_invite_obj = serializer.save()
                if int(email_invite_obj.no_of_invites) > 0:
                    data = {
                        "country": project_group_obj.project_group_country.country_code,
                        "language": project_group_obj.project_group_language.language_code,
                        "number_of_invites": email_invite_obj.no_of_invites,
                        "survey_url": project_group_obj.project_group_surveyurl + '&source='+ str(panel_source.id),
                        "subject_line": email_invite_obj.email_subjectline.email_subject_line,
                        "schedule": datetime.strftime(email_invite_obj.schedule, "%Y-%m-%d %H:%M:%S"),
                        "survey_number": project_group_obj.project_group_number,
                        "survey_reward_points": project_group_obj.panel_reward_points,
                        "selected_question_answers": json_data
                    }

                    req = requests.post(settings.OPINIONSDEALSNEW_BASE_URL + 'send-email-invites', json=data)

                    if req.status_code == 200:
                        return Response(serializer.data, status=status.HTTP_201_CREATED, )
                    else:
                        return Response(req.json(), status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"error":"We Can't Send Zero Number Of Invites.!"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error":"We Can't Send Email Invitation to Panelist. You Need to First Panel Enabled True.!"},status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            return Response({'detail': 'Invalid survey number'}, status=status.HTTP_400_BAD_REQUEST)


class PanelistCompletionCountView(viewsets.ModelViewSet):

    def retrieve(self, request, *args, **kwargs):
        source = self.kwargs['source']
        resp_detail_object = RespondentDetail.objects.filter(source=source, resp_status='4').annotate(month=TruncMonth('start_time')).values('month').annotate(completion_count=Count('id'))
        completion_count_list = list(resp_detail_object.values_list('completion_count', flat=True))
        month_list =[datetime.strftime(month_name,"%b-%Y") for month_name in resp_detail_object.values_list('month',flat=True).order_by("month")]

        return Response({'completion_count_list': completion_count_list,'month_list': month_list}, status=status.HTTP_200_OK)


class MyPagenumberPagination(PageNumberPagination):
    page_size = '10'

class PanelistSurveyHistory(viewsets.ModelViewSet):
    serializer_class = PanelistSurveyHistorySerializer
    pagination_class = MyPagenumberPagination
    lookup_field = 'id'

    def get_queryset(self):
        pid = self.kwargs['id']
        resp_detail_obj = RespondentDetail.objects.filter(respondenturldetail__pid=pid)
        return resp_detail_obj

    def retrieve(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProjectGroupAddSlickRouterView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectGroupAddSlickRouterSerializer

    '''
        class to get a single instance of Project Group object and to update it.
    '''

    def get_object(self, project_group_number):

        try:
            return ProjectGroup.objects.get(project_group_number=project_group_number)
        except ProjectGroup.DoesNotExist:
            return None

    def get(self, request, project_group_number):

        instance = self.get_object(project_group_number)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data)
        else:
            return Response({'error': 'No data found for the provided ProjectGroup-ID..!'}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, project_group_number):

        instance = self.get_object(project_group_number)
        if instance != None:
            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid(raise_exception=True):
                project_group = serializer.save()
                suppgrp = SupplierOrganisation.objects.get(supplier_type = '4')
                if project_group.enable_panel:
                    obj, created =  ProjectGroupSupplier.objects.update_or_create(project_group=instance, supplier_org=suppgrp, defaults={'project_group':instance, 'supplier_org':suppgrp, 'completes':instance.project_group_completes, 'clicks':instance.project_group_clicks, 'cpi':(int(project_group.panel_reward_points)/1000),'supplier_status':'Live'})
                    req = create_slick_router(project_group)
                    if req.status_code == 200:
                        return Response({'message':'Project added successfully..!'}, status=status.HTTP_200_OK)
                    else:
                        project_group.enable_panel = False
                        project_group.save(force_update=True, update_fields=['enable_panel'])
                        convert_json = json.loads(req.text)
                        return Response(convert_json, status=status.HTTP_400_BAD_REQUEST)
                else:
                    try:
                        sup_obj = ProjectGroupSupplier.objects.get(project_group=instance, supplier_org=suppgrp)
                        sup_obj.supplier_status = 'Paused'
                        sup_obj.save()
                    except:
                        project_group.enable_panel = False
                        project_group.save(force_update=True, update_fields=['enable_panel'])
                        pass
                    req = delete_panel_data(project_group)
                    if req.status_code == 200:
                        pass
                    else:
                        project_group.enable_panel = False
                        project_group.save(force_update=True, update_fields=['enable_panel'])
                        pass
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No data found for the provided ProjectGroup-ID..!'}, status=status.HTTP_404_NOT_FOUND)
        


class SurveyFetchForOpinionsdeal(APIView):
    permission_classes = (ODPanelAuthPermission,)

    def post(self, request):
        
        survey_list = []

        project_grp_list = ProjectGroup.objects.filter(project_group_status = "Live",enable_panel = True)
        
        for project_grp in project_grp_list:
            survey_questions = panel_survey_questions_create_update(project_grp)
            survey_list.append(survey_questions)

        return Response(survey_list, status=status.HTTP_200_OK)
    

class CountryLanguageMappingListForOpinionsDealAPI(APIView):

    def get(self, request):

        country_language_obj = ClientDBCountryLanguageMapping.objects.all().values(
            "toluna_client_language_id",
            "zamplia_client_language_id",
            "client_language_name",
            "client_language_description",
            "country_lang_guid",
            language_code = F("lanugage_id__language_code"),
            country_code = F("country_id__country_code"),
            ).order_by("id")

        return Response(country_language_obj, status=status.HTTP_200_OK)


class PanelOpinionsDealSurveyPriorityAPI(APIView):
    permission_classes = (ODPanelAuthPermission,)
    
    def get(self, request):

        survey_priority_obj = RountingPriority.objects.filter(project_group__project_group_status = "Live",project_group__enable_panel = True).values_list(
            'project_group__project_group_number', flat=True
        )
        return Response(survey_priority_obj, status=status.HTTP_200_OK)
