from hashlib import blake2b
from ClientSupplierAPIIntegration.TolunaClientAPI.models import *
from Prescreener.models import ProjectGroupPrescreener
from Project.models import *
from rest_framework.response import Response
from django.conf import settings
from rest_framework import status
from Questions.models import TranslatedAnswer, TranslatedQuestion
from rest_framework.views import APIView
import requests,concurrent.futures, uuid, hashlib, datetime

def fecthSurveysFromTolunaSide():

    # S-1 : Fetch Toluna API Project
    try:
        project_obj = Project.objects.filter(project_customer__customer_url_code='toluna',project_status = 'Live').order_by('-id').first()
        customerOrg_obj = project_obj.project_customer
    except:
        return Response({'message':'Toluna Project Customer Not Available'},status=status.HTTP_400_BAD_REQUEST)
    base_url = settings.TOLUNA_CLIENT_BASE_URL #Base URL for Toluna API Calls
    threat_potential_score = project_obj.project_customer.threat_potential_score

    # S-2 : Fetch Default Supplier which needs to be added into the survey.
    survey_default_source_list = CustomerDefaultSupplySources.objects.only('supplierOrg__id','supplierOrg__supplier_status','supplierOrg__supplier_type','supplierOrg__supplier_terminateurl','supplierOrg__supplier_completeurl','supplierOrg__supplier_quotafullurl','supplierOrg__supplier_securityterminateurl','supplierOrg__supplier_postbackurl','supplierOrg__supplier_routerurl','default_max_cpi','default_max_completes','default_max_clicks','supplierOrg__supplier_internal_terminate_redirect_url','supplierOrg__supplier_terminate_no_project_available').filter(is_active=True,customerOrg=customerOrg_obj,supplierOrg__supplier_status = '1').values('supplierOrg__id','supplierOrg__supplier_status','supplierOrg__supplier_type','supplierOrg__supplier_terminateurl','supplierOrg__supplier_completeurl','supplierOrg__supplier_quotafullurl','supplierOrg__supplier_securityterminateurl','supplierOrg__supplier_postbackurl','supplierOrg__supplier_routerurl','default_max_cpi','default_max_completes','default_max_clicks','supplierOrg__supplier_internal_terminate_redirect_url','supplierOrg__supplier_terminate_no_project_available')

    surveysparams = SurveyQualifyParametersCheck.objects.get(customerOrg__customer_url_code = 'toluna')
    ##*************** Customer Default Sub Supplier ***************sub_supplierOrg__supplier_org_id
    survey_default_sub_supplier_source_list = CustomerDefaultSubSupplierSources.objects.only('sub_supplierOrg__id','sub_supplierOrg__sub_supplier_code','sub_supplierOrg__sub_supplier_status','sub_supplierOrg__supplier_org_id__supplier_type','sub_supplierOrg__supplier_org_id','sub_supplierOrg__sub_supplier_terminateurl','sub_supplierOrg__sub_supplier_completeurl','sub_supplierOrg__sub_supplier_quotafullurl','sub_supplierOrg__sub_supplier_securityterminateurl','sub_supplierOrg__sub_supplier_postbackurl','sub_supplierOrg__sub_supplier_routerurl','default_max_cpi','default_max_completes','default_max_clicks','sub_supplierOrg__sub_supplier_internal_terminate_redirect_url','sub_supplierOrg__sub_supplier_terminate_no_project_available').filter(is_active=True,customerOrg=customerOrg_obj,sub_supplierOrg__sub_supplier_status = '1').values('sub_supplierOrg__id','sub_supplierOrg__sub_supplier_code','sub_supplierOrg__sub_supplier_status','sub_supplierOrg__supplier_org_id__supplier_type','sub_supplierOrg__supplier_org_id','sub_supplierOrg__sub_supplier_terminateurl','sub_supplierOrg__sub_supplier_completeurl','sub_supplierOrg__sub_supplier_quotafullurl','sub_supplierOrg__sub_supplier_securityterminateurl','sub_supplierOrg__sub_supplier_postbackurl','sub_supplierOrg__sub_supplier_routerurl','default_max_cpi','default_max_completes','default_max_clicks','sub_supplierOrg__sub_supplier_internal_terminate_redirect_url','sub_supplierOrg__sub_supplier_terminate_no_project_available')
    
    survey_no_inclusion_list = [] #Newly Fetched Surveys to be added in this list from For loop
    country_lang_guid_list = [] #Quid List
    toluna_survey_list = []
    # S-3: Fetch Country and Language where GUID is available. 
    for country in ClientDBCountryLanguageMapping.objects.exclude(country_lang_guid=None):

        guid = country.country_lang_guid
        country_lang_guid_list.append(guid)

        # S-4: Fetch the Survey for perticular GUID.
        survey_base_url = base_url + f'/IPExternalSamplingService/ExternalSample/{guid}/Quotas?includeRoutables:TRUE'
        response = requests.get(survey_base_url, headers={'API_AUTH_KEY' : settings.TOLUNA_API_AUTH_KEY}, verify=False if settings.SERVER_TYPE != 'production' else True)
        try:
            result = [dict(item, **{'country':country, 'country_guid':guid}) for item in response.json()['Surveys']]
            toluna_survey_list = toluna_survey_list + result
        except:
            continue
        
    def parellel_surveys_storing_func(survey):
        
        # Exclude Surveys who have more than 20 LOI
        if survey['LOI'] > surveysparams.bid_loi_lte or survey['LOI'] < surveysparams.bid_loi_gte:
            return
        if survey['IR'] > surveysparams.bid_incidence_lte or survey['IR'] < surveysparams.bid_incidence_gte:
            return
        if survey['Price']['Amount'] > surveysparams.cpi_lte or survey['Price']['Amount'] < surveysparams.cpi_gte:
            return

        client_survey_id = survey['SurveyID']
        client_quotas = survey['Quotas']

        # APPEND SURVEYS INTO THIS LIST FOR EXCLUDING SURVEYS NOT IN THIS LIST & MARKING THEIR STATUS PENDING FROM LIVE
        survey_no_inclusion_list.append(client_survey_id)

        # ---------------- START: SAVE SURVEY TABLE--------------------------

        # S-5: Create or Update the Surveys fetched from Toluna Side
        try:
            h = blake2b(digest_size=25)
            grp_num = bin(int(client_survey_id))
            h.update(grp_num.encode())
            S_value = h.hexdigest()
            project_group_survey_url = settings.SURVEY_URL+"survey?glsid="+S_value
   
            prjgrp_obj, created = ProjectGroup.objects.update_or_create(
                client_survey_number = client_survey_id,
                project_group_country =  survey['country'].country_id,
                project_group_language =  survey['country'].lanugage_id,
                defaults={
                    'project_group_name':survey['SurveyName'],
                    'project_group_loi':survey['LOI'],
                    'project_group_incidence':survey['IR'],
                    'project_group_cpi':survey['Price']['Amount'],
                    'project_group_completes':survey['CompletesRequired'],
                    'project_group_clicks':1000000,
                    'project':project_obj,
                    'project_group_status':'Live',
                    'threat_potential_score': threat_potential_score,
                    'project_group_startdate': datetime.datetime.now().date(),
                    'project_group_enddate': (datetime.datetime.today() + datetime.timedelta(days=90)).date(),
                    'project_group_redirectID' : project_obj.project_redirectID,
                    'project_group_encodedS_value' : S_value,
                    'project_group_surveyurl':project_group_survey_url,
                    'show_on_DIY' : False,
                    'threat_potential_score' : 90,
                    'project_group_ip_check':False,
                    'project_group_pid_check':False,
                    'ad_enable_panel':True,
                    'project_group_liveurl': 'https://panelviewpoint.com/?RID=%%RID%%',
                    'project_group_testurl': 'https://panelviewpoint.com/?RID=%%RID%%'
                }   
            )
            prjgrp_obj.project_group_number = 1000000 + int(prjgrp_obj.id)
            prjgrp_obj.excluded_project_group = [str(prjgrp_obj.project_group_number)]
            prjgrp_obj.save()
        except:
            return Response({"error":"Survey Already exists..!"}, status=status.HTTP_400_BAD_REQUEST)
        if not created:
                ProjectGroupSupplier.objects.filter(project_group = prjgrp_obj).exclude(supplier_org__supplier_type = '2').update(supplier_status = 'Live')
                ProjectGroupSubSupplier.objects.filter(project_group = prjgrp_obj).update(sub_supplier_status = 'Live')

        # ---------------- END: SAVE SURVEY TABLE----------------------

        # S-6: Update the Quotas for the survey.
        ClientQuota.objects.filter(project_group=prjgrp_obj).delete()
        prescreener_question_dict = {}
        added_question = []
        age_question_available = False
        gender_question_available = False
        zipcode_question_available = False
        for quota in client_quotas:
            client_quota_obj, client_quota_obj_created = ClientQuota.objects.update_or_create(quota_id=quota['QuotaID'], defaults={'completes_required':quota['CompletesRequired'], 'completes_remaining':quota['EstimatedCompletesRemaining'],'project_group':prjgrp_obj, 'quota_json_data':quota})
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
                            ques_mapping_obj = TranslatedQuestion.objects.get(toluna_question_id=que_ans['QuestionID'],apidbcountrylangmapping=survey['country'].id)
                        except:
                            client_subquota_obj.delete() 
                            break
                        ques_ans_obj, ques_ans_obj_created = ClientSurveyPrescreenerQuestions.objects.update_or_create(client_subquota=client_subquota_obj,client_question_mapping=ques_mapping_obj,defaults = {'is_routable':que_ans['IsRoutable'], 'client_name':prjgrp_obj.project.project_customer.customer_url_code})
                        
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
        if not ClientQuota.objects.filter(project_group = prjgrp_obj).exists():
            prjgrp_obj.project_group_status = 'Paused'
            prjgrp_obj.save()
            return
        
        # if Age Question not from toluna end and we added from our side
        if not age_question_available:
            question_data = TranslatedQuestion.objects.get(toluna_question_id = "1001538",apidbcountrylangmapping=survey['country'].id)
            allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                translated_parent_question = question_data).exclude(toluna_answer_id = '2006351').values_list('id',flat=True))
            prescreener_question_dict[question_data] = {
                                "allowedoptions" : allowedoptions_ids,
                                "allowedRangeMin" : '18,25,30,35,40,45,50,55,60,65',
                                "allowedRangeMax" : '24,29,34,39,44,49,54,59,64,100',
                            }
        # if Gender Question not from toluna end and we added from our side
        if not gender_question_available:
            question_data2 = TranslatedQuestion.objects.get(toluna_question_id="1001007",apidbcountrylangmapping=survey['country'].id)
            allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                translated_parent_question = question_data2).values_list('id',flat=True))        
            prescreener_question_dict[question_data2] = {
                                "allowedoptions" : allowedoptions_ids,
                                "allowedRangeMin" : '',
                                "allowedRangeMax" : '',
                            }
        # if Zip Code Question not from toluna end and we added from our side
        if not zipcode_question_available:
            question_data3 = TranslatedQuestion.objects.get(toluna_question_id="1001042",apidbcountrylangmapping=survey['country'].id)
            allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                translated_parent_question = question_data3).values_list('id',flat=True))        
            prescreener_question_dict[question_data3] = {
                                "allowedoptions" : allowedoptions_ids,
                                "allowedRangeMin" : '',
                                "allowedRangeMax" : '',
                            }
        seq = 4
        ProjectGroupPrescreener.objects.filter(project_group_id = prjgrp_obj).update(is_enable = False)
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
                            project_group_id = prjgrp_obj,
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
        ProjectGroupPrescreener.objects.filter(project_group_id = prjgrp_obj,translated_question_id__is_active = False).update(is_enable=False)
    
        
        # S-7: ADD DEFAULT SUPPLIERS TO ALL SURVEYS
        for supplier in survey_default_source_list:
            uuid4_str = uuid.uuid4().hex
            surveyentry_link_code = hashlib.md5((str(client_survey_id) + str(supplier['supplierOrg__id'])).encode() + uuid4_str.encode()).hexdigest()

            supplier_cpi = round(survey['Price']['Amount']*0.40, 2) if round(survey['Price']['Amount']*0.40, 2) < supplier['default_max_cpi'] else supplier['default_max_cpi']
            supplier_completes = supplier['default_max_completes'] if supplier['default_max_completes'] < survey['EstimatedCompletesRemaining'] else survey['EstimatedCompletesRemaining']

            ## For Opinions Deal Panel Survey Rewards Add ## 
            if supplier['supplierOrg__supplier_type'] == "4":
                cpi = survey['Price']['Amount']
                if float(cpi) <= 0.5:
                    prjgrp_obj.panel_reward_points = 250
                elif float(cpi) >= 0.5 and float(cpi) <= 1:
                    prjgrp_obj.panel_reward_points = 500
                elif float(cpi) > 1 and float(cpi) <= 1.5:
                    prjgrp_obj.panel_reward_points = 750
                else:
                    prjgrp_obj.panel_reward_points = 1000
                prjgrp_obj.enable_panel = True
                prjgrp_obj.save()

            prj_grp_supp, prj_grp_supp_created = ProjectGroupSupplier.objects.update_or_create(
                supplier_org_id=supplier['supplierOrg__id'],
                project_group=prjgrp_obj,
                defaults={
                    'completes':supplier_completes,
                    'clicks':supplier['default_max_clicks'],
                    'cpi':supplier_cpi,
                    'supplier_completeurl':supplier['supplierOrg__supplier_completeurl'],
                    'supplier_terminateurl':supplier['supplierOrg__supplier_terminateurl'],
                    'supplier_quotafullurl':supplier['supplierOrg__supplier_quotafullurl'],
                    'supplier_securityterminateurl':supplier['supplierOrg__supplier_securityterminateurl'],
                    'supplier_postbackurl':supplier['supplierOrg__supplier_postbackurl'],
                    'supplier_internal_terminate_redirect_url' :supplier['supplierOrg__supplier_internal_terminate_redirect_url'],
                    'supplier_terminate_no_project_available' :supplier['supplierOrg__supplier_terminate_no_project_available']
                    })

            if prj_grp_supp_created: 
                prj_grp_supp.supplier_survey_url = project_group_survey_url + "&source="+str(supplier['supplierOrg__id'])+"&PID=XXXXX"
                prj_grp_supp.save()
        
        # ADD DEFAULT SUB SUPPLIERS TO ALL SURVEYS
        for sub_supplier in survey_default_sub_supplier_source_list:
            supplier_cpi = round(survey['Price']['Amount']*0.40, 2) if round(survey['Price']['Amount']*0.40, 2) < sub_supplier['default_max_cpi'] else sub_supplier['default_max_cpi']
            supplier_completes = sub_supplier['default_max_completes'] if sub_supplier['default_max_completes'] < survey['EstimatedCompletesRemaining'] else survey['EstimatedCompletesRemaining']

            supplier_org = SupplierOrganisation.objects.get(id = sub_supplier['sub_supplierOrg__supplier_org_id'])

            if supplier_org.supplier_type == "5":

                project_grp_supplier_obj = ProjectGroupSupplier.objects.get(project_group_id = prjgrp_obj.id, supplier_org__id = supplier_org.id,project_group__ad_enable_panel = True)

                projct_grp_sub_supplier, created = ProjectGroupSubSupplier.objects.update_or_create(
                    project_group_id = prjgrp_obj.id,
                    project_group_supplier_id = project_grp_supplier_obj.id,
                    sub_supplier_org_id = sub_supplier['sub_supplierOrg__id'],
                    defaults={
                        'completes' : supplier_completes,
                        'clicks' : sub_supplier['default_max_clicks'],
                        'cpi' : supplier_cpi,
                        'sub_supplier_completeurl':sub_supplier['sub_supplierOrg__sub_supplier_completeurl'],
                        'sub_supplier_terminateurl':sub_supplier['sub_supplierOrg__sub_supplier_terminateurl'],
                        'sub_supplier_quotafullurl':sub_supplier['sub_supplierOrg__sub_supplier_quotafullurl'],
                        'sub_supplier_securityterminateurl':sub_supplier['sub_supplierOrg__sub_supplier_securityterminateurl'],
                        'sub_supplier_postbackurl':sub_supplier['sub_supplierOrg__sub_supplier_postbackurl'],
                        'sub_supplier_internal_terminate_redirect_url' :sub_supplier['sub_supplierOrg__sub_supplier_internal_terminate_redirect_url'],
                        'sub_supplier_terminate_no_project_available' :sub_supplier['sub_supplierOrg__sub_supplier_terminate_no_project_available']
                    }
                )

                if created:
                    projct_grp_sub_supplier.sub_supplier_survey_url = project_grp_supplier_obj.supplier_survey_url.replace("PID=XXXXX",f"sub_sup={str(sub_supplier['sub_supplierOrg__sub_supplier_code'])}&PID=%%PID%%")
                    projct_grp_sub_supplier.save()
            else:
                continue
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        yield_results = list(executor.map(parellel_surveys_storing_func, toluna_survey_list))
    
    # S-8: Pause the survey and suppliers which are not fetched in the list from Toluna End. Make sure to update the status of Toluna Surveys only
    projectgroup_obj = ProjectGroup.objects.filter(project = project_obj, project_group_status = 'Live').exclude(client_survey_number__in=survey_no_inclusion_list)

    project_group_number_list = list(projectgroup_obj.values_list('project_group_number', flat=True))
    projectgroup_obj.update(project_group_status='Paused')

    pgs_obj = ProjectGroupSupplier.objects.filter(project_group__project_group_number__in = project_group_number_list)
    pgs_obj.update(supplier_status = 'Paused')

    # Pause those Survey who Force Paused by Automatic
    ProjectGroup.objects.filter(project_group_number__in = ProjeGroupForceStop.objects.all().values_list('project_group__project_group_number',flat=True)).update(project_group_status='Paused')

    return Response(data={'message':'Surveys have been Successfully Updated.'})


def fecthSurveysFromZampliaSide():
    try:
        project_obj = Project.objects.filter(project_customer__customer_url_code='zamplia',project_status = 'Live').order_by('-id').first()
        customerOrg_obj = project_obj.project_customer
    except:
        return Response(data={'message':'Create New Project with Zamplia Customer URL Code'},status=status.HTTP_400_BAD_REQUEST)
    base_url = settings.STAGING_URL
    zamplia_survey_list = []
    headers = {
        'Accept' : 'application/json',
        'ZAMP-KEY' : settings.STAGING_KEY
    }
    survey_no_inclusion_list = [] #Newly Fetched Surveys to be added in this list from For loop
    response = requests.get(f'{base_url}/Surveys/GetAllocatedSurveys', headers=headers)
    zamplia_survey_list = zamplia_survey_list + response.json()['result']['data']
    threat_potential_score = project_obj.project_customer.threat_potential_score
    surveysparams = SurveyQualifyParametersCheck.objects.get(customerOrg__customer_url_code = 'zamplia')
    survey_default_source_list = CustomerDefaultSupplySources.objects.only('supplierOrg__id','supplierOrg__supplier_status','supplierOrg__supplier_type','supplierOrg__supplier_terminateurl','supplierOrg__supplier_completeurl','supplierOrg__supplier_quotafullurl','supplierOrg__supplier_securityterminateurl','supplierOrg__supplier_postbackurl','supplierOrg__supplier_routerurl','default_max_cpi','default_max_completes','default_max_clicks','supplierOrg__supplier_internal_terminate_redirect_url','supplierOrg__supplier_terminate_no_project_available').filter(customerOrg=customerOrg_obj).values('supplierOrg__id','supplierOrg__supplier_status','supplierOrg__supplier_type','supplierOrg__supplier_terminateurl','supplierOrg__supplier_completeurl','supplierOrg__supplier_quotafullurl','supplierOrg__supplier_securityterminateurl','supplierOrg__supplier_postbackurl','supplierOrg__supplier_routerurl','default_max_cpi','default_max_completes','default_max_clicks','supplierOrg__supplier_internal_terminate_redirect_url','supplierOrg__supplier_terminate_no_project_available')

    ##*************** Customer Default Sub Supplier ***************sub_supplierOrg__supplier_org_id
    survey_default_sub_supplier_source_list = CustomerDefaultSubSupplierSources.objects.only('sub_supplierOrg__id','sub_supplierOrg__sub_supplier_code','sub_supplierOrg__sub_supplier_status','sub_supplierOrg__supplier_org_id__supplier_type','sub_supplierOrg__supplier_org_id','sub_supplierOrg__sub_supplier_terminateurl','sub_supplierOrg__sub_supplier_completeurl','sub_supplierOrg__sub_supplier_quotafullurl','sub_supplierOrg__sub_supplier_securityterminateurl','sub_supplierOrg__sub_supplier_postbackurl','sub_supplierOrg__sub_supplier_routerurl','default_max_cpi','default_max_completes','default_max_clicks','sub_supplierOrg__sub_supplier_internal_terminate_redirect_url','sub_supplierOrg__sub_supplier_terminate_no_project_available').filter(is_active=True,customerOrg=customerOrg_obj).values('sub_supplierOrg__id','sub_supplierOrg__sub_supplier_code','sub_supplierOrg__sub_supplier_status','sub_supplierOrg__supplier_org_id__supplier_type','sub_supplierOrg__supplier_org_id','sub_supplierOrg__sub_supplier_terminateurl','sub_supplierOrg__sub_supplier_completeurl','sub_supplierOrg__sub_supplier_quotafullurl','sub_supplierOrg__sub_supplier_securityterminateurl','sub_supplierOrg__sub_supplier_postbackurl','sub_supplierOrg__sub_supplier_routerurl','default_max_cpi','default_max_completes','default_max_clicks','sub_supplierOrg__sub_supplier_internal_terminate_redirect_url','sub_supplierOrg__sub_supplier_terminate_no_project_available')

    def parellel_surveys_storing_func(survey):
        # We have only mapped US English survey in Zamplia Question mapping
        if survey['LOI'] > surveysparams.bid_loi_lte or survey['LOI'] < surveysparams.bid_loi_gte:
            return
        if survey['IR'] > surveysparams.bid_incidence_lte or survey['IR'] < surveysparams.bid_incidence_gte:
            return
        if float(survey['CPI']) > float(surveysparams.cpi_lte) or float(survey['CPI']) < float(surveysparams.cpi_gte):
            return
        if survey["LanguageId"] != 4:
            return
        
        h = hashlib.blake2b(digest_size=25)
        grp_num = bin(int(survey['SurveyId']))
        h.update(grp_num.encode())
        S_value = h.hexdigest()
        project_group_survey_url = settings.SURVEY_URL+"survey?glsid="+S_value
        countrylang = ClientDBCountryLanguageMapping.objects.get(zamplia_client_language_id=str(survey['LanguageId']))
        
        prjgrp_obj, created = ProjectGroup.objects.update_or_create(
            client_survey_number = survey['SurveyId'],
            project_group_country_id =  countrylang.country_id.id,
            project_group_language_id =  countrylang.lanugage_id.id,
            defaults={
                'project_group_name':survey['Name'],
                'project_group_loi':survey['LOI'],
                'project_group_incidence':survey['IR'],
                'project_group_cpi':survey['CPI'],
                'project_group_completes':survey['TotalCompleteRequired'],
                'project_group_clicks':1000000,
                'project':project_obj,
                'project_group_status':'Live',
                'threat_potential_score': threat_potential_score,
                'project_group_startdate': datetime.datetime.now().date(),
                'project_group_enddate': (datetime.datetime.today() + datetime.timedelta(days=90)).date(),
                'project_group_redirectID' : project_obj.project_redirectID,
                'project_group_encodedS_value' : S_value,
                'project_group_surveyurl':project_group_survey_url,
                'show_on_DIY' : False,
                'threat_potential_score' : 90,
                'ad_enable_panel':True,
                'project_group_liveurl': 'https://panelviewpoint.com/?RID=%%RID%%',
                'project_group_testurl': 'https://panelviewpoint.com/?RID=%%RID%%'
                }     
            )
        prjgrp_obj.project_group_number = 1000000 + int(prjgrp_obj.id)
        prjgrp_obj.excluded_project_group = [str(prjgrp_obj.project_group_number)]
        prjgrp_obj.save()
        if not created:
            ProjectGroupSupplier.objects.filter(project_group = prjgrp_obj).exclude(supplier_org__supplier_type = '2').update(supplier_status = 'Live')
            ProjectGroupSubSupplier.objects.filter(project_group = prjgrp_obj).update(sub_supplier_status = 'Live')
        survey_no_inclusion_list.append(survey['SurveyId'])
        prescreener_question_dict = {}
        added_question = []
        client_quotas = (requests.get(f'{base_url}/Surveys/GetSurveyQuotas?SurveyId={survey["SurveyId"]}', headers=headers)).json()['result']['data']
        client_qualifications = (requests.get(f'{base_url}/Surveys/GetSurveyQualifications?SurveyId={survey["SurveyId"]}', headers=headers)).json()['result']['data']
        for quota in client_quotas:
            client_quota_obj, created = ClientQuota.objects.update_or_create(
            quota_id=quota['QuotaId'],
            defaults={
                'project_group': prjgrp_obj,
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
                            'client_name':prjgrp_obj.project.project_customer.customer_url_code,
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
                    prjgrp_obj.custom_question = True
                    prjgrp_obj.save()
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
                    prjgrp_obj.custom_question = True
                    prjgrp_obj.save()
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
        ProjectGroupPrescreener.objects.filter(project_group_id = prjgrp_obj).update(is_enable = False)
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

        #   Disable old prescreener added in survey
        ProjectGroupPrescreener.objects.filter(project_group_id = prjgrp_obj,translated_question_id__is_active = False).update(is_enable=False)
        
        for supplier in survey_default_source_list:
            uuid4_str = uuid.uuid4().hex
            surveyentry_link_code = hashlib.md5((str(survey['SurveyId']) + str(supplier['supplierOrg__id'])).encode() + uuid4_str.encode()).hexdigest()

            supplier_cpi = round(float(survey['CPI'])*0.40, 2) if round(float(survey['CPI'])*0.40, 2) < supplier['default_max_cpi'] else supplier['default_max_cpi']
            supplier_completes = supplier['default_max_completes'] if supplier['default_max_completes'] < survey['TotalCompleteRequired'] else survey['TotalCompleteRequired']

            ## For Opinions Deal Panel Survey Rewards Add ##
            if supplier['supplierOrg__supplier_type'] == "4": 
                cpi = survey['CPI']
                if float(cpi) <= 0.5:
                    prjgrp_obj.panel_reward_points = 250
                elif float(cpi) >= 0.5 and float(cpi) <= 1:
                    prjgrp_obj.panel_reward_points = 500
                elif float(cpi) > 1 and float(cpi) <= 1.5:
                    prjgrp_obj.panel_reward_points = 750
                else:
                    prjgrp_obj.panel_reward_points = 1000
                prjgrp_obj.enable_panel = True
                prjgrp_obj.save()

            prj_grp_supp, prj_grp_supp_created = ProjectGroupSupplier.objects.update_or_create(
                supplier_org_id=supplier['supplierOrg__id'],
                project_group=prjgrp_obj,
                defaults={
                    'completes':supplier_completes,
                    'clicks':supplier['default_max_clicks'],
                    'cpi':supplier_cpi,
                    'supplier_completeurl':supplier['supplierOrg__supplier_completeurl'],
                    'supplier_terminateurl':supplier['supplierOrg__supplier_terminateurl'],
                    'supplier_quotafullurl':supplier['supplierOrg__supplier_quotafullurl'],
                    'supplier_securityterminateurl':supplier['supplierOrg__supplier_securityterminateurl'],
                    'supplier_postbackurl':supplier['supplierOrg__supplier_postbackurl'],
                    'supplier_internal_terminate_redirect_url' :supplier['supplierOrg__supplier_internal_terminate_redirect_url'],
                    'supplier_terminate_no_project_available' :supplier['supplierOrg__supplier_terminate_no_project_available']
                    })

            if prj_grp_supp_created: 
                prj_grp_supp.supplier_survey_url = project_group_survey_url + "&source="+str(supplier['supplierOrg__id'])+"&PID=XXXXX"
                prj_grp_supp.save()


        # ADD DEFAULT SUB SUPPLIERS TO ALL SURVEYS
        for sub_supplier in survey_default_sub_supplier_source_list:

            supplier_cpi = round(float(survey['CPI'])*0.40, 2) if round(float(survey['CPI'])*0.40, 2) < sub_supplier['default_max_cpi'] else sub_supplier['default_max_cpi']
            supplier_completes = sub_supplier['default_max_completes'] if sub_supplier['default_max_completes'] < survey['TotalCompleteRequired'] else survey['TotalCompleteRequired']

            supplier_org = SupplierOrganisation.objects.get(id = sub_supplier['sub_supplierOrg__supplier_org_id'])

            if supplier_org.supplier_type == "5":
                project_grp_supplier_obj = ProjectGroupSupplier.objects.get(project_group_id = prjgrp_obj.id, supplier_org__id = supplier_org.id,project_group__ad_enable_panel = True)

                projct_grp_sub_supplier, created = ProjectGroupSubSupplier.objects.update_or_create(
                    project_group_id = prjgrp_obj.id,
                    project_group_supplier_id = project_grp_supplier_obj.id,
                    sub_supplier_org_id = sub_supplier['sub_supplierOrg__id'],
                    defaults={
                        'completes' : supplier_completes,
                        'clicks' : sub_supplier['default_max_clicks'],
                        'cpi' : supplier_cpi,
                        'sub_supplier_completeurl':sub_supplier['sub_supplierOrg__sub_supplier_completeurl'],
                        'sub_supplier_terminateurl':sub_supplier['sub_supplierOrg__sub_supplier_terminateurl'],
                        'sub_supplier_quotafullurl':sub_supplier['sub_supplierOrg__sub_supplier_quotafullurl'],
                        'sub_supplier_securityterminateurl':sub_supplier['sub_supplierOrg__sub_supplier_securityterminateurl'],
                        'sub_supplier_postbackurl':sub_supplier['sub_supplierOrg__sub_supplier_postbackurl'],
                        'sub_supplier_internal_terminate_redirect_url' :sub_supplier['sub_supplierOrg__sub_supplier_internal_terminate_redirect_url'],
                        'sub_supplier_terminate_no_project_available' :sub_supplier['sub_supplierOrg__sub_supplier_terminate_no_project_available']
                    }
                )

                if created:
                    projct_grp_sub_supplier.sub_supplier_survey_url = project_grp_supplier_obj.supplier_survey_url.replace("PID=XXXXX",f"sub_sup={str(sub_supplier['sub_supplierOrg__sub_supplier_code'])}&PID=%%PID%%")
                    projct_grp_sub_supplier.save()
            else:
                continue
            
            ## ./ADD DEFAULT SUB SUPPLIERS TO ALL SURVEYS

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        yield_results = list(executor.map(parellel_surveys_storing_func, zamplia_survey_list))
    
    projectgroup_obj = ProjectGroup.objects.filter(project = project_obj, project_group_status = 'Live').exclude(
        client_survey_number__in=survey_no_inclusion_list)
    project_group_number_list = list(projectgroup_obj.values_list('project_group_number', flat=True))
    projectgroup_obj.update(project_group_status='Paused')

    pgs_obj = ProjectGroupSupplier.objects.filter(project_group__project_group_number__in = project_group_number_list)
    pgs_obj.update(supplier_status = 'Paused')
    return Response(data={'message':'New Surveys have been added.'})

class FecthSurveysFromTolunaSideAPI(APIView):
    
    def get(self, request):
        if settings.SERVER_TYPE == 'localhost':
            return fecthSurveysFromTolunaSide()
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

class FecthSurveysFromZampliaSideAPI(APIView):
    
    def get(self, request):
        if settings.SERVER_TYPE == 'localhost':
            return fecthSurveysFromZampliaSide()
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)