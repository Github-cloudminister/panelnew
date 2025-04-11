# Basic Import
import requests, concurrent, datetime, requests, concurrent.futures

#Django import
from django.conf import settings
from django.db.models import Case, Value, When, Sum, Q, ExpressionWrapper
from django.db.models.functions import Cast,Coalesce
from django.db.models.aggregates import Count
from django.db.models.expressions import F

#Restframework impport
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions, status, generics
from rest_framework.permissions import IsAuthenticated

#3rd party import
from knox.auth import TokenAuthentication

#App import
from ClientSupplierAPIIntegration.models import *
from ClientSupplierAPIIntegration.TolunaClientAPI.models import ClientDBCountryLanguageMapping
from Logapp.models import CeleryAPICallLog
from Prescreener.models import ProjectGroupPrescreener
from Project.serializers import median_value
from Project.models import ProjectGroup, Project, ProjectGroupSubSupplier, ProjectGroupSupplier
from Questions.models import TranslatedAnswer, TranslatedQuestion
from affiliaterouter.models import RountingPriority
from feasibility.views import MyPagenumberPagination
from .models import *
from .serializers import *
from ClientSupplierAPIIntegration.models import *


max_workers = 2 if settings.SERVER_TYPE == 'localhost' else 30

class CustomerAuthPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        auth_token = request.META.get('HTTP_AUTHORIZATION')
        if auth_token != None:
            if '982df7e4793d0bea0e208ef52ce18b6d' in auth_token.split('Token '):
                return True
        return False

class CustomerDefaultSupplySourcesAPI(generics.ListCreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomerDefaultSupplySourcesSerializer
    queryset = CustomerDefaultSupplySources.objects.all()


class getCustDefaultSupplySourceAPI(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomerDefaultSupplySourcesSerializer
    queryset = CustomerDefaultSupplySources.objects.all()

    def get_queryset(self):
        customer_obj = self.request.GET.get('customer')
        query_set = CustomerDefaultSupplySources.objects.filter(customerOrg=customer_obj)
        return query_set


class CustomerDefaultSubSupplySourcesAPI(generics.ListCreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomerDefaultSubSupplySourcesSerializer
    queryset = CustomerDefaultSubSupplierSources.objects.all()


class getCustDefaultSubSupplySourceAPI(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomerDefaultSubSupplySourcesSerializer
    queryset = CustomerDefaultSubSupplierSources.objects.all()

    def get_queryset(self):
        customer_obj = self.request.GET.get('customer')
        query_set = CustomerDefaultSubSupplierSources.objects.filter(customerOrg=customer_obj)
        return query_set



class UpdateMultipleCustomerDefaultSupplySourcesAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def post(self, request):
        no_supply_sources_list = []
        payload_list = request.data

        for supply in payload_list:
            default_source_obj = CustomerDefaultSupplySources.objects.filter(supplierOrg__id=supply['supplier_id'], customerOrg__id=supply['customer_id'])
            if not default_source_obj:
                no_supply_sources_list.append({'supplier_id':supply['supplier_id'], 'customer_id':supply['customer_id']})
            else:
                default_source_obj.update(is_active = supply.get('isAdded'),default_max_cpi=supply.get('default_max_cpi'), default_max_completes=supply.get('default_max_completes'), default_max_clicks=supply.get('default_max_clicks'))

        return Response(data={'message':'Default Supply Sources Updated Successfully for all Surveys', 'No Default Supply Sources available for':no_supply_sources_list})
    

class UpdateMultipleCustomerDefaultSubSupplySourcesAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def post(self, request):
        no_supply_sources_list = []
        payload_list = request.data

        for supply in payload_list:
            default_source_obj = CustomerDefaultSubSupplierSources.objects.filter(sub_supplierOrg__id=supply['sub_supplier_id'], customerOrg__id=supply['customer_id'])
            if not default_source_obj:
                no_supply_sources_list.append({'sub_supplier_id':supply['sub_supplier_id'], 'customer_id':supply['customer_id']})
            else:
                default_source_obj.update(is_active = supply.get('isAdded'),default_max_cpi=supply.get('default_max_cpi'), default_max_completes=supply.get('default_max_completes'), default_max_clicks=supply.get('default_max_clicks'))

        return Response(data={'message':'Default Sub Supply Sources Updated Successfully for all Surveys', 'No Default Sub Supply Sources available for':no_supply_sources_list})


class ClientSurveysListAPI(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = MyPagenumberPagination
    serializer_class = ClientSurveysListSerializer

    def get_queryset(self):
        status = self.request.GET.get('status')
        survey_no = self.request.GET.get('survey_no')
        country = self.request.GET.get('country')
        language = self.request.GET.get('language')
        survey = self.request.GET.get('survey')
        sortby = self.request.GET.get('sortby')

        query_set = ProjectGroup.objects.filter(
            project__project_customer__customer_url_code__in=['toluna','zamplia','sago']).order_by(sortby)
        if status:
            query_set = query_set.filter(project_group_status = status)
        if survey_no:
            query_set = query_set.filter(project_group_number = survey_no)
        if country:
            query_set = query_set.filter(project_group_country = country)
        if language:
            query_set = query_set.filter(project_group_language = language)
        if survey:
            query_set = query_set.filter(project__project_customer__customer_url_code = survey)

        return query_set


class ListClientDBCountryLanguageAPI(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ListClientDBCountryLanguageSerializer
    queryset = ClientDBCountryLanguageMapping.objects.order_by('client_language_description')



class TotalCustomerRevenueMonthWiseCountApi(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes =(IsAuthenticated,)

    def get(self, request):
        requested_months = request.GET.get('months')
        requested_years = request.GET.get('year')

        if requested_months in ['', None, 'undefined']:
            requested_months = datetime.now().month
        else:
            requested_months = requested_months.split(',')
        if requested_years in ['', None, 'undefined']:
            requested_years = datetime.now().year
        else:
            requested_years = requested_years.split(',')

        if type(requested_months) == int:
            resp_details_list = RespondentDetail.objects.filter(respondentdetailsrelationalfield__project__project_customer__customer_url_code='toluna',end_time_day__month=requested_months, url_type='Live')
        elif type(requested_months) == list:
            resp_details_list = RespondentDetail.objects.filter(respondentdetailsrelationalfield__project__project_customer__customer_url_code='toluna',end_time_day__month__in=requested_months, url_type='Live')

        if type(requested_years) == int:
            resp_details_list = resp_details_list.filter(respondentdetailsrelationalfield__project__project_customer__customer_url_code='toluna',end_time_day__year=requested_years)
        elif type(requested_years) == list:
            resp_details_list = resp_details_list.filter(respondentdetailsrelationalfield__project__project_customer__customer_url_code='toluna',end_time_day__year__in=requested_years)

        resp_details_list = resp_details_list.values('end_time_day__month', 'respondentreconcilation__verified_at__date').annotate(
            customer_name=F('respondentdetailsrelationalfield__project__project_customer__cust_org_name'), 
            customer_url_code=F('respondentdetailsrelationalfield__project__project_customer__customer_url_code'), 
            completes=Count('resp_status', filter=Q(resp_status='4')), 
            incompletes=Count('resp_status',filter=Q(resp_status='3')),
            terminates=Count('resp_status',filter=Q(resp_status='5')), 
            quota_full=Count('resp_status',filter=Q(resp_status='6')),
            security_terminate=Count('resp_status',filter=Q(resp_status='7')), 
            starts=Cast(F('incompletes')+F('completes')+F('terminates')+F('quota_full')+F('security_terminate'), output_field=models.FloatField()), 
            conversion_rate=Case(
                When(Q(starts=0),then=Cast(0.0, output_field=models.DecimalField(max_digits=7,decimal_places=2))), 
                default=Cast(F('completes')/F('starts')*100, output_field=models.DecimalField(max_digits=7,decimal_places=2))
            ),
            revenue=Coalesce(
                Sum(
                    'project_group_cpi', 
                    filter=Q(resp_status__in=['4','9'])
                ),0.0
            ),
            expense=Coalesce(
                Sum(
                    'supplier_cpi', 
                    filter=Q(resp_status='4')
                ), 0.0
            ),
            margin=Case(
                When(Q(revenue=0.0)|Q(revenue=None),then=Cast(0.0, models.DecimalField(max_digits=7,decimal_places=2))), 
                default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'), output_field=models.DecimalField(max_digits=7,decimal_places=2)),
            ),
            client_rejected=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='8', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ),
            completesII=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='4', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ),
            pvp_rejected=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='9', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ),
            rejection_rate=Cast(
                Case(When(Q(completesII=0) & Q(client_rejected=0) & Q(pvp_rejected=0),then='completesII'), 
                default=(F('client_rejected') / (F('completesII') + F('client_rejected') + F('pvp_rejected')))*100), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            )
        )
        return Response(resp_details_list)
        

class TotalSupplierRevenueMonthWiseCountApi(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        requested_months = request.GET.get('months')
        requested_years = request.GET.get('year')

        if requested_months in ['', None, 'undefined']:
            requested_months = datetime.now().month
        else:
            requested_months = requested_months.split(',')
        if requested_years in ['', None, 'undefined']:
            requested_years = datetime.now().year
        else:
            requested_years = requested_years.split(',')

        if type(requested_months) == int:
            resp_details_list = RespondentDetail.objects.filter(respondentdetailsrelationalfield__project__project_customer__customer_url_code='toluna',end_time_day__month=requested_months, url_type='Live')
        elif type(requested_months) == list:
            resp_details_list = RespondentDetail.objects.filter(respondentdetailsrelationalfield__project__project_customer__customer_url_code='toluna',end_time_day__month__in=requested_months, url_type='Live')

        if type(requested_years) == int:
            resp_details_list = resp_details_list.filter(respondentdetailsrelationalfield__project__project_customer__customer_url_code='toluna',end_time_day__year=requested_years)
        elif type(requested_years) == list:
            resp_details_list = resp_details_list.filter(respondentdetailsrelationalfield__project__project_customer__customer_url_code='toluna',end_time_day__year__in=requested_years)

        resp_details_list = resp_details_list.values('end_time_day__month').annotate(
            supplier_name=Case(
                When(Q(respondentdetailsrelationalfield__source__supplier_name=None),then=Value('-')), 
                default=F('respondentdetailsrelationalfield__source__supplier_name')
            ), 
            completes=Count('resp_status', filter=Q(resp_status='4')), 
            incompletes=Count('resp_status',filter=Q(resp_status='3')),
            terminates=Count('resp_status',filter=Q(resp_status='5')), 
            quota_full=Count('resp_status',filter=Q(resp_status='6')), 
            security_terminate=Count('resp_status',filter=Q(resp_status='7')), 
            starts=Cast(
                F('incompletes')+F('completes')+F('terminates')+F('quota_full')+F('security_terminate'), 
                output_field=models.DecimalField(max_digits=7, decimal_places=2)
            ), 
            conversion_rate=Case(
                When(Q(starts=0),then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))), 
                default=Cast(
                    (F('completes')/F('starts'))*100, 
                    output_field=models.DecimalField(max_digits=7, decimal_places=2)
                )
            ), 
            revenue=Coalesce(
                Sum(
                    'project_group_cpi', 
                    filter=Q(resp_status__in=['4','9'])
                ), 0.0
            ), 
            expense=Coalesce(
                Sum(
                    'supplier_cpi', 
                    filter=Q(resp_status='4'), 
                ), 0.0
            ), 
            margin=Case(
                When(
                    Q(revenue=0.0)|Q(revenue=None),
                    then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))
                ),
                default=Cast(
                    ((F('revenue')-F('expense'))*100)/F('revenue'), 
                    output_field=models.DecimalField(max_digits=7,decimal_places=2)
                )
            ), 
            client_rejected=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='8', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ), 
            completesII=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='4', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ), 
            pvp_rejected=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='9', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ), 
            rejection_rate=Case(
                When(
                    Q(completesII=0) & Q(pvp_rejected=0),
                    then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))), 
                default=Cast(
                    (F('client_rejected') / (F('completesII') + F('client_rejected')))*100, 
                    output_field=models.DecimalField(max_digits=7,decimal_places=2)
                )
            )
        )

        return Response(resp_details_list)



class ClientSurveyWiseQuotasDataView(generics.ListAPIView):
    serializer_class = ClientQuotaDataSerializer

    def post(self,request):

        survey_no = request.data['survey_no']

        query_set = ClientQuota.objects.filter(project_group__project_group_number=survey_no)
        serializer = self.serializer_class(query_set, many=True)

        return Response({"Client_data":serializer.data}, status=status.HTTP_200_OK)
    

class ClientSupplyProjectGroupStatusUpdateView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        project_group_number = self.request.GET.get('survey_no')    
        statuss = self.request.GET.get('status')    
        project_group_obj = ProjectGroup.objects.filter(project_group_number = project_group_number).update(project_group_status = statuss)

        return Response({"success":"Survey Status Update Successfully..!"}, status=status.HTTP_200_OK)
    


class ClientProjectGroupSupplierDataView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        survey_no = self.request.GET.get('survey_no')
        survey_wise_project_supplier = ProjectGroupSupplier.objects.filter(project_group__project_group_number = survey_no).values(
            survey_id = F('project_group'),
            survey_number = F('project_group__project_group_number'),
            supplier_name = F('supplier_org__supplier_name'),
            supplier_statuss = F('supplier_status'),
            complete = F('completes'),
            click = F('clicks'),
            cpis = F('cpi'),
            supplier_survey_urls = F('supplier_survey_url'),
            incidence = F('project_group__project_group_incidence'),
            loi = F('project_group__project_group_loi'),
            ).annotate(
            quota_full = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status=6, respondentdetailsrelationalfield__respondent__url_type='Live'), distinct=True),
            security_terminate = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status=7, respondentdetailsrelationalfield__respondent__url_type='Live'), distinct=True),
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
        
        return Response({"survey_supplier":survey_wise_project_supplier}, status=status.HTTP_200_OK)


class ClientSurveyQuotaUpdateView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def post(self, request):
        quota_id_list = request.data['quota_id']
        survey_number = request.data['survey_number']
        base_url = settings.TOLUNA_CLIENT_BASE_URL
        projectgroup = ProjectGroup.objects.get(project_group_number=survey_number)
        
        guid = ClientDBCountryLanguageMapping.objects.get(
            lanugage_id = projectgroup.project_group_language,
            country_id = projectgroup.project_group_country
        ).country_lang_guid
        prescreener_question_dict = {}
        added_question = []
        for quota_id in quota_id_list:
            survey_base_url = f'{base_url}/IPExternalSamplingService/ExternalSample/{guid}/QuotaStatus/{quota_id}'

            response = requests.get(survey_base_url, headers={'API_AUTH_KEY' : settings.TOLUNA_API_AUTH_KEY}).json()

            client_quota_obj= ClientQuota.objects.get(quota_id=quota_id)
            client_quota_obj.completes_required = int(response['CompletesRequired'])
            client_quota_obj.completes_remaining = int(response['EstimatedCompletesRemaining'])
            client_quota_obj.quota_json_data = response
            client_quota_obj.save()

            for layer in response['Layers']:
                client_layer_obj = ClientLayer.objects.get(layer_id=layer['LayerID'])
                client_layer_obj.client_quota = client_quota_obj
                client_layer_obj.save()
                for subquota in layer['SubQuotas']:
                    client_subquota_obj = ClientSubQuota.objects.get(subquota_id=subquota['SubQuotaID'], client_layer=client_layer_obj)
                    client_subquota_obj.current_completes = subquota['CurrentCompletes']
                    client_subquota_obj.target_completes = subquota['MaxTargetCompletes']
                    client_subquota_obj.save()
                    for que_ans in subquota['QuestionsAndAnswers']:
                        if que_ans['QuestionID'] in [2910004,2910002,1012467,2910205,1012468,2910005,2910208]:
                            client_subquota_obj.delete()
                            break
                        try:
                            ques_mapping_obj = TranslatedQuestion.objects.get(
                                toluna_question_id=que_ans['QuestionID'],
                                lang_code=client_quota_obj.client_survey.project_group.project_group_language)
                        except:
                            client_subquota_obj.delete() 
                            break
                        ques_ans_obj, created = ClientSurveyPrescreenerQuestions.objects.update_or_create(
                            client_subquota=client_subquota_obj,
                            client_question_mapping=ques_mapping_obj,
                            defaults = {
                                'is_routable':que_ans['IsRoutable'],
                                'client_name':client_quota_obj.client_survey.project_group.project.project_customer.customer_url_code})

                        if que_ans['QuestionID'] == 1001042:
                            zip_list = que_ans['AnswerValues']
                            zipcode_question_available = True
                        if que_ans['QuestionID'] == 1001538:
                            age_ranges = {2006351:'13-17', 2006352:'18-24',2006353:'25-29',2006354:'30-34',2006355:'35-39',2006356:'40-44',2006357:'45-49',2006358:'50-54',2006359:'55-59',2006360:'60-64',2006361:'65-100'}
                            allowed_ranges = [age_ranges[a] for a in que_ans['AnswerIDs']]
                            allowed_ranges = allowed_ranges + que_ans['AnswerValues']
                            age_ranges = []
                            min_range = ""
                            max_range = ""
                            for a in allowed_ranges:
                                if min_range not in ["", None]:
                                    min_range= f"{min_range},{a.split('-')[0]}"
                                    max_range= f"{max_range},{a.split('-')[1]}"
                                else:
                                    min_range= a.split('-')[0]
                                    max_range= a.split('-')[1]
                            ques_ans_obj.allowedRangeMin = min_range
                            ques_ans_obj.allowedRangeMax = max_range
                            ques_ans_obj.save()
                        else:
                            min_range = "0"
                            max_range = "100"

                        if not que_ans['AnswerIDs']:
                            answer_qs = list(TranslatedAnswer.objects.filter(
                                translated_parent_question = ques_mapping_obj).values_list('id',flat=True))
                            ques_ans_obj.open_end_ans_options = que_ans['AnswerValues']
                            ques_ans_obj.save()
                        else:
                            answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj, 
                            toluna_answer_id__in = que_ans['AnswerIDs']).values_list('id',flat=True))
                            ques_ans_obj.client_answer_mappings.clear()

                            ques_ans_obj.client_answer_mappings.add(*answer_qs)
                        
                        if ques_mapping_obj in added_question:
                            # When question is already added in dict and we just need to update the Answer options and min-max ranges
                            prescreener_question_dict[ques_mapping_obj]['allowedoptions']+=answer_qs
                            if min_range not in prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']:
                                prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']},{min_range}"
                                prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']},{max_range}"
                        else:
                            added_question.append(ques_mapping_obj)
                            prescreener_question_dict[ques_mapping_obj] = {
                                "allowedoptions" : answer_qs,
                                "allowedRangeMin" : min_range,
                                "allowedRangeMax" : max_range,
                            }
            seq = 1
            ProjectGroupPrescreener.objects.filter(project_group_id = client_quota_obj.client_survey.project_group).update(is_enable = False)
            for question_key, values in prescreener_question_dict.items():
                if question_key == '1001538':
                    values.update({'sequence' : 1})
                elif question_key == '1001007':
                    values.update({'sequence' : 2})
                elif question_key == '1001042':
                    values.update({'sequence' : 3})
                else:
                    values.update({'sequence' : seq})
                seq+=1
                ques_ans_obj, created = ProjectGroupPrescreener.objects.update_or_create(
                                project_group_id = client_quota_obj.client_survey.project_group,
                                translated_question_id = question_key,
                                defaults = {
                                "allowedRangeMin" : values['allowedRangeMin'],
                                "allowedRangeMax" : values['allowedRangeMax'],
                                "sequence" : values['sequence'],
                                "is_enable" : True
                                }
                            )
                if question_key.toluna_question_id == '1001042' and zipcode_question_available:
                    ques_ans_obj.allowed_zipcode_list = zip_list
                    ques_ans_obj.save()

                ques_ans_obj.allowedoptions.clear()
                ques_ans_obj.allowedoptions.add(*values['allowedoptions'])
                seq+=1
        return Response({"message":"Survey Quota Updated Successfully"}, status=status.HTTP_200_OK)


class AllClientSurveyQuotaUpdateView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        # for Toluna Quotas and Qualifications Update
        quotaid_list = list(ClientQuota.objects.filter(
            client_survey__project_group__project__project_customer__customer_url_code = 'toluna',
            client_survey__project_group__project_group_status = 'Live').values_list('quota_id',flat=True))
        base_url = settings.TOLUNA_CLIENT_BASE_URL

        def parellel_surveys_updateing_func(quota_id):
            survey_base_url = f'{base_url}/IPExternalSamplingService/ExternalSample/6661984C-D520-4FF0-9B9F-2B5A57CEB7A6/QuotaStatus/{quota_id}'
            
            response = requests.get(survey_base_url, headers={'API_AUTH_KEY' : settings.TOLUNA_API_AUTH_KEY})

            if response.status_code not in [200,201]:
                return
            response = response.json()
            client_quota_obj= ClientQuota.objects.get(quota_id=quota_id)
            client_quota_obj.completes_required = int(response['CompletesRequired'])
            client_quota_obj.completes_remaining = int(response['EstimatedCompletesRemaining'])
            client_quota_obj.quota_json_data = response
            client_quota_obj.save()
            zipcode_question_available = False
            prescreener_question_dict = {}
            added_question = []

            for layer in response['Layers']:
                client_layer_obj = ClientLayer.objects.get(layer_id=layer['LayerID'])
                client_layer_obj.client_quota = client_quota_obj
                client_layer_obj.save()

                for subquota in layer['SubQuotas']:
                    client_subquota_obj = ClientSubQuota.objects.get(subquota_id=subquota['SubQuotaID'], client_layer=client_layer_obj)
                    client_subquota_obj.current_completes = subquota['CurrentCompletes']
                    client_subquota_obj.target_completes = subquota['MaxTargetCompletes']
                    client_subquota_obj.save()
                    for que_ans in subquota['QuestionsAndAnswers']:
                        if que_ans['QuestionID'] in [2910004,2910002,1012467,2910205,1012468,2910005,2910208]:
                            client_subquota_obj.delete()
                            break
                        try:
                            ques_mapping_obj = TranslatedQuestion.objects.get(
                                toluna_question_id=que_ans['QuestionID'],
                                lang_code=client_quota_obj.client_survey.project_group.project_group_language)
                        except:
                            client_subquota_obj.delete() 
                            break
                        ques_ans_obj, created = ClientSurveyPrescreenerQuestions.objects.update_or_create(
                            client_subquota=client_subquota_obj,
                            client_question_mapping=ques_mapping_obj,
                            defaults = {
                                'is_routable':que_ans['IsRoutable'],
                                'client_name':client_quota_obj.client_survey.project_group.project.project_customer.customer_url_code})

                        if que_ans['QuestionID'] == 1001042:
                            zip_list = que_ans['AnswerValues']
                            zipcode_question_available = True
                        if que_ans['QuestionID'] == 1001538:
                            age_ranges = {2006351:'13-17', 2006352:'18-24',2006353:'25-29',2006354:'30-34',2006355:'35-39',2006356:'40-44',2006357:'45-49',2006358:'50-54',2006359:'55-59',2006360:'60-64',2006361:'65-100'}
                            allowed_ranges = [age_ranges[a] for a in que_ans['AnswerIDs']]
                            allowed_ranges = allowed_ranges + que_ans['AnswerValues']
                            age_ranges = []
                            min_range = ""
                            max_range = ""
                            for a in allowed_ranges:
                                if min_range not in ["", None]:
                                    min_range= f"{min_range},{a.split('-')[0]}"
                                    max_range= f"{max_range},{a.split('-')[1]}"
                                else:
                                    min_range= a.split('-')[0]
                                    max_range= a.split('-')[1]
                            ques_ans_obj.allowedRangeMin = min_range
                            ques_ans_obj.allowedRangeMax = max_range
                            ques_ans_obj.save()
                        else:
                            min_range = "0"
                            max_range = "100"

                        if not que_ans['AnswerIDs']:
                            answer_qs = list(TranslatedAnswer.objects.filter(
                                translated_parent_question = ques_mapping_obj).values_list('id',flat=True))
                            ques_ans_obj.open_end_ans_options = que_ans['AnswerValues']
                            ques_ans_obj.save()
                        else:
                            answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj, 
                            toluna_answer_id__in = que_ans['AnswerIDs']).values_list('id',flat=True))
                            ques_ans_obj.client_answer_mappings.clear()

                            ques_ans_obj.client_answer_mappings.add(*answer_qs)
                        
                        if ques_mapping_obj in added_question:
                            # When question is already added in dict and we just need to update the Answer options and min-max ranges
                            prescreener_question_dict[ques_mapping_obj]['allowedoptions']+=answer_qs
                            if min_range not in prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']:
                                prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']},{min_range}"
                                prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']},{max_range}"
                        else:
                            added_question.append(ques_mapping_obj)
                            prescreener_question_dict[ques_mapping_obj] = {
                                "allowedoptions" : answer_qs,
                                "allowedRangeMin" : min_range,
                                "allowedRangeMax" : max_range,
                                "sequence" : len(added_question)
                            }
            seq = 1
            for question_key, values in prescreener_question_dict.items():
                ques_ans_obj, created = ProjectGroupPrescreener.objects.update_or_create(
                                project_group_id = client_quota_obj.client_survey.project_group,

                                translated_question_id = question_key,
                                defaults = {
                                "allowedRangeMin" : values['allowedRangeMin'],
                                "allowedRangeMax" : values['allowedRangeMax'],

                                "sequence" : values['sequence'],
                                "is_enable" : True
                                }
                            )
                if question_key.toluna_question_id == '1001042' and zipcode_question_available:
                    ques_ans_obj.allowed_zipcode_list = zip_list
                    ques_ans_obj.save()

                ques_ans_obj.allowedoptions.clear()
                ques_ans_obj.allowedoptions.add(*values['allowedoptions'])
                seq+=1

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            yield_results = list(executor.map(parellel_surveys_updateing_func, quotaid_list))
        

        # For Zamplia Quotas and Qualifications Update
        zamplia_base_url = settings.STAGING_URL
        survey_number_list = list(ClientQuota.objects.filter(
            client_survey__project_group__project__project_customer__customer_url_code = 'zamplia',
            client_survey__project_group__project_group_status = 'Live').values_list(
                'client_survey__project_group__project_group_number',flat=True))
        headers = {
            'Accept' : 'application/json',
            'ZAMP-KEY' : settings.STAGING_KEY
        }
        def parellel_zamplia_surveys_updateing_func(survey_number):
            prescreener_question_dict = {}
            added_question = []
            prjgrp_obj = ProjectGroup.objects.get(project_group_number = survey_number)
            client_quotas = requests.get(f'{zamplia_base_url}/Surveys/GetSurveyQuotas?SurveyId={survey_number}', headers=headers)
            client_qualifications = requests.get(f'{zamplia_base_url}/Surveys/GetSurveyQualifications?SurveyId={survey_number}', headers=headers)
            if client_quotas.status_code not in [200,201] and client_qualifications.status_code not in [200,201]:
                return
            client_quotas = client_quotas.json()['result']['data']
            client_qualifications = client_qualifications.json()['result']['data']
            for quota in client_quotas:
                client_quota_obj, created = ClientQuota.objects.update_or_create(
                quota_id=quota['QuotaId'],
                defaults={
                    'completes_required':quota['TotalQuotaCount'],
                    'completes_remaining':quota['TotalQuotaCount'],
                    'quota_json_data':quota})
                client_layer_obj, created = ClientLayer.objects.update_or_create(
                    layer_id=quota['QuotaId'],
                    client_quota=client_quota_obj)
                client_subquota_obj, created = ClientSubQuota.objects.update_or_create(
                    subquota_id=quota['QuotaId'],
                    client_layer=client_layer_obj,
                    defaults={
                        'target_completes':quota['TotalQuotaCount']})
                
                for que_ans in quota['QuotaQualifications']:
                    allowed_Range_Min = ""
                    allowed_Range_Max = ""

                    try:
                        ques_mapping_obj = TranslatedQuestion.objects.get(zamplia_question_id=que_ans['QuestionId'])
                        
                        ques_ans_obj, created = ClientSurveyPrescreenerQuestions.objects.update_or_create(
                            client_subquota=client_subquota_obj,
                            client_question_mapping=ques_mapping_obj,
                            defaults = {
                                "allowedRangeMin" : allowed_Range_Min,
                                "allowedRangeMax" : allowed_Range_Max,
                                "client_name" : "Zamplia"
                                })
                        
                        if ques_mapping_obj.parent_question_type == 'NU':
                            answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj).values_list('id',flat=True))
                            for anscode in que_ans['AnswerCodes']:
                                if allowed_Range_Min not in ["", None]:
                                        allowed_Range_Min = f"{allowed_Range_Min},{anscode.split('-')[0]}"
                                        allowed_Range_Max = f"{allowed_Range_Max},{anscode.split('-')[1]}"
                                else:
                                    allowed_Range_Min = anscode.split('-')[0]
                                    allowed_Range_Max = anscode.split('-')[1]
                        else:
                            allowed_Range_Min = "0"
                            allowed_Range_Min = "100"
                            answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj, 
                            zamplia_answer_id__in = que_ans['AnswerCodes']).values_list('id',flat=True))

                        ques_ans_obj.client_answer_mappings.clear()
                        ques_ans_obj.client_answer_mappings.add(*answer_qs)
                        ques_ans_obj.allowedRangeMin = allowed_Range_Min
                        ques_ans_obj.allowedRangeMax = allowed_Range_Max
                        ques_ans_obj.save()
                    except:
                        continue
            
            for qualification in client_qualifications:
                    
                    allowedRangeMin = ""
                    allowedRangeMax = ""
                    allowedZipList = []
                    try:
                        ques_mapping_obj = TranslatedQuestion.objects.get(zamplia_question_id=qualification['QuestionID'])
                        
                        if qualification['QuestionID'] in [2,'2']:
                            allowedZipList = qualification['AnswerCodes']

                        if ques_mapping_obj.parent_question_type == 'NU':
                            answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj).values_list('id',flat=True))
                            for anscode in qualification['AnswerCodes']:
                                if allowedRangeMin not in ["", None]:
                                        allowedRangeMin = f"{allowedRangeMin},{anscode.split('-')[0]}"
                                        allowedRangeMax = f"{allowedRangeMax},{anscode.split('-')[1]}"
                                else:
                                    allowedRangeMin = anscode.split('-')[0]
                                    allowedRangeMax = anscode.split('-')[1]
                        else:
                            allowedRangeMin = "0"
                            allowedRangeMax = "100"
                            answer_qs = list(TranslatedAnswer.objects.filter( 
                            zamplia_answer_id__in = qualification['AnswerCodes']).values_list('id',flat=True))
                        
                        if ques_mapping_obj in added_question:
                                # When question is already added in dict and we just need to update the Answer options and min-max ranges
                                prescreener_question_dict[ques_mapping_obj]['allowedoptions']+=answer_qs
                                if allowedRangeMin not in prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']:
                                    prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']},{allowedRangeMin}"
                                    prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']},{allowedRangeMax}"
                        else:
                            # When the question is added first time. 
                            added_question.append(ques_mapping_obj)
                            prescreener_question_dict[ques_mapping_obj] = {
                                "allowedoptions" : answer_qs,
                                "allowedRangeMin" : allowedRangeMin,
                                "allowedRangeMax" : allowedRangeMax,
                                "sequence" : len(added_question)
                            }
                    except:
                        continue

            seq = 1
            for question_key, values in prescreener_question_dict.items():
                ques_answer_obj, created = ProjectGroupPrescreener.objects.update_or_create(
                                project_group_id = prjgrp_obj,
                                translated_question_id = question_key,
                                defaults = {
                                "allowedRangeMin" : values['allowedRangeMin'],
                                "allowedRangeMax" : values['allowedRangeMax'],
                                "sequence" : values['sequence'],
                                "is_enable" : True
                                }
                            )
                if question_key.Internal_question_id == '112498':
                    ques_answer_obj.allowed_zipcode_list = allowedZipList
                    ques_answer_obj.save()
                ques_answer_obj.allowedoptions.clear()
                ques_answer_obj.allowedoptions.add(*values['allowedoptions'])
                seq+=1
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            yield_results = list(executor.map(parellel_zamplia_surveys_updateing_func, survey_number_list))
        return Response({"message":"Survey Quota Updated Successfully"}, status=status.HTTP_200_OK)


class TolunaPostQuotaUpdateNotifications(APIView):

    def post(self, request,projectcode):
        request_data = request.data
        if not request_data['IsLive'] and projectcode == 'WrR8dd4gg0drfrh5dedge2WfeFyRt7hfsA1E':
            client_quota_obj = ClientQuota.objects.filter(project_group__client_survey_number=request_data['SurveyID'])
            if len(client_quota_obj) == 1:
                project_group_obj = ProjectGroup.objects.filter(client_survey_number = request_data['SurveyID'])
                project_group_obj.update(project_group_status= 'Paused')
                ProjectGroupSupplier.objects.filter(project_group__in=project_group_obj).update(supplier_status = 'Paused')
                ProjectGroupSubSupplier.objects.filter(project_group__client_survey_number=request_data['SurveyID']).update(
                    sub_supplier_status = 'Paused')
            else:
                client_quota_obj.filter(quota_id=request_data['QuotaID']).delete()
        return Response({"message":"Survey Quota Updated Successfully"}, status=status.HTTP_200_OK)
    
class TolunaPostSurveyNotifications(APIView):

    def post(self, request,projectcode):
        request_data = request.data
        if request_data['Status'] == 'Closed' and projectcode == 'WrR8dgf587ujnh3yh3gdedge2WfeFyRt7hfsA1E':
            project_group_obj = ProjectGroup.objects.filter(client_survey_number = request_data['SurveyID'])
            project_group_obj.update(project_group_status= 'Paused')
            ProjectGroupSupplier.objects.filter(project_group__in=project_group_obj).update(supplier_status = 'Paused')
            ProjectGroupSubSupplier.objects.filter(project_group__client_survey_number=request_data['SurveyID']).update(
                sub_supplier_status = 'Paused')
        return Response({"message":"Survey Status Updated Successfully"}, status=status.HTTP_200_OK)


class RetrieveSurveyQualifyParametersAPI(generics.RetrieveUpdateDestroyAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SurveyQualifyParametersSetupSerializer
    queryset = SurveyQualifyParametersCheck.objects.all()
    lookup_field = 'customerOrg'


    def get(self, request, *args, **kwargs):

        if not SurveyQualifyParametersCheck.objects.filter(customerOrg__id=kwargs['customerOrg']):
            return Response(data={'message':'Detail Not Found'})

        return super().get(request, *args, **kwargs)


class SurveyQualifyParametersSetupAPI(generics.ListCreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SurveyQualifyParametersSetupSerializer
    queryset = SurveyQualifyParametersCheck.objects.all()


    def post(self, request):
        SurveyQualifyParametersCheck.objects.filter(customerOrg=request.data.get('customerOrg')).delete()
        return super().post(request)

class CountryLangSendToCeleryForSurveyFetch(APIView):
    permission_classes = (CustomerAuthPermission,)

    def get(self,request):
        CeleryAPICallLog.objects.create(APIname = 'CountryLangSendToCeleryForSurveyFetch-1')
        countrylangobj_list = ClientDBCountryLanguageMapping.objects.filter(
            country_lang_guid__isnull = False).values(
                'lanugage_id_id','country_id_id','toluna_client_language_id','zamplia_client_language_id',
                'client_language_name','client_language_description','country_lang_guid')
        return Response(countrylangobj_list, status=status.HTTP_200_OK)
    
class SurveyQualifyParametersCheckAPI(APIView):
    permission_classes = (CustomerAuthPermission,)

    def get(self,request):
        CeleryAPICallLog.objects.create(APIname = 'SurveyQualifyParametersCheckAPI-2')
        countrylangobj_list = SurveyQualifyParametersCheck.objects.filter(
            customerOrg__customer_url_code = request.data['customer_url_code']).values()
        return Response(countrylangobj_list, status=status.HTTP_200_OK)

class ClientSurveyListCeleryAPI(generics.ListCreateAPIView):
    permission_classes = (CustomerAuthPermission,)

    def post(self,request):
        CeleryAPICallLog.objects.create(APIname = 'ClientSurveyListCeleryAPI-3')
        try:
            surveys_list = request.data['surveys']
            try:
                projectobj = Project.objects.filter(
                    project_customer__customer_url_code = request.data['customer_url_code'],
                    project_status = 'Live').order_by('-id').first()
            except:
                return Response({"error":"Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)
            
            projectgroupobjlist = ProjectGroup.objects.filter(project__project_customer__customer_url_code = request.data['customer_url_code'])
            projectgrouplist = list(projectgroupobjlist.values_list('client_survey_number',flat=True))
            live_survey_list = []

            bulk_create_surveys = []
            bulk_update_surveys = []

            def multithred_survey_create(survey):

                live_survey_list.append(survey['client_survey_number'])
                if str(survey['client_survey_number']) in projectgrouplist:
                    projectgroupobj = ProjectGroup.objects.get(project_group_country_id = survey['project_group_country_id'],project_group_language_id = survey['project_group_language_id'],client_survey_number = survey['client_survey_number'])
                    projectgroupobj.project_group_name = survey['project_group_name']
                    projectgroupobj.project_group_loi = survey['project_group_loi']
                    projectgroupobj.project_group_incidence = survey['project_group_incidence']
                    projectgroupobj.project_group_cpi = survey['project_group_cpi']
                    projectgroupobj.project_group_completes = survey['project_group_completes']
                    projectgroupobj.project_group_clicks = 1000000
                    projectgroupobj.project_group_status = 'Live'
                    projectgroupobj.project_group_startdate = datetime.datetime.now().date()
                    projectgroupobj.project_group_enddate = (datetime.datetime.today() + datetime.timedelta(days=90)).date()
                    projectgroupobj.project_group_encodedR_value = survey['project_group_encodedR_value']
                    projectgroupobj.ad_enable_panel = True
                    projectgroupobj.project_group_redirectID = projectobj.project_redirectID
                    bulk_update_surveys.append(projectgroupobj)
                else:
                    project_group_survey_url = settings.SURVEY_URL+"survey?glsid="+survey['project_group_encodedS_value']
                    bulk_create_surveys.append(ProjectGroup(
                        client_survey_number = survey['client_survey_number'],
                        project_group_country_id = survey['project_group_country_id'],
                        project_group_language_id = survey['project_group_language_id'],
                        project_group_name = survey['project_group_name'],
                        project_group_loi = survey['project_group_loi'],
                        project_group_incidence = survey['project_group_incidence'],
                        project_group_cpi = survey['project_group_cpi'],
                        project_group_completes = survey['project_group_completes'],
                        project_group_clicks = 1000000,
                        project_id = projectobj.id,
                        project_group_status = 'Live',
                        threat_potential_score = projectobj.project_customer.threat_potential_score,
                        project_group_startdate = datetime.datetime.now().date(),
                        project_group_enddate = (datetime.datetime.today() + datetime.timedelta(days=90)).date(),
                        project_group_redirectID = projectobj.project_redirectID,
                        project_group_encodedS_value = survey['project_group_encodedS_value'],
                        project_group_encodedR_value = survey['project_group_encodedR_value'],
                        project_group_surveyurl = project_group_survey_url,
                        show_on_DIY = False,
                        project_group_ip_check = False,
                        project_group_pid_check = False,
                        ad_enable_panel = True,
                        project_group_liveurl = survey['project_group_liveurl'],
                        project_group_testurl = survey['project_group_testurl']
                        )
                    )
            
            with concurrent.futures.ThreadPoolExecutor(max_workers = max_workers) as executor:
                yield_results = list(executor.map(multithred_survey_create, surveys_list))

            ProjectGroup.objects.bulk_create(bulk_create_surveys)

            ProjectGroup.objects.bulk_update(bulk_update_surveys,['project_group_name','project_group_incidence','project_group_cpi','project_group_completes','project_group_clicks','project_group_status','project_group_startdate','project_group_enddate','project_group_redirectID','ad_enable_panel'])

            projectgroupobjlist.filter(project_group_status = 'Live').update(project_group_number = 1000000 + F('id'),excluded_project_group = [str(1000000 + F('id'))],project = projectobj)

            return Response({"message":"Survey Status Updated Successfully"}, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)


class ClientSurveysPause(generics.ListCreateAPIView):
    permission_classes = (CustomerAuthPermission,)

    def post(self,request):
        CeleryAPICallLog.objects.create(APIname = 'ClientSurveysPause-5')
        action_to_be_performed = request.data.get('action','survey_live')
        customer_url_code = request.data.get('customer_url_code')
        live_survey_numbers = request.data.get('live_survey_numbers',None)
        paused_survey_numbers = request.data.get('paused_client_survey_number',None)

        if request.data['customer_url_code'] in ['toluna','zamplia','sago']:

            if action_to_be_performed == 'survey_pause':
                ProjectGroup.objects.filter(
                project__project_customer__customer_url_code = customer_url_code,
                project_group_status = 'Live', client_survey_number__in = paused_survey_numbers).update(project_group_status = 'Paused')

                RountingPriority.objects.filter(project_group__client_survey_number__in = paused_survey_numbers).delete()
            else:
                if len(live_survey_numbers)>30:
                    ProjectGroup.objects.filter(
                        project__project_customer__customer_url_code = customer_url_code,
                        project_group_status = 'Live'
                    ).exclude(client_survey_number__in = live_survey_numbers).update(project_group_status = 'Paused')

                    RountingPriority.objects.filter(
                        project_group__project__project_customer__customer_url_code = customer_url_code
                        ).exclude(project_group__client_survey_number__in = live_survey_numbers).delete()

                # ProjectGroup.objects.filter(
                #     project_group_number__in = ProjeGroupForceStop.objects.all().values_list(
                #         'project_group__project_group_number',flat=True)).update(project_group_status='Paused')

            ProjectGroupSupplier.objects.filter(
                project_group__project__project_customer__customer_url_code = customer_url_code, supplier_status = 'Live',
                project_group__project_group_status = 'Paused').update(supplier_status = 'Paused')
                
            ProjectGroupSubSupplier.objects.filter(
                project_group__project__project_customer__customer_url_code = customer_url_code, 
                sub_supplier_status = 'Live', project_group__project_group_status = 'Paused').update(sub_supplier_status = 'Paused')
            
            return Response({"message":"Success"}, status=status.HTTP_200_OK)
        else:
            return Response({"error":"Customer URL code Not Found"}, status=status.HTTP_200_OK)
    
class ClientSurveySupplierlive(generics.ListCreateAPIView):
    permission_classes = (CustomerAuthPermission,)

    def post(self,request):
        CeleryAPICallLog.objects.create(APIname = 'ClientSurveySupplierlive-6')
        ProjectGroupSupplier.objects.filter(
            project_group__client_survey_number__in = request.data['client_survey_number']
        ).exclude(supplier_org__supplier_type__in = ['2']).update(supplier_status = 'Live')
        
        ProjectGroupSubSupplier.objects.filter(
            project_group__client_survey_number__in = request.data['client_survey_number']).update(sub_supplier_status = 'Live')
        
        return Response({"message":"Success"}, status=status.HTTP_200_OK)

class ClientSurveyOfQuotasListCeleryAPI(generics.ListCreateAPIView):
    permission_classes = (CustomerAuthPermission,)

    def post(self,request):
        CeleryAPICallLog.objects.create(APIname = 'ClientSurveyOfQuotasListCeleryAPI-4')
        try:
            if request.data['client_name'] == 'toluna':
                quotas_list = request.data['Quotas']
                def quotas_storing_func(quotas):
                    toluna_survey_number = list(quotas.keys())[0]
                    toluna_survey_quota = quotas[toluna_survey_number]
                    projectgroup_obj = ProjectGroup.objects.get(client_survey_number = toluna_survey_number)
                    apidbcountrylangmapping = ClientDBCountryLanguageMapping.objects.get(
                        country_id=projectgroup_obj.project_group_country,
                        lanugage_id=projectgroup_obj.project_group_language)
                    prescreener_question_dict = {}
                    added_question = []
                    age_question_available = False
                    gender_question_available = False
                    zipcode_question_available = False
                    for quota in toluna_survey_quota:
                        ClientQuota.objects.filter(quota_id=quota['QuotaID']).delete()
                        client_quota_obj, client_quota_obj_created = ClientQuota.objects.update_or_create(quota_id=quota['QuotaID'], defaults={'completes_required':quota['CompletesRequired'], 'completes_remaining':quota['EstimatedCompletesRemaining'],'project_group':projectgroup_obj, 'quota_json_data':quota})
                        for layer in quota['Layers']:
                            client_layer_obj, client_layer_obj_created = ClientLayer.objects.update_or_create(layer_id=layer['LayerID'],client_quota=client_quota_obj)
                            for subquota in layer['SubQuotas']:
                                client_subquota_obj, client_subquota_obj_created = ClientSubQuota.objects.update_or_create(subquota_id=subquota['SubQuotaID'], client_layer=client_layer_obj,defaults={'current_completes':subquota['CurrentCompletes'],'target_completes':subquota['MaxTargetCompletes']})
                                # SAVING A SURVEY'S QUESTIONS AND THEIR ALLOWED ANSWERS
                                for que_ans in subquota['QuestionsAndAnswers']:
                                    if que_ans['QuestionID'] in [2910004,2910002,1012467,2910205,1012468,2910005,2910208,1005151,2910001,2910002,2910004,2910005,2910010,2910012,2910206,2910207,2910208,2910209,2910227,1012467,1012468]:
                                        client_subquota_obj.delete()
                                        break
                                    try:
                                        ques_mapping_obj = TranslatedQuestion.objects.get(
                                            toluna_question_id=que_ans['QuestionID'],apidbcountrylangmapping=apidbcountrylangmapping)
                                    except:
                                        client_subquota_obj.delete()
                                        break
                                    ques_ans_obj, ques_ans_obj_created = ClientSurveyPrescreenerQuestions.objects.update_or_create(
                                        client_subquota=client_subquota_obj,client_question_mapping=ques_mapping_obj,
                                        defaults = {'is_routable':que_ans['IsRoutable'],
                                                    'client_name':projectgroup_obj.project.project_customer.customer_url_code})
                                    
                                    if que_ans['QuestionID'] == 1001042:
                                        zip_list = list(map(str, que_ans['AnswerValues']))
                                        zipcode_question_available = True
                                    if que_ans['QuestionID'] == 1001007:
                                        gender_question_available = True
                                    if que_ans['QuestionID'] == 1001538:
                                        age_question_available = True
                                        # This is Age question
                                        age_ranges = {2006351:'13-17', 2006352:'18-24',2006353:'25-29',2006354:'30-34',2006355:'35-39',2006356:'40-44',2006357:'45-49',2006358:'50-54',2006359:'55-59',2006360:'60-64',2006361:'65-100'}
                                        allowed_ranges = [age_ranges[a] for a in que_ans['AnswerIDs']]
                                        allowed_ranges = allowed_ranges + que_ans['AnswerValues']
                                        age_ranges = []
                                        min_range = ""
                                        max_range = ""
                                        for a in allowed_ranges:
                                            if min_range not in ["", None]:
                                                min_range= f"{min_range},{a.split('-')[0]}"
                                                max_range= f"{max_range},{a.split('-')[1]}"
                                            else:
                                                min_range= a.split('-')[0]
                                                max_range= a.split('-')[1]
                                        ques_ans_obj.allowedRangeMin = min_range
                                        ques_ans_obj.allowedRangeMax = max_range
                                        ques_ans_obj.save()
                                    else:
                                        min_range = "0"
                                        max_range = "100"

                                    if not que_ans['AnswerIDs']:
                                        answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj).values_list('id',flat=True))
                                        ques_ans_obj.open_end_ans_options = que_ans['AnswerValues']
                                        ques_ans_obj.save()
                                    else:
                                        answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj, 
                                        toluna_answer_id__in = que_ans['AnswerIDs']).values_list('id',flat=True))
                                        ques_ans_obj.client_answer_mappings.clear()

                                        ques_ans_obj.client_answer_mappings.add(*answer_qs)
                                    
                                    if ques_mapping_obj in added_question:
                                        # When question is already added in dict and we just need to update the Answer options and min-max ranges
                                        prescreener_question_dict[ques_mapping_obj]['allowedoptions']+=answer_qs
                                        if min_range not in prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']:
                                            prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']},{min_range}"
                                            prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']},{max_range}"
                                    else:
                                        # When the question is added first time. 
                                        added_question.append(ques_mapping_obj)
                                        prescreener_question_dict[ques_mapping_obj] = {
                                            "allowedoptions" : answer_qs,
                                            "allowedRangeMin" : min_range,
                                            "allowedRangeMax" : max_range,
                                        }

                            if not ClientSubQuota.objects.filter(client_layer=client_layer_obj).exists():
                                client_quota_obj.delete()
                                break
                    if not ClientQuota.objects.filter(project_group = projectgroup_obj).exists():
                        projectgroup_obj.project_group_status = 'Paused'
                        projectgroup_obj.save()
                        return
                    
                    # if Age Question not from toluna end and we added from our side
                    if not age_question_available:
                        question_data = TranslatedQuestion.objects.get(toluna_question_id = "1001538",apidbcountrylangmapping=apidbcountrylangmapping)
                        allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                            translated_parent_question = question_data).exclude(toluna_answer_id = '2006351').values_list('id',flat=True))
                        prescreener_question_dict[question_data] = {
                                            "allowedoptions" : allowedoptions_ids,
                                            "allowedRangeMin" : '18,25,30,35,40,45,50,55,60,65',
                                            "allowedRangeMax" : '24,29,34,39,44,49,54,59,64,100',
                                        }
                    # if Gender Question not from toluna end and we added from our side
                    if not gender_question_available:
                        question_data2 = TranslatedQuestion.objects.get(toluna_question_id="1001007",apidbcountrylangmapping=apidbcountrylangmapping)
                        allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                            translated_parent_question = question_data2).values_list('id',flat=True))        
                        prescreener_question_dict[question_data2] = {
                                            "allowedoptions" : allowedoptions_ids,
                                            "allowedRangeMin" : '',
                                            "allowedRangeMax" : '',
                                        }
                    # if Zip Code Question not from toluna end and we added from our side
                    if not zipcode_question_available:
                        question_data3 = TranslatedQuestion.objects.get(toluna_question_id="1001042",apidbcountrylangmapping=apidbcountrylangmapping)
                        allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                            translated_parent_question = question_data3).values_list('id',flat=True))        
                        prescreener_question_dict[question_data3] = {
                                            "allowedoptions" : allowedoptions_ids,
                                            "allowedRangeMin" : '',
                                            "allowedRangeMax" : '',
                                        }
                    seq = 4
                    ProjectGroupPrescreener.objects.filter(project_group_id = projectgroup_obj).update(is_enable = False)
                    for question_key, values in prescreener_question_dict.items():
                        if question_key == '1001538':
                            values.update({'sequence' : 1})
                        elif question_key == '1001007':
                            values.update({'sequence' : 2})
                        elif question_key == '1001042':
                            values.update({'sequence' : 3})
                        else:
                            values.update({'sequence' : seq})
                            seq+=1
                        ques_ans_obj, ques_ans_obj_created = ProjectGroupPrescreener.objects.update_or_create(
                                        project_group_id = projectgroup_obj,
                                        translated_question_id = question_key,
                                        defaults = {
                                        "allowedRangeMin" : values['allowedRangeMin'],
                                        "allowedRangeMax" : values['allowedRangeMax'],
                                        "sequence" : values['sequence'],
                                        "is_enable" : True
                                        }
                                    )
                        #zip answers list added if zip question available from Toluna side
                        if question_key.toluna_question_id == '1001042' and zipcode_question_available:
                            ques_ans_obj.allowed_zipcode_list = zip_list
                            ques_ans_obj.save()
                            
                        ques_ans_obj.allowedoptions.clear()
                        ques_ans_obj.allowedoptions.add(*values['allowedoptions'])
                    
                    #   Disable old prescreener added in survey
                    ProjectGroupPrescreener.objects.filter(
                        project_group_id = projectgroup_obj,translated_question_id__is_active = False).update(is_enable=False)
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    yield_results = list(executor.map(quotas_storing_func, quotas_list))
                
                return Response({"message":"Survey Status Updated Successfully"}, status=status.HTTP_200_OK)
            elif request.data['client_name'] == 'zamplia':

                def zamplia_quotas_update_create(surveys):

                    prescreener_question_dict = {}
                    added_question = []
                    try:
                        client_quotas = surveys['client_quotas']
                        client_qualifications = surveys['client_qualifications']
                        projectgroup_obj = ProjectGroup.objects.get(client_survey_number = surveys['survey_number'])
                    except:
                        return Response({"error":"Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)
                    for quota in client_quotas:
                        client_quota_obj, created = ClientQuota.objects.update_or_create(
                        quota_id=quota['QuotaId'],
                        defaults={
                            'project_group':projectgroup_obj,
                            'completes_required':quota['TotalQuotaCount'],
                            'completes_remaining':quota['TotalQuotaCount'],
                            'quota_json_data':quota})
                        client_layer_obj, created = ClientLayer.objects.update_or_create(
                            layer_id=quota['QuotaId'],
                            client_quota=client_quota_obj)
                        client_subquota_obj, created = ClientSubQuota.objects.update_or_create(
                            subquota_id=quota['QuotaId'],
                            client_layer=client_layer_obj,
                            defaults={
                                'target_completes':quota['TotalQuotaCount']})
                        
                        for que_ans in quota['QuotaQualifications']:
                            allowed_Range_Min = ""
                            allowed_Range_Max = ""

                            try:
                                ques_mapping_obj = TranslatedQuestion.objects.get(zamplia_question_id=que_ans['QuestionId'])
                                
                                ques_ans_obj, created = ClientSurveyPrescreenerQuestions.objects.update_or_create(
                                    client_subquota=client_subquota_obj,
                                    client_question_mapping=ques_mapping_obj,
                                    defaults = {
                                        "allowedRangeMin" : allowed_Range_Min,
                                        "allowedRangeMax" : allowed_Range_Max,
                                        "client_name" : "zamplia"
                                        })
                                
                                if ques_mapping_obj.parent_question_type == 'NU':
                                    answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj).values_list('id',flat=True))
                                    for anscode in que_ans['AnswerCodes']:
                                        if allowed_Range_Min not in ["", None]:
                                                allowed_Range_Min = f"{allowed_Range_Min},{anscode.split('-')[0]}"
                                                allowed_Range_Max = f"{allowed_Range_Max},{anscode.split('-')[1]}"
                                        else:
                                            allowed_Range_Min = anscode.split('-')[0]
                                            allowed_Range_Max = anscode.split('-')[1]
                                else:
                                    allowed_Range_Min = "0"
                                    allowed_Range_Min = "100"
                                    answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj, 
                                    zamplia_answer_id__in = que_ans['AnswerCodes']).values_list('id',flat=True))

                                ques_ans_obj.client_answer_mappings.clear()
                                ques_ans_obj.client_answer_mappings.add(*answer_qs)
                                ques_ans_obj.allowedRangeMin = allowed_Range_Min
                                ques_ans_obj.allowedRangeMax = allowed_Range_Max
                                ques_ans_obj.save()
                            except:
                                continue

                    age_question_available = False
                    gender_question_available = False
                    zipcode_question_available = False
                    allowedZipList = []
                    for qualification in client_qualifications:
                            
                            allowedRangeMin = ""
                            allowedRangeMax = ""
                            try:
                                ques_mapping_obj = TranslatedQuestion.objects.get(zamplia_question_id=qualification['QuestionID'])
                                
                                if qualification['QuestionID'] in [2,'2']:
                                    allowedZipList = qualification['AnswerCodes']
                                    zipcode_question_available = True

                                if qualification['QuestionID'] in [1,'1']:
                                    gender_question_available = True

                                if qualification['QuestionID'] in [29,'29']:
                                    age_question_available = True

                                if ques_mapping_obj.parent_question_type == 'NU':
                                    answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj).values_list('id',flat=True))
                                    for anscode in qualification['AnswerCodes']:
                                        if allowedRangeMin not in ["", None]:
                                                allowedRangeMin = f"{allowedRangeMin},{anscode.split('-')[0]}"
                                                allowedRangeMax = f"{allowedRangeMax},{anscode.split('-')[1]}"
                                        else:
                                            allowedRangeMin = anscode.split('-')[0]
                                            allowedRangeMax = anscode.split('-')[1]
                                else:
                                    allowedRangeMin = "0"
                                    allowedRangeMax = "100"
                                    answer_qs = list(TranslatedAnswer.objects.filter( 
                                    zamplia_answer_id__in = qualification['AnswerCodes']).values_list('id',flat=True))
                                
                                if ques_mapping_obj in added_question:
                                        # When question is already added in dict and we just need to update the Answer options and min-max ranges
                                        prescreener_question_dict[ques_mapping_obj]['allowedoptions']+=answer_qs
                                        if allowedRangeMin not in prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']:
                                            prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']},{allowedRangeMin}"
                                            prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']},{allowedRangeMax}"
                                else:
                                    # When the question is added first time. 
                                    added_question.append(ques_mapping_obj)
                                    prescreener_question_dict[ques_mapping_obj] = {
                                        "allowedoptions" : answer_qs,
                                        "allowedRangeMin" : allowedRangeMin,
                                        "allowedRangeMax" : allowedRangeMax,
                                    }
                            except:
                                continue

                    # if Age Question not from Zamplia end and we added from our side
                    if not age_question_available:
                        question_data = TranslatedQuestion.objects.get(Internal_question_id = "112521")
                        allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                            translated_parent_question = question_data).exclude(toluna_answer_id = '2006351').values_list('id',flat=True))
                        prescreener_question_dict[question_data] = {
                                            "allowedoptions" : allowedoptions_ids,
                                            "allowedRangeMin" : '18,25,30,35,40,45,50,55,60,65',
                                            "allowedRangeMax" : '24,29,34,39,44,49,54,59,64,100',
                                        }
                    # if Gender Question not from Zamplia end and we added from our side
                    if not gender_question_available:
                        question_data2 = TranslatedQuestion.objects.get(Internal_question_id="112499")
                        allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                            translated_parent_question = question_data2).values_list('id',flat=True))        
                        prescreener_question_dict[question_data2] = {
                                            "allowedoptions" : allowedoptions_ids,
                                            "allowedRangeMin" : '',
                                            "allowedRangeMax" : '',
                                        }
                    # if Zip Code Question not from Zamplia end and we added from our side
                    if not zipcode_question_available:
                        question_data3 = TranslatedQuestion.objects.get(Internal_question_id="112498")
                        allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                            translated_parent_question = question_data3).values_list('id',flat=True))        
                        prescreener_question_dict[question_data3] = {
                                            "allowedoptions" : allowedoptions_ids,
                                            "allowedRangeMin" : '',
                                            "allowedRangeMax" : '',
                                        }

                    seq = 4
                    ProjectGroupPrescreener.objects.filter(project_group_id = projectgroup_obj).update(is_enable = False)
                    for question_key, values in prescreener_question_dict.items():
                        if question_key == '1001538':
                            values.update({'sequence' : 1})
                        elif question_key == '1001007':
                            values.update({'sequence' : 2})
                        elif question_key == '1001042':
                            values.update({'sequence' : 3})
                        else:
                            values.update({'sequence' : seq})
                            seq+=1
                        ques_answer_obj, created = ProjectGroupPrescreener.objects.update_or_create(
                                        project_group_id = projectgroup_obj,
                                        translated_question_id = question_key,
                                        defaults = {
                                        "allowedRangeMin" : values['allowedRangeMin'],
                                        "allowedRangeMax" : values['allowedRangeMax'],
                                        "sequence" : values['sequence'],
                                        "is_enable" : True
                                        }
                                    )
                        if question_key.Internal_question_id == '112498':
                            ques_answer_obj.allowed_zipcode_list = allowedZipList
                            ques_answer_obj.save()
                        ques_answer_obj.allowedoptions.clear()
                        ques_answer_obj.allowedoptions.add(*values['allowedoptions'])
                    #   Disable old prescreener added in survey
                    ProjectGroupPrescreener.objects.filter(
                        project_group_id = projectgroup_obj,translated_question_id__is_active = False).update(is_enable=False)
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    yield_results = list(executor.map(zamplia_quotas_update_create, request.data['qualifications']))
                return Response({"message":"Survey Status Updated Successfully"}, status=status.HTTP_200_OK)
            
            elif request.data['client_name'] == 'sago':

                def sago_quotas_update_create(surveys):
                    
                    prescreener_question_dict = {}
                    added_question = []
                    try:
                        client_qualifications = surveys['client_qualifications']
                        projectgroup_obj = ProjectGroup.objects.get(client_survey_number = surveys['survey_number'])
                    except:
                        return Response({"error":"Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)
                    
                    age_question_available = False
                    gender_question_available = False
                    zipcode_question_available = False
                    allowedZipList = []
                    for que_ans in client_qualifications:
                        allowedRangeMin = ""
                        allowedRangeMax = ""
                        try:
                            ques_mapping_obj = TranslatedQuestion.objects.get(sago_question_id=que_ans['QualificationId'])
                            if ques_mapping_obj.parent_question_type == 'NU':
                                age_question_available = True
                                answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj).values_list('id',flat=True))
                                for anscode in que_ans['AnswerIds']:
                                    if allowedRangeMin not in ["", None]:
                                        allowedRangeMin = f"{allowedRangeMin},{anscode.split('-')[0]}"
                                        allowedRangeMax = f"{allowedRangeMax},{anscode.split('-')[1]}"
                                    else:
                                        allowedRangeMin = anscode.split('-')[0]
                                        allowedRangeMax = anscode.split('-')[1]
                            else:
                                allowedRangeMin = "0"
                                allowedRangeMax = "100"
                                answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj, 
                                sago_answer_id__in = que_ans['AnswerCodes']).values_list('id',flat=True))

                            if que_ans['QualificationId'] == 143:
                                allowedZipList = que_ans['AnswerIds']
                                zipcode_question_available = True

                            if que_ans['QualificationId'] == 60:
                                gender_question_available = True

                            if ques_mapping_obj in added_question:
                                # When question is already added in dict and we just need to update the Answer options and min-max ranges
                                prescreener_question_dict[ques_mapping_obj]['allowedoptions']+=answer_qs
                                if allowedRangeMin not in prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']:
                                    prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']},{allowedRangeMin}"
                                    prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']},{allowedRangeMax}"
                            else:
                                # When the question is added first time. 
                                added_question.append(ques_mapping_obj)
                                prescreener_question_dict[ques_mapping_obj] = {
                                    "allowedoptions" : answer_qs,
                                    "allowedRangeMin" : allowedRangeMin,
                                    "allowedRangeMax" : allowedRangeMax,
                                }
                        except:
                            projectgroup_obj.project_group_status = 'Paused'
                            projectgroup_obj.save()
                            return             
                    # if Age Question not from sago end and we added from our side
                    if not age_question_available:
                        question_data = TranslatedQuestion.objects.get(Internal_question_id = "112521")
                        allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                            translated_parent_question = question_data).exclude(toluna_answer_id = '2006351').values_list('id',flat=True))
                        prescreener_question_dict[question_data] = {
                                            "allowedoptions" : allowedoptions_ids,
                                            "allowedRangeMin" : '18,25,30,35,40,45,50,55,60,65',
                                            "allowedRangeMax" : '24,29,34,39,44,49,54,59,64,100',
                                        }
                    # if Gender Question not from sago end and we added from our side
                    if not gender_question_available:
                        question_data2 = TranslatedQuestion.objects.get(Internal_question_id="112499")
                        allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                            translated_parent_question = question_data2).values_list('id',flat=True))        
                        prescreener_question_dict[question_data2] = {
                                            "allowedoptions" : allowedoptions_ids,
                                            "allowedRangeMin" : '',
                                            "allowedRangeMax" : '',
                                        }
                    # if Zip Code Question not from sago end and we added from our side
                    if not zipcode_question_available:
                        question_data3 = TranslatedQuestion.objects.get(Internal_question_id="112498")
                        allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                            translated_parent_question = question_data3).values_list('id',flat=True))        
                        prescreener_question_dict[question_data3] = {
                                            "allowedoptions" : allowedoptions_ids,
                                            "allowedRangeMin" : '',
                                            "allowedRangeMax" : '',
                                        }
                    seq = 4
                    ProjectGroupPrescreener.objects.filter(project_group_id = projectgroup_obj).update(is_enable = False)
                    for question_key, values in prescreener_question_dict.items():
                        if question_key == '1001538':
                            values.update({'sequence' : 1})
                        elif question_key == '1001007':
                            values.update({'sequence' : 2})
                        elif question_key == '1001042':
                            values.update({'sequence' : 3})
                        else:
                            values.update({'sequence' : seq})
                            seq+=1
                        ques_answer_obj, created = ProjectGroupPrescreener.objects.update_or_create(
                                        project_group_id = projectgroup_obj,
                                        translated_question_id = question_key,
                                        defaults = {
                                        "allowedRangeMin" : values['allowedRangeMin'],
                                        "allowedRangeMax" : values['allowedRangeMax'],
                                        "sequence" : values['sequence'],
                                        "is_enable" : True
                                        }
                                    )
                        if question_key.Internal_question_id == '112498':
                            ques_answer_obj.allowed_zipcode_list = allowedZipList
                            ques_answer_obj.save()
                        ques_answer_obj.allowedoptions.clear()
                        ques_answer_obj.allowedoptions.add(*values['allowedoptions'])
                    #   Disable old prescreener added in survey
                    ProjectGroupPrescreener.objects.filter(
                        project_group_id = projectgroup_obj,translated_question_id__is_active = False).update(is_enable=False)
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    yield_results = list(executor.map(sago_quotas_update_create, request.data['qualifications']))
                return Response({"message":"Success"}, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)

class AddUpdateDefaultSupplier(APIView):

    def post(self,request):
        try:
            CeleryAPICallLog.objects.create(APIname = 'AddUpdateDefaultSupplier-7')
            clientname = request.data.get('clientname')

            survey_default_source_list = CustomerDefaultSupplySources.objects.filter(is_active=True,customerOrg__customer_url_code = clientname,supplierOrg__supplier_status = '1')
            survey_default_sub_supplier_source_list = CustomerDefaultSubSupplierSources.objects.filter(is_active=True,customerOrg__customer_url_code = clientname,sub_supplierOrg__sub_supplier_status = '1')

            projectgroup_obj_list = ProjectGroup.objects.filter(project__project_customer__customer_url_code = clientname,project_group_status = 'Live')

            def add_default_supplier(projectgroup):
                for supplier in survey_default_source_list:
                    try:
                        supplier_cpi = round(projectgroup.project_group_cpi*0.40, 2) if round(projectgroup.project_group_cpi*0.40, 2) < supplier.default_max_cpi else supplier.default_max_cpi

                        supplier_completes = supplier.default_max_completes if supplier.default_max_completes < projectgroup.project_group_completes else projectgroup.project_group_completes

                        ## For Opinions Deal Panel Survey Rewards Add ## 
                        if supplier.supplierOrg.supplier_type == "4":
                            cpi = projectgroup.project_group_cpi
                            if float(cpi) <= 0.5:
                                projectgroup.panel_reward_points = 250
                            elif float(cpi) >= 0.5 and float(cpi) <= 1:
                                projectgroup.panel_reward_points = 500
                            elif float(cpi) > 1 and float(cpi) <= 1.5:
                                projectgroup.panel_reward_points = 750
                            else:
                                projectgroup.panel_reward_points = 1000
                            projectgroup.enable_panel = True
                            projectgroup.save()

                        prj_grp_supp, prj_grp_supp_created = ProjectGroupSupplier.objects.update_or_create(
                            supplier_org_id=supplier.supplierOrg_id,
                            project_group=projectgroup,
                            defaults={
                                'completes':supplier_completes,
                                'clicks':supplier.default_max_clicks,
                                'cpi':supplier_cpi,
                                'supplier_completeurl':supplier.supplierOrg.supplier_completeurl,
                                'supplier_terminateurl':supplier.supplierOrg.supplier_terminateurl,
                                'supplier_quotafullurl':supplier.supplierOrg.supplier_quotafullurl,
                                'supplier_securityterminateurl':supplier.supplierOrg.supplier_securityterminateurl,
                                'supplier_postbackurl':supplier.supplierOrg.supplier_postbackurl,
                                'supplier_internal_terminate_redirect_url' :supplier.supplierOrg.supplier_internal_terminate_redirect_url,
                                'supplier_terminate_no_project_available' :supplier.supplierOrg.supplier_terminate_no_project_available
                                })

                        if prj_grp_supp_created: 
                            prj_grp_supp.supplier_survey_url = projectgroup.project_group_surveyurl + "&source="+str(supplier.supplierOrg_id)+"&PID=XXXXX"
                            prj_grp_supp.save()
                    except:
                        continue

                    if supplier.supplierOrg.supplier_type == "5":
                        for sub_supplier in survey_default_sub_supplier_source_list:
                            try:
                                supplier_cpi = round(projectgroup.project_group_cpi*0.40, 2) if round(projectgroup.project_group_cpi*0.40, 2) < sub_supplier.default_max_cpi else sub_supplier.default_max_cpi
                                supplier_completes = sub_supplier.default_max_completes if sub_supplier.default_max_completes < projectgroup.project_group_completes else projectgroup.project_group_completes

                                project_grp_supplier_obj = ProjectGroupSupplier.objects.get(project_group_id = projectgroup.id, supplier_org__id = supplier.supplierOrg.id,project_group__ad_enable_panel = True)

                                projct_grp_sub_supplier, created = ProjectGroupSubSupplier.objects.update_or_create(
                                    project_group_id = projectgroup.id,
                                    project_group_supplier_id = project_grp_supplier_obj.id,
                                    sub_supplier_org_id = sub_supplier.sub_supplierOrg.id,
                                    defaults={
                                        'completes' : supplier_completes,
                                        'clicks' : sub_supplier.default_max_clicks,
                                        'cpi' : supplier_cpi,
                                        'sub_supplier_completeurl':sub_supplier.sub_supplierOrg.sub_supplier_completeurl,
                                        'sub_supplier_terminateurl':sub_supplier.sub_supplierOrg.sub_supplier_terminateurl,
                                        'sub_supplier_quotafullurl':sub_supplier.sub_supplierOrg.sub_supplier_quotafullurl,
                                        'sub_supplier_securityterminateurl':sub_supplier.sub_supplierOrg.sub_supplier_securityterminateurl,
                                        'sub_supplier_postbackurl':sub_supplier.sub_supplierOrg.sub_supplier_postbackurl,
                                        'sub_supplier_internal_terminate_redirect_url' :sub_supplier.sub_supplierOrg.sub_supplier_internal_terminate_redirect_url,
                                        'sub_supplier_terminate_no_project_available' :sub_supplier.sub_supplierOrg.sub_supplier_terminate_no_project_available
                                    }
                                )

                                if created:
                                    projct_grp_sub_supplier.sub_supplier_survey_url = project_grp_supplier_obj.supplier_survey_url.replace("PID=XXXXX",f"sub_sup={str(sub_supplier.sub_supplierOrg.sub_supplier_code)}&PID=%%PID%%")
                                    projct_grp_sub_supplier.save()
                            except:
                                continue
                    else:
                        continue

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                yield_results = list(executor.map(add_default_supplier, projectgroup_obj_list))
            return Response({"message":"Success"}, status=status.HTTP_200_OK)
        except Exception as error:
            CeleryAPICallLog.objects.create(APIname = f'AddUpdateDefaultSupplier-7======error{error}')
            return Response({"error":"Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)


class ClientSurveyWisePrescreenerQuestionDataView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self,request):
        try:
            survey_no = request.data['survey_no']
            project_group_prescreener_obj_list = ProjectGroupPrescreener.objects.filter(
                project_group_id__project_group_number = survey_no)
            prescreener_serializer = PrescreenerSerializerForClientSupply(project_group_prescreener_obj_list,many=True)
            return Response(prescreener_serializer.data, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)