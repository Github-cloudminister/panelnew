from Prescreener.models import ProjectGroupPrescreener
from SupplierAPI.serializers import PrescreenerQuestionsAnswerLucidListSerializer
from Surveyentry.models import RespondentDetail
from Surveyentry.custom_function import get_object_or_none
from SupplierAPI.models import LucidCountryLanguageMapping
import requests, json


lucid_survey_status = {
    "Cancel": "05",  # Cancel
    "Booked": "01",  # Bid
    "Live": "03",  # Live
    "Paused": "02",  # Paused
    "Closed": "04",  # Closed
    "Reconciled": "13",  # Reconciled
    "ReadyForInvoice": "09",  # Invoiced
    "ReadyForInvoiceApproved": "09",  # Invoiced
    "Invoiced": "09",  # Invoiced
    "Archived": "11",  # Archived
}

lucid_study_type = {
    '1': 1, # Adhoc
    '2': 13, # Tracker
    '3': 5, # IHUT
    '4': 8, # Community Recruit
    '5': 11, # Panel Sourcing
    '6': 17, # Qual
    '7': 21, # IR Check
    '8': 1, # Other
    '9': 2, # Diary
    '10': 22, # Recontact
    '11': 16, # Wave Study
}

lucid_industries = {
    '1': 1, # Automotive
    '2': 2, # Beauty/Cosmetics
    '3': 3, # Beverages - Alcoholic
    '4': 4, # Beverages - Non Alcoholic
    '5': 5, # Education
    '6': 6, # Electronics/Computer/Software
    '7': 7, # Entertainment (Movies, Music, TV, Etc)
    '8': 8, # Fashion/Clothing
    '9': 9, # Financial Services/Insurance
    '10': 10, # Food/Snacks
    '11': 11, # Gambling/Lottery
    '12': 12, # Healthcare/Pharmaceuticals
    '13': 13, # Home (Utilities/Appliances, ...)
    '14': 14, # Home Entertainment (DVD,VHS)
    '15': 15, # Home Improvement/Real Estate/Construction
    '16': 16, # IT (Servers,Databases, Etc)
    '17': 17, # Personal Care/Toiletries
    '18': 18, # Pets
    '19': 19, # Politics
    '20': 20, # Publishing (Newspaper, Magazines, Books)
    '21': 21, # Restaurants
    '22': 22, # Sports/Outdoor
    '23': 23, # Telecommunications (Phone, Cell Phone, Cable)
    '24': 24, # Tobacco (Smokers)
    '25': 25, # Toys
    '26': 26, # Transportation/Shipping
    '27': 27, # Travel
    '29': 29, # Websites/Internet/E-Commerce
    '30': 30, # other
    '31': 31, # Sensitive Content
    '32': 32, # Explicit Content
    '28': 28, # Gaming
    '33': 30, # HRDM
    '34': 30, # Job/Career
    '35': 30, # Shopping
    '36': 30, # Parenting
    '37': 30, # Religion
    '38': 30, # ITDM
    '39': 30, # Marketing/Advertising
    '40': 30, # Other - B2B
    '41': 30, # Ailment
    '42': 30, # Social Media
    '43': 30, # SBOs (Small Business Owners)
    '44': 30, # Engineering
    '45': 30, # Manufacturing
    '46': 30, # Retail
    '47': 30, # Opinion Elites
    '48': 30, # Retail
}

lucid_sample_type = {
    '1': 101, # B2B
    '2': 100, # Consumer
    '3': 103, # Healthcare
    '4': 100, # Other
}

def get_survey_details(prjgrp_supplier_obj, survey_status=None):
    if survey_status == None:
        survey_status = lucid_survey_status[prjgrp_supplier_obj.supplier_status]
    else:
        survey_status = lucid_survey_status[survey_status]

    country_lang_id = get_object_or_none(LucidCountryLanguageMapping, country_id=prjgrp_supplier_obj.project_group.project_group_country, lanugage_id = prjgrp_supplier_obj.project_group.project_group_language)

    if country_lang_id != None:
        country_lang_id = country_lang_id.lucid_country_lang_id

    project_group_security_check =  prjgrp_supplier_obj.project_group.project_group_security_check
    if project_group_security_check:
        project_group_ip_check = prjgrp_supplier_obj.project_group.project_group_ip_check
        project_group_pid_check = prjgrp_supplier_obj.project_group.project_group_pid_check
    else:
        project_group_ip_check = False
        project_group_pid_check = False

    dict_payload = {
        'SurveyName':f"{prjgrp_supplier_obj.project_group.project_group_number}-{prjgrp_supplier_obj.project_group.project_group_name}", 
        'AccountID': prjgrp_supplier_obj.id, 
        'SurveyStatusCode': survey_status, 
        'CountryLanguageID': country_lang_id, 
        'ClientSurveyLiveURL': f"{prjgrp_supplier_obj.supplier_survey_url}&PID=[%RID%]", 
        'TestRedirectURL': f"{prjgrp_supplier_obj.supplier_survey_url}&PID=[%RID%]&isTest=1", 
        'SurveyPriority':1, 
        'SurveyNumber':prjgrp_supplier_obj.lucidSupplier_survey_id, 
        'IndustryID': lucid_industries[prjgrp_supplier_obj.project_group.project.project_category], 
        'StudyTypeID': lucid_study_type[prjgrp_supplier_obj.project_group.project.project_type], 
        'ClientCPI': prjgrp_supplier_obj.cpi, 
        'QuotaCPI': prjgrp_supplier_obj.cpi, 
        'IsActive':True, 
        'Quota': prjgrp_supplier_obj.completes, 
        "FulcrumExchangeAllocation": 0,
        "FulcrumExchangeHedgeAccess": True, 
        "IsVerifyCallBack": False,
        "UniquePID": project_group_pid_check,
        "UniqueIPAddress": project_group_ip_check,
        "IsRelevantID": True,
        "IsDedupe": True,
        "IsGeoIP": True,
        "IsFraudProfile": False,
        "FraudProfileThreshold": 0,
        "IsTrueSample": False,
        "QuotaCalculationTypeID": 2, # Either 1 for ”Completes” (quotas determined by completes) or 2=”Prescreens” (quotas determined when leaving Lucid Marketplace).
        "SurveyPlatformID": 1, # This should be hardcoded to 1 which represents “none”.
        "BidLengthOfInterview": prjgrp_supplier_obj.project_group.project_group_loi,
        "BusinessUnitID": 2210,
        "SampleTypeID": lucid_sample_type[prjgrp_supplier_obj.project_group.project_audience_type],
        "BidIncidence": prjgrp_supplier_obj.project_group.project_group_incidence,
        "CollectsPII": False
    }
    
    return dict_payload

def get_survey_qualifications(SurveyNumber):
    qulifications = ProjectGroupPrescreener.objects.filter(
        project_group_id__project_group_number = SurveyNumber,
        is_enable=True,translated_question_id__is_active = True).exclude(
            translated_question_id__lucid_question_id__exact = ''
        )
    serializer = PrescreenerQuestionsAnswerLucidListSerializer(qulifications,many=True)
    return serializer.data

def create_lucid_survey(prjgrp_supplier_obj):
    survey_create_base_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+'/Demand/v1/Surveys/Create'
    survey_update_base_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+'/Demand/v1/Surveys/Update/'
    survey_Qualification_create_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+'/Demand/v1/SurveyQualifications/Create/'

    headers = {'Content-type': 'application/json', 'Authorization' : prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.api_key}

    request_body = get_survey_details(prjgrp_supplier_obj)
    if request_body['CountryLanguageID'] == '9':
        try:
            request_body['CountryLanguageID'] = '7'
            response = requests.post(survey_create_base_url, json=request_body, headers=headers)
            request_body['CountryLanguageID'] = '9'
            request_body['SurveyNumber'] = str(response.json()['Survey']['SurveyNumber'])
            response = requests.put(survey_update_base_url + str(response.json()['Survey']['SurveyNumber']), json=request_body, headers=headers)
        except:
            return response
    else:
        response = requests.post(survey_create_base_url, json=request_body, headers=headers)
    SurveyNumber = str(response.json()['Survey']['SurveyNumber'])
    if response.status_code in [200,201]:
        try:
            request_body = get_survey_qualifications(prjgrp_supplier_obj.project_group.project_group_number)
            order = 1
            for question in request_body:
                PreCodes = list(filter(None, question['AnswerOptions']))
                if question['lucidquestion'] == '42':
                    try:
                        PreCodes = []
                        allowedRangeMin = question['allowedRangeMin'].split(',')
                        allowedRangeMax = question['allowedRangeMax'].split(',')
                        for min, max in zip(allowedRangeMin, allowedRangeMax):
                            abc = list(range(int(min),int(max)+1))
                            PreCodes.extend(abc)
                    except:
                        PreCodes = [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99]
                params = {
                    "Name": "STANDARD_RELATIONSHIP",
                    "QuestionID": question['lucidquestion'],
                    "LogicalOperator": "OR",
                    "NumberOfRequiredConditions": 1,
                    "IsActive": True,
                    "PreCodes": PreCodes,
                    "Order": order,
                    "MaxPunch": -1
                }
                requests.post(survey_Qualification_create_url + SurveyNumber, json=params, headers=headers)
                order = order + 1
        except:
            return response
    return response

def update_lucid_survey(prjgrp_supplier_obj, survey_status=None):
    survey_base_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+f'/Demand/v1/Surveys/Update/{prjgrp_supplier_obj.lucidSupplier_survey_id}'

    headers = {'Content-type': 'application/json', 'Authorization' : prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.api_key}

    request_body = get_survey_details(prjgrp_supplier_obj, survey_status=survey_status)

    response = requests.put(survey_base_url, json=request_body, headers=headers)

    return response

def create_lucid_survey_Qualifications(prjgrp_supplier_obj,serializer):
    headers = {'Authorization' : prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.api_key}
    survey_create_base_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+f'/Demand/v1/SurveyQualifications/Create/{prjgrp_supplier_obj.lucidSupplier_survey_id}'
    survey_update_base_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+f'/Demand/v1/SurveyQualifications/Update/{prjgrp_supplier_obj.lucidSupplier_survey_id}'
    projectgrouppre = ProjectGroupPrescreener.objects.get(id=serializer.data['id'])
    PreCodes = list(projectgrouppre.allowedoptions.values_list('lucid_answer_id',flat=True))
    params = {
        "Name": "STANDARD_RELATIONSHIP",
        "QuestionID": projectgrouppre.translated_question_id.lucid_question_id,
        "LogicalOperator": "OR",
        "NumberOfRequiredConditions": 1,
        "IsActive": True,
        "PreCodes": list(filter(None, PreCodes)),
        "MaxPunch": -1
    }
    response = requests.post(survey_create_base_url,json=params, headers=headers)
    
    if response.status_code not in [200,201]:
        response = requests.put(survey_update_base_url,json=params, headers=headers)
    return response

def update_lucid_survey_Qualifications(prjgrp_supplier_obj,prescreenerquestionid):
    headers = {'Authorization' : prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.api_key}
    survey_update_base_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+f'/Demand/v1/SurveyQualifications/Update/{prjgrp_supplier_obj.lucidSupplier_survey_id}'
    projectgrouppre = ProjectGroupPrescreener.objects.get(id=prescreenerquestionid)
    if projectgrouppre.translated_question_id.lucid_question_id == '42':
        try:
            PreCodes = []
            allowedRangeMin = projectgrouppre.allowedRangeMin.split(',')
            allowedRangeMax = projectgrouppre.allowedRangeMax.split(',')
            for min, max in zip(allowedRangeMin, allowedRangeMax):
                abc = list(range(int(min),int(max)+1))
                PreCodes.extend(abc)
        except:
            PreCodes = [18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99]
    elif projectgrouppre.translated_question_id.lucid_question_id == '45':
        PreCodes = list(projectgrouppre.allowed_zipcode_list)
    else:
        PreCodes = list(projectgrouppre.allowedoptions.values_list('lucid_answer_id',flat=True))
                
    params = {
        "Name": "STANDARD_RELATIONSHIP",
        "QuestionID": projectgrouppre.translated_question_id.lucid_question_id,
        "LogicalOperator": "OR",
        "NumberOfRequiredConditions": 1,
        "IsActive": True,
        "PreCodes": list(filter(None, PreCodes)),
        "MaxPunch": -1
    }
    response = requests.put(survey_update_base_url,json=params, headers=headers)
    return response

def retrieve_lucid_survey(prjgrp_supplier_obj):
    survey_base_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+f'/Demand/v1/Surveys/BySurveyNumber/{prjgrp_supplier_obj.lucidSupplier_survey_id}'

    headers = {'Authorization' : prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.api_key}

    response = requests.get(survey_base_url, headers=headers)

    return response

def list_lucid_surveys(prjgrp_supplier_obj):
    survey_base_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+'/Demand/v1/Surveys/BySurveyStatus/01'

    headers = {'Authorization' : prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.api_key}

    response = requests.get(survey_base_url, headers=headers)

    return response

def reconcile_lucid_survey(prjgrp_supplier_obj):
    survey_base_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+f'/Demand/v1/Surveys/Reconcile/{prjgrp_supplier_obj.lucidSupplier_survey_id}'

    headers = {'Content-type': 'application/json', 'Authorization' : prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.api_key}

    body = {'ResponseIDs': [item.respondenturldetail.RID for item in RespondentDetail.objects.filter(respondentdetailsrelationalfield__project_group_supplier__id=prjgrp_supplier_obj.id, resp_status='4')]}

    request_body = json.dumps(body)

    response = requests.post(survey_base_url, json=request_body, headers=headers)

    if response.status_code in [200, 201]:
        update_lucid_survey(prjgrp_supplier_obj, survey_status="Reconciled")
    return response