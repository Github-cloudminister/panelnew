from ClientSupplierAPIIntegration.TolunaClientAPI.models import *
from Prescreener.models import *
from Project.models import *
from Questions.models import *
from SupplierBuyerAPI.models import SupplierBuyerProjectGroup
from SupplierBuyerAPI.serializers import PrescreenerQuestionAnswerSerializers
from affiliaterouter.models import RountingPriority
import concurrent.futures
from django.conf import settings
from django.db.models import F,Count,When,Q,Case
from datetime import datetime,timedelta


def get_country_lang():
    countrylangobj_list = ClientDBCountryLanguageMapping.objects.filter(country_lang_guid__isnull = False).values('lanugage_id_id','country_id_id','toluna_client_language_id','zamplia_client_language_id','client_language_name','client_language_description','country_lang_guid')
    return countrylangobj_list

def client_survey_supplier_live(client_survey_number):
    ProjectGroupSupplier.objects.filter(
        project_group__client_survey_number__in = client_survey_number
    ).exclude(supplier_org__supplier_type__in = ['2']).update(supplier_status = 'Live')
    
    ProjectGroupSubSupplier.objects.filter(
        project_group__client_survey_number__in = client_survey_number).update(sub_supplier_status = 'Live')
    
    return "Success"

def client_survey_pause(action_to_be_performed,customer_url_code,live_survey_numbers,paused_survey_numbers):

    if customer_url_code in ['toluna','zamplia','sago']:

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
        
        return "Success"
    else:
        return "Customer URL code Not Found"

def AddUpdateDefaultSupplier(clientname):
    try:
        survey_default_source_list = CustomerDefaultSupplySources.objects.filter(is_active=True,customerOrg__customer_url_code = clientname,supplierOrg__supplier_status = '1')
        survey_default_sub_supplier_source_list = CustomerDefaultSubSupplierSources.objects.filter(is_active=True,customerOrg__customer_url_code = clientname,sub_supplierOrg__sub_supplier_status = '1')

        projectgroup_obj_list = ProjectGroup.objects.filter(project__project_customer__customer_url_code = clientname,project_group_status = 'Live')

        def add_default_supplier(projectgroup):
            for supplier in survey_default_source_list:
                try:
                    supplier_cpi = round(projectgroup.project_group_cpi*0.80, 2) if round(projectgroup.project_group_cpi*0.80, 2) < supplier.default_max_cpi else supplier.default_max_cpi

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
                    prj_grp_supp.cpi = projectgroup.project_group_cpi
                    prj_grp_supp.save()
                    for sub_supplier in survey_default_sub_supplier_source_list:
                        try:
                            supplier_cpi = round(projectgroup.project_group_cpi*0.80, 2) if round(projectgroup.project_group_cpi*0.80, 2) < sub_supplier.default_max_cpi else sub_supplier.default_max_cpi
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

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            yield_results = list(executor.map(add_default_supplier, projectgroup_obj_list))
        return "Success"
    except:
        return "Something Want Wrong"


def client_survey_of_quotas_lists_celery_pvp(request):
    try:
        if request['client_name'] == 'toluna':
            quotas_list = request['Quotas']
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
                                try:
                                    ques_mapping_obj = TranslatedQuestion.objects.get(
                                        toluna_question_id=que_ans['QuestionID'],apidbcountrylangmapping=apidbcountrylangmapping)
                                    if ques_mapping_obj.parent_question_type in ['CT']:
                                        client_subquota_obj.delete()
                                        break
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
                
                #   Paused survey which does't have any Prescreener
                if ProjectGroupPrescreener.objects.filter(
                    project_group_id = projectgroup_obj,is_enable = True).count() == 0:
                    projectgroup_obj.project_group_status = 'Paused'
                    projectgroup_obj.save()
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                yield_results = list(executor.map(quotas_storing_func, quotas_list))
            
        elif request['client_name'] == 'zamplia':

            def zamplia_quotas_update_create(surveys):

                prescreener_question_dict = {}
                added_question = []
                try:
                    client_quotas = surveys['client_quotas']
                    client_qualifications = surveys['client_qualifications']
                    projectgroup_obj = ProjectGroup.objects.get(client_survey_number = surveys['survey_number'])
                except:
                    return "Something Want Wrong"
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
                            
                            if ques_mapping_obj.parent_question_type == 'ZIP':
                                zipcode_question_available = True
                                allowedZipList = qualification['AnswerCodes']

                            if qualification['QuestionID'] in ['1','5875']:
                                gender_question_available = True

                            if ques_mapping_obj.parent_question_type == 'NU':
                                age_question_available = True
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
                    question_data = TranslatedQuestion.objects.get(
                        parent_question_type = "NU",
                        apidbcountrylangmapping__country_id = projectgroup_obj.project_group_country,
                        apidbcountrylangmapping__lanugage_id = projectgroup_obj.project_group_language
                        )
                    allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                        translated_parent_question = question_data).exclude(toluna_answer_id = '2006351').values_list('id',flat=True))
                    prescreener_question_dict[question_data] = {
                                        "allowedoptions" : allowedoptions_ids,
                                        "allowedRangeMin" : '18,25,30,35,40,45,50,55,60,65',
                                        "allowedRangeMax" : '24,29,34,39,44,49,54,59,64,100',
                                    }
                # if Gender Question not from Zamplia end and we added from our side
                if not gender_question_available:
                    question_data2 = TranslatedQuestion.objects.get(
                        zamplia_question_id__in = ['1','5875'],
                        apidbcountrylangmapping__country_id = projectgroup_obj.project_group_country,
                        apidbcountrylangmapping__lanugage_id = projectgroup_obj.project_group_language
                    )
                    allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                        translated_parent_question = question_data2).values_list('id',flat=True))        
                    prescreener_question_dict[question_data2] = {
                                        "allowedoptions" : allowedoptions_ids,
                                        "allowedRangeMin" : '',
                                        "allowedRangeMax" : '',
                                    }
                # if Zip Code Question not from Zamplia end and we added from our side
                if not zipcode_question_available:
                    question_data3 = TranslatedQuestion.objects.get(
                        parent_question_type = "ZIP",
                        apidbcountrylangmapping__country_id = projectgroup_obj.project_group_country,
                        apidbcountrylangmapping__lanugage_id = projectgroup_obj.project_group_language
                        )
                    allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                        translated_parent_question = question_data3).values_list('id',flat=True))        
                    prescreener_question_dict[question_data3] = {
                                        "allowedoptions" : allowedoptions_ids,
                                        "allowedRangeMin" : '',
                                        "allowedRangeMax" : '',
                                    }
                ProjectGroupPrescreener.objects.filter(project_group_id = projectgroup_obj).update(is_enable = False)
                for question_key, values in prescreener_question_dict.items():
                    ques_answer_obj, created = ProjectGroupPrescreener.objects.update_or_create(
                                    project_group_id = projectgroup_obj,
                                    translated_question_id = question_key,
                                    defaults = {
                                    "allowedRangeMin" : values['allowedRangeMin'],
                                    "allowedRangeMax" : values['allowedRangeMax'],
                                    "is_enable" : True
                                    }
                                )
                    if ques_answer_obj.translated_question_id.parent_question_type == 'ZIP':
                        ques_answer_obj.allowed_zipcode_list = allowedZipList
                    ques_answer_obj.allowedoptions.clear()
                    ques_answer_obj.allowedoptions.add(*values['allowedoptions'])
                    ques_answer_obj.save()

                #   Paused survey which does't have any Prescreener
                if ProjectGroupPrescreener.objects.filter(
                    project_group_id = projectgroup_obj,is_enable = True).count() == 0:
                    projectgroup_obj.project_group_status = 'Paused'
                    projectgroup_obj.save()

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                yield_results = list(executor.map(zamplia_quotas_update_create, request['qualifications']))
        
        elif request['client_name'] == 'sago':

            def sago_quotas_update_create(surveys):
                
                prescreener_question_dict = {}
                added_question = []
                try:
                    client_qualifications = surveys['client_qualifications']
                    projectgroup_obj = ProjectGroup.objects.get(client_survey_number = surveys['survey_number'])
                except:
                    return "Something Want Wrong"
                
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
                        continue             
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

                #   Paused survey which does't have any Prescreener
                if ProjectGroupPrescreener.objects.filter(
                    project_group_id = projectgroup_obj,is_enable = True).count() == 0:
                    projectgroup_obj.project_group_status = 'Paused'
                    projectgroup_obj.save()
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                yield_results = list(executor.map(sago_quotas_update_create, request['qualifications']))
    except:
        return "Something Want Wrong"

def survey_qualify_parameters_check(customer_url_code):
    countrylangobj_list = SurveyQualifyParametersCheck.objects.filter(
        customerOrg__customer_url_code = customer_url_code).values()
    return countrylangobj_list

def client_survey_lists_celery_pvp(request):
    try:
        surveys_list = request['surveys']
        try:
            projectobj = Project.objects.filter(
                project_customer__customer_url_code = request['client_name'],
                project_status = 'Live').order_by('-id').first()
        except:
            return "Something Want Wrong"
        
        projectgroupobjlist = ProjectGroup.objects.filter(project__project_customer__customer_url_code = request['client_name'])
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
                projectgroupobj.project_group_startdate = datetime.now().date()
                projectgroupobj.project_group_enddate = (datetime.today() + timedelta(days=90)).date()
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
                    project_group_startdate = datetime.now().date(),
                    project_group_enddate = (datetime.today() + timedelta(days=90)).date(),
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
        
        with concurrent.futures.ThreadPoolExecutor(max_workers = 10) as executor:
            yield_results = list(executor.map(multithred_survey_create, surveys_list))

        ProjectGroup.objects.bulk_create(bulk_create_surveys)

        ProjectGroup.objects.bulk_update(bulk_update_surveys,['project_group_name','project_group_incidence','project_group_cpi','project_group_completes','project_group_clicks','project_group_status','project_group_startdate','project_group_enddate','project_group_redirectID','ad_enable_panel'])

        projectgroupobjlist.filter(project_group_status = 'Live').update(project_group_number = 1000000 + F('id'),excluded_project_group = [str(1000000 + F('id'))],project = projectobj)
    except:
        return "Something Want Wrong"


def SupplierBuyerProjectGroupCreateView():

    try:
        project_group_number_list = list(ProjectGroup.objects.filter(project_group_status = 'Live').values_list('project_group_number',flat=True))
        def surveybuyer_parellel_surveys_storing_func(survey):
            prescreenerobj = ProjectGroupPrescreener.objects.filter(
                project_group_id__project_group_number = survey,
                is_enable = True,
                translated_question_id__is_active = True
            ).exclude(translated_question_id__parent_question_type = 'CTZIP')
            if len(prescreenerobj) != 0:
                serilizer = PrescreenerQuestionAnswerSerializers(prescreenerobj,many=True)
                try:
                    SupplierBuyerProjectGroup.objects.update_or_create(
                        project_group = prescreenerobj.first().project_group_id,
                        defaults = {'qualification' : serilizer.data}
                    )
                except:
                    pass
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            yield_results = list(executor.map(surveybuyer_parellel_surveys_storing_func, project_group_number_list))
            
        return "Success"
    except:
        return "Something Want Wrong"


def CeleryConversionCalculation():

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
        with concurrent.futures.ThreadPoolExecutor(max_workers = 10) as executor:
            yield_results = list(executor.map(multithred_survey_create, annotated_queryset))
            
        ProjectGroupPriorityStats.objects.bulk_update(bulk_update_surveys,['internal_conversion','visits','completes'])
        ProjectGroupPriorityStats.objects.bulk_create(bulk_created_surveys)
        return "Success"


def SurveyPriorityCelery():
    try:
        projectlist1 = ProjectGroup.objects.annotate(
            prescreener_count =  Count('projectgroupprescreener'),
        ).filter(
            project__project_customer__customer_url_code = 'toluna',
            project_group_status = 'Live',
            prescreener_count = 3
        ).order_by('-project_group_incidence')[0:3]

        projectlist2 = ProjectGroup.objects.annotate(
            prescreener_count =  Count('projectgroupprescreener'),
        ).filter(
            project__project_customer__customer_url_code = 'zamplia',
            project_group_status = 'Live',
            prescreener_count = 3
        ).order_by('-project_group_incidence')[0:3]

        projectlist3 = ProjectGroup.objects.annotate(
            prescreener_count =  Count('projectgroupprescreener'),
        ).filter(
            project__project_customer__customer_url_code = 'sago',
            project_group_status = 'Live',
            prescreener_count = 3
        ).order_by('-project_group_incidence')[0:3]

        projectlist4 = ProjectGroup.objects.annotate(
            prescreener_count =  Count('projectgroupprescreener',filter=(Q(projectgroupprescreener__is_enable = True))),
        ).filter(
            project__project_customer__customer_url_code__in = ['toluna','zamplia','sago'],
            project_group_status = 'Live',
            prescreener_count = 3
        ).exclude(
            project__project_type = '13',
            projectgroupprioritystats__internal_conversion = 0
        ).order_by('-projectgroupprioritystats__internal_conversion')[0:3]
        
        projectlist = projectlist1.union(projectlist2).union(projectlist3).union(projectlist4)

        if len(projectlist) != 0:
            RountingPriority.objects.all().delete()
            for survey in projectlist:
                RountingPriority.objects.update_or_create(
                    project_group = survey
                )
        return "Success"
    except:
        return "Something Want Wrong"