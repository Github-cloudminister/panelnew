from AutomationAPI.serializers import ProjectGroupSerializer
from Project.panel_view import panel_survey_questions_create_update
from celery import shared_task
from django.conf import settings
import requests, concurrent, hashlib, requests, concurrent.futures,uuid
from rest_framework.decorators import api_view
from AutomationAPI.common import *
from AutomationAPI.models import *
from Logapp.models import *
from django.conf import settings
from Supplier_Final_Ids_Email.models import SupplierIdsMarks, supplierFinalIdsDeploy
from django.template.loader import render_to_string
from Surveyentry.models import RespondentDetail
from automated_email_notifications.email_configurations import sendEmailSendgripAPIIntegration
from django.db.models import Sum, FloatField
from django.db.models.functions import Coalesce,Round,Cast
from django.http import JsonResponse
from django.db import close_old_connections


TOLUNA_CLIENT_BASE_URL = settings.TOLUNA_CLIENT_BASE_URL
ZAMPLIA_CLIENT_BASE_URL = settings.STAGING_URL
SAGO_BASEURL = settings.SAGO_BASEURL

zampliaheaders = {'Accept' : 'application/json','ZAMP-KEY' : settings.STAGING_KEY}
tolunaheaders = {'API_AUTH_KEY' : settings.TOLUNA_API_AUTH_KEY}
sagoheader = {"X-MC-SUPPLY-KEY":settings.SAGO_X_MC_SUPPLY_KEY}


def surveys_map_create_update(surveys_dict):

    surveyparams = survey_qualify_parameters_check('toluna')[0]
    survey_list = surveys_dict['survey_list']
    final_surveys = []
    toluna_survey_number = []
    total_quotas_list = []

    try:
        def map_toluna_surveys(survey):

            if int(survey['LOI']) > int(surveyparams['bid_loi_lte']) or int(survey['LOI']) < int(surveyparams['bid_loi_gte']):
                return
            if int(survey['IR']) > int(surveyparams['bid_incidence_lte']) or int(survey['IR']) < int(surveyparams['bid_incidence_gte']):
                return
            if float(survey['Price']['Amount']) > float(surveyparams['cpi_lte']) or float(survey['Price']['Amount']) < float(surveyparams['cpi_gte']):
                return
            
            h = hashlib.blake2b(digest_size=25)
            grp_num = bin(int(survey['SurveyID']))
            h.update(grp_num.encode())
            S_value = h.hexdigest()
            quotas = survey['Quotas']
            survey.pop('Quotas')

            final_surveys.append({
                'project_group_country_id' : surveys_dict['country_id'],
                'project_group_language_id' : surveys_dict['lanugage_id'],
                'client_survey_number' : str(survey['SurveyID']),
                'project_group_name' : survey['SurveyName'],
                'project_group_loi' : survey['LOI'],
                'project_group_incidence' : survey['IR'],
                'project_group_cpi' : survey['Price']['Amount'],
                'project_group_completes' : survey['CompletesRequired'],
                'project_group_clicks' : 1000000,
                'project_group_status' : 'Live',
                'project_group_encodedS_value' : S_value,
                'project_group_encodedR_value' : surveys_dict['country_lang_guid'],
                'show_on_DIY' : False,
                'project_group_ip_check' : False,
                'project_group_pid_check' : False,
                'ad_enable_panel' : True,
                'project_group_liveurl' : 'https://panelviewpoint.com/?RID=%%RID%%',
                'project_group_testurl' : 'https://panelviewpoint.com/?RID=%%RID%%'

            })

            toluna_survey_number.append(str(survey['SurveyID']))
            total_quotas_list.append({survey['SurveyID']:quotas})

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            yield_results = list(executor.map(map_toluna_surveys, survey_list))

    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'toluna',line_number = '73',error_details = error,inputdata = survey_list)
        return JsonResponse({"message": "Something Want Wrong"})
    
    try:
    
        surveys_break_list = [final_surveys[0:100],final_surveys[100:200],final_surveys[200:300],final_surveys[300:400],final_surveys[400:500],final_surveys[500:600],final_surveys[600:700],final_surveys[700:800],final_surveys[800:900],final_surveys[900:1000],final_surveys[1000:1100],final_surveys[1100:1200],final_surveys[1200:1300],final_surveys[1300:1400],final_surveys[1400:1500],final_surveys[1500:1600],final_surveys[1600:1700],final_surveys[1700:1800],final_surveys[1800:1900],final_surveys[1900:2000],final_surveys[2000:2100],final_surveys[2100:2200],final_surveys[2200:2300],final_surveys[2300:2400],final_surveys[2400:2500],final_surveys[2500:2600],final_surveys[2600:2700],final_surveys[2700:2800],final_surveys[2800:2900],final_surveys[2900:3000],final_surveys[3000:3100],final_surveys[3100:3200],final_surveys[3200:3300],final_surveys[3300:3400],final_surveys[3400:3500],final_surveys[3500:3600],final_surveys[3600:3700],final_surveys[3700:3800],final_surveys[3800:3900],final_surveys[3900:4000],final_surveys[4000:4100],final_surveys[4100:4200],final_surveys[4200:4300],final_surveys[4300:4400],final_surveys[4400:4500],final_surveys[4500:4600],final_surveys[4600:4700],final_surveys[4700:4800],final_surveys[4800:4900],final_surveys[4900:]]

        def post_toluna_surveys(surveys):
                    
            if len(surveys) != 0:
                client_survey_lists_celery_pvp({"surveys":surveys,'client_name' : 'toluna'})
                
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            yield_results = list(executor.map(post_toluna_surveys, surveys_break_list))

        return total_quotas_list,toluna_survey_number
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'toluna',line_number = '90',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})

def get_toluna_surveys():
    
    countrylist = get_country_lang()

    surveys_list = []
    try:
        for countrydata in countrylist:

            response = requests.get(f'{TOLUNA_CLIENT_BASE_URL}/IPExternalSamplingService/ExternalSample/{countrydata["country_lang_guid"]}/Quotas?includeRoutables:TRUE',headers=tolunaheaders, verify= True).json()
            if 'Surveys' not in response:
                return
            else:
                surveys_list.append({'lanugage_id': countrydata['lanugage_id_id'],'country_id': countrydata['country_id_id'], 'country_lang_guid':countrydata["country_lang_guid"], 'survey_list':response['Surveys']})
                ClientSupplierFetchSurveysLog.objects.create(client_name = 'toluna',total_surveys_fetch = len(response['Surveys']))
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'toluna',line_number = '108',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})

    total_toluna_survey_number = []
    final_total_quotas_list = []
    try:
        def country_wise_survey_create(surveys_dict):
            total_quotas_list,toluna_survey_number = surveys_map_create_update(surveys_dict)
            total_toluna_survey_number.extend(toluna_survey_number)
            final_total_quotas_list.extend(total_quotas_list)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            yield_results = list(executor.map(country_wise_survey_create, surveys_list))
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'toluna',line_number = '121',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})

    client_survey_supplier_live(total_toluna_survey_number)

    if len(total_toluna_survey_number) > 30:
        client_survey_pause('survey_live','toluna',total_toluna_survey_number,None)

    try:
        quotas_break_list = [final_total_quotas_list[0:100],final_total_quotas_list[100:200],final_total_quotas_list[200:300],final_total_quotas_list[300:400],final_total_quotas_list[400:500],final_total_quotas_list[500:600],final_total_quotas_list[600:700],final_total_quotas_list[700:800],final_total_quotas_list[800:900],final_total_quotas_list[900:1000],final_total_quotas_list[1000:1100],final_total_quotas_list[1100:1200],final_total_quotas_list[1200:1300],final_total_quotas_list[1300:1400],final_total_quotas_list[1400:1500],final_total_quotas_list[1500:1600],final_total_quotas_list[1600:1700],final_total_quotas_list[1700:1800],final_total_quotas_list[1800:1900],final_total_quotas_list[1900:2000],final_total_quotas_list[2000:2100],final_total_quotas_list[2100:2200],final_total_quotas_list[2200:2300],final_total_quotas_list[2300:2400],final_total_quotas_list[2400:2500],final_total_quotas_list[2500:2600],final_total_quotas_list[2600:2700],final_total_quotas_list[2700:2800],final_total_quotas_list[2800:2900],final_total_quotas_list[2900:3000],final_total_quotas_list[3000:3100],final_total_quotas_list[3100:3200],final_total_quotas_list[3200:3300],final_total_quotas_list[3300:3400],final_total_quotas_list[3400:3500],final_total_quotas_list[3500:3600],final_total_quotas_list[3600:3700],final_total_quotas_list[3700:3800],final_total_quotas_list[3800:3900],final_total_quotas_list[3900:4000],final_total_quotas_list[4000:4100],final_total_quotas_list[4100:4200],final_total_quotas_list[4200:4300],final_total_quotas_list[4300:4400],final_total_quotas_list[4400:4500],final_total_quotas_list[4500:4600],final_total_quotas_list[4600:4700],final_total_quotas_list[4700:4800],final_total_quotas_list[4800:4900],final_total_quotas_list[4900:]]

        def post_toluna_quotas(surveys):
            if len(surveys) != 0:
                client_survey_of_quotas_lists_celery_pvp({"Quotas":surveys,'client_name' : 'toluna'})
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            yield_results = list(executor.map(post_toluna_quotas, quotas_break_list))
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'toluna',line_number = '137',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})

def get_zamplia_surveys():
    try:
        response = requests.get(f'{ZAMPLIA_CLIENT_BASE_URL}/Surveys/GetAllocatedSurveys', headers=zampliaheaders)
        ClientSupplierFetchSurveysLog.objects.create(client_name = 'zamplia',total_surveys_fetch = len(response.json()['result']['data']))
        
        surveyparams = SurveyQualifyParametersCheck.objects.get(customerOrg__customer_url_code = 'zamplia')
        clientdbcountrylang_valueslist = list(surveyparams.client_country_languages.values_list('zamplia_client_language_id',flat=True))
        clientdbcountrylang_values = surveyparams.client_country_languages.values('zamplia_client_language_id','lanugage_id_id','country_id_id')
        
        if 'result' not in response.json() or 'data' not in response.json()['result'] or len(response.json()['result']['data']) == 0:
            return
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'zamplia',line_number = '148',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})

    final_zamplia_surveys = []
    zamplia_survey_numbers = []

    try:
        def map_zamplia_surveys(survey):
            if int(survey['LOI']) > int(surveyparams.bid_loi_lte) or int(survey['LOI']) < int(surveyparams.bid_loi_gte):
                return
            if int(survey['IR']) > int(surveyparams.bid_incidence_lte) or int(survey['IR']) < int(surveyparams.bid_incidence_gte):
                return
            if float(survey['CPI']) > float(surveyparams.cpi_lte) or float(survey['CPI']) < float(surveyparams.cpi_gte):
                return
            if str(survey["LanguageId"]) not in clientdbcountrylang_valueslist:
                return
            for index in clientdbcountrylang_values:
                if int(index['zamplia_client_language_id']) == int(survey["LanguageId"]):
                    CountryLanguageobj = index
                    break
            h = hashlib.blake2b(digest_size=25)
            grp_num = bin(int(survey['SurveyId']))
            h.update(grp_num.encode())
            S_value = h.hexdigest()
            final_zamplia_surveys.append({
                'project_group_country_id' : CountryLanguageobj['country_id_id'],
                'project_group_language_id' : CountryLanguageobj['lanugage_id_id'],
                'client_survey_number' : str(survey['SurveyId']),
                'project_group_name' : survey['Name'],
                'project_group_loi' : survey['LOI'],
                'project_group_incidence' : survey['IR'],
                'project_group_cpi' : survey['CPI'],
                'project_group_completes' : survey['TotalCompleteRequired'],
                'project_group_clicks' : 1000000,
                'project_group_status' : 'Live',
                'project_group_encodedS_value' : S_value,
                'project_group_encodedR_value' : S_value,
                'show_on_DIY' : False,
                'project_group_ip_check' : False,
                'project_group_pid_check' : False,
                'ad_enable_panel' : True,
                'project_group_liveurl' : 'https://panelviewpoint.com/?RID=%%RID%%',
                'project_group_testurl' : 'https://panelviewpoint.com/?RID=%%RID%%'

            })
            zamplia_survey_numbers.append(str(survey['SurveyId']))
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            yield_results = list(executor.map(map_zamplia_surveys, response.json()['result']['data']))
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'zamplia',line_number = '194',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})

    try:
        zamplia_surveys_break_list = [final_zamplia_surveys[:100],final_zamplia_surveys[100:200],final_zamplia_surveys[200:300],final_zamplia_surveys[300:400],final_zamplia_surveys[400:500],final_zamplia_surveys[500:600],final_zamplia_surveys[600:700],final_zamplia_surveys[700:800],final_zamplia_surveys[800:900],final_zamplia_surveys[900:1000],final_zamplia_surveys[1000:1100],
        final_zamplia_surveys[1100:1200],final_zamplia_surveys[1200:1300],final_zamplia_surveys[1300:1400],final_zamplia_surveys[1400:1500],final_zamplia_surveys[1500:1600],final_zamplia_surveys[1600:1700],final_zamplia_surveys[1700:1800],final_zamplia_surveys[1800:1900],final_zamplia_surveys[1900:2000],final_zamplia_surveys[2000:2100],final_zamplia_surveys[2100:2200],final_zamplia_surveys[2200:2300],final_zamplia_surveys[2300:2400],final_zamplia_surveys[2400:2500],final_zamplia_surveys[2500:2600],final_zamplia_surveys[2600:2700],final_zamplia_surveys[2700:2800],final_zamplia_surveys[2800:2900],final_zamplia_surveys[2900:3000],final_zamplia_surveys[3000:3100],final_zamplia_surveys[3100:3200],final_zamplia_surveys[3200:3300],final_zamplia_surveys[3300:3400],final_zamplia_surveys[3400:3500],final_zamplia_surveys[3500:3600],final_zamplia_surveys[3600:3700],final_zamplia_surveys[3700:3800],final_zamplia_surveys[3800:3900],final_zamplia_surveys[3900:4000],final_zamplia_surveys[4000:4100],final_zamplia_surveys[4100:4200],final_zamplia_surveys[4200:4300],final_zamplia_surveys[4300:4400],final_zamplia_surveys[4400:4500],final_zamplia_surveys[4500:4600],final_zamplia_surveys[4600:4700],final_zamplia_surveys[4700:4800],final_zamplia_surveys[4800:4900],final_zamplia_surveys[4900:]]

        def post_zamplia_surveys(surveys):
            
            if len(surveys) != 0:
                client_survey_lists_celery_pvp({"surveys":surveys,'client_name':'zamplia'})
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            yield_results = list(executor.map(post_zamplia_surveys, zamplia_surveys_break_list))

        if len(zamplia_survey_numbers)>0:
            client_survey_supplier_live(zamplia_survey_numbers)
        
        # We are checking length intentionally to make sure we always get more than 30 surveys from Zamplia. We believe that if we are getting less than 30 surveys it means there is some error at Zamplia end and it is pausing all of the our live surveys. 
        #also we added log how many surveys got in last call
        if len(zamplia_survey_numbers) > 30:
            client_survey_pause('survey_live','zamplia',zamplia_survey_numbers,None)

    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'zamplia',line_number = '217',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})

    try:
        total_zamplia_quotas_list = []
        paused_survey_list = []
        def get_zamplia_quotas_qualifications(survey_number):

            try:
                client_quotas = requests.get(f'{ZAMPLIA_CLIENT_BASE_URL}/Surveys/GetSurveyQuotas?SurveyId={survey_number}', headers=zampliaheaders).json()['result']['data']
                client_qualifications = requests.get(f'{ZAMPLIA_CLIENT_BASE_URL}/Surveys/GetSurveyQualifications?SurveyId={survey_number}', headers=zampliaheaders).json()['result']['data']

                total_zamplia_quotas_list.append({
                    'client_quotas' : client_quotas,
                    'client_qualifications' : client_qualifications,
                    'survey_number' : survey_number
                })
            except Exception as error:
                ClientSupplierAPIErrorLog.objects.create(client_name = 'zamplia',line_number = '235',error_details = error)
                paused_survey_list.append(survey_number)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            yield_results = list(executor.map(get_zamplia_quotas_qualifications, zamplia_survey_numbers))
        
        if len(paused_survey_list)>0:
            client_survey_pause('survey_pause','zamplia',[],[paused_survey_list])
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'zamplia',line_number = '244',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})

    zamplia_quotas_break_list = [total_zamplia_quotas_list[0:100],total_zamplia_quotas_list[100:200],total_zamplia_quotas_list[200:300],total_zamplia_quotas_list[300:400],total_zamplia_quotas_list[400:500],total_zamplia_quotas_list[500:600],total_zamplia_quotas_list[600:700],total_zamplia_quotas_list[700:800],total_zamplia_quotas_list[800:900],total_zamplia_quotas_list[900:1000],total_zamplia_quotas_list[1000:1100],total_zamplia_quotas_list[1100:1200],total_zamplia_quotas_list[1200:1300],total_zamplia_quotas_list[1300:1400],total_zamplia_quotas_list[1400:1500],total_zamplia_quotas_list[1500:1600],total_zamplia_quotas_list[1600:1700],total_zamplia_quotas_list[1700:1800],total_zamplia_quotas_list[1800:1900],total_zamplia_quotas_list[1900:2000],total_zamplia_quotas_list[2000:2100],total_zamplia_quotas_list[2100:2200],total_zamplia_quotas_list[2200:2300],total_zamplia_quotas_list[2300:2400],total_zamplia_quotas_list[2400:2500],total_zamplia_quotas_list[2500:2600],total_zamplia_quotas_list[2600:2700],total_zamplia_quotas_list[2700:2800],total_zamplia_quotas_list[2800:2900],total_zamplia_quotas_list[2900:3000],total_zamplia_quotas_list[3000:3100],total_zamplia_quotas_list[3100:3200],total_zamplia_quotas_list[3200:3300],total_zamplia_quotas_list[3300:3400],total_zamplia_quotas_list[3400:3500],total_zamplia_quotas_list[3500:3600],total_zamplia_quotas_list[3600:3700],total_zamplia_quotas_list[3700:3800],total_zamplia_quotas_list[3800:3900],total_zamplia_quotas_list[3900:]]

    try:
        def send_zamplia_quotas_qualifications(zamplia_quotas):
            if len(zamplia_quotas) != 0:
                client_survey_of_quotas_lists_celery_pvp({"client_name":"zamplia","qualifications" : zamplia_quotas})
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            yield_results = list(executor.map(send_zamplia_quotas_qualifications, zamplia_quotas_break_list))
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'zamplia',line_number = '256',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})

def SagoClientSurveyFetchAPI():
    try:
        sago_surveys = requests.get(f'{SAGO_BASEURL}api/v2/survey/allocated-surveys',headers=sagoheader)

        if sago_surveys.status_code not in [200,201] or 'Surveys' not in sago_surveys.json() or len(sago_surveys.json()['Surveys']) == 0:
            return
        ClientSupplierFetchSurveysLog.objects.create(client_name = 'sago',total_surveys_fetch = len(sago_surveys.json()['Surveys']))
        surveyparams = survey_qualify_parameters_check('sago')[0]

        survey_list = sago_surveys.json()['Surveys']
        final_surveys = []
        sago_survey_number = []

        def map_sago_surveys(survey):

            if survey['LanguageId'] != 3:
                return
            if int(survey['LOI']) > int(surveyparams['bid_loi_lte']) or int(survey['LOI']) < int(surveyparams['bid_loi_gte']):
                return
            if int(survey['IR']) > int(surveyparams['bid_incidence_lte']) or int(survey['IR']) < int(surveyparams['bid_incidence_gte']):
                return
            if float(survey['CPI']) > float(surveyparams['cpi_lte']) or float(survey['CPI']) < float(surveyparams['cpi_gte']):
                return
            
            h = hashlib.blake2b(digest_size=25)
            grp_num = bin(int(survey['SurveyId']))
            h.update(grp_num.encode())
            S_value = h.hexdigest()

            final_surveys.append({
                'project_group_country_id' : '244',
                'project_group_language_id' : '41',
                'client_survey_number' : str(survey['SurveyId']),
                'project_group_name' : survey['SurveyId'],
                'project_group_loi' : survey['LOI'],
                'project_group_incidence' : survey['IR'],
                'project_group_cpi' : survey['CPI'],
                'project_group_completes' : 500,
                'project_group_clicks' : 10000,
                'project_group_status' : 'Live',
                'project_group_encodedS_value' : S_value,
                'project_group_encodedR_value' : S_value,
                'show_on_DIY' : False,
                'project_group_ip_check' : False,
                'project_group_pid_check' : False,
                'ad_enable_panel' : True,
                'project_group_liveurl' : survey['LiveLink'].replace("[#scid#]","%%RID%%"),
                'project_group_testurl' : survey['LiveLink'].replace("[#scid#]","%%RID%%")

            })

            sago_survey_number.append(str(survey['SurveyId']))

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            yield_results = list(executor.map(map_sago_surveys, survey_list))
        try:
            if len(sago_survey_number) > 30:
                client_survey_pause('survey_live','sago',sago_survey_number,None)
                
            sago_surveys_break_list = [final_surveys[:100],final_surveys[100:200],final_surveys[200:300],final_surveys[300:400],final_surveys[400:500],final_surveys[500:600],final_surveys[600:700],final_surveys[700:800],final_surveys[800:900],final_surveys[900:1000],final_surveys[1000:1100],final_surveys[1100:1200],final_surveys[1200:1300],final_surveys[1300:1400],final_surveys[1400:1500],final_surveys[1500:1600],final_surveys[1600:1700],final_surveys[1700:1800],final_surveys[1800:1900],final_surveys[1900:2000],final_surveys[2000:2100],final_surveys[2100:2200],final_surveys[2200:2300],final_surveys[2300:2400],final_surveys[2400:2500],final_surveys[2500:2600],final_surveys[2600:2700],final_surveys[2700:2800],final_surveys[2800:2900],final_surveys[2900:3000],final_surveys[3000:3100],final_surveys[3100:3200],final_surveys[3200:3300],final_surveys[3300:3400],final_surveys[3400:3500],final_surveys[3500:3600],final_surveys[3600:3700],final_surveys[3700:3800],final_surveys[3800:3900],final_surveys[3900:]]
            
            def post_sago_surveys(surveys):
                
                if len(surveys) != 0:
                    client_survey_lists_celery_pvp({"surveys":surveys,'client_name':'sago'})
    
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                yield_results = list(executor.map(post_sago_surveys, sago_surveys_break_list))

        except Exception as error:
            ClientSupplierAPIErrorLog.objects.create(client_name = 'sagoapi',line_number = '326',error_details = error)
            return JsonResponse({"message": "Something Want Wrong"})
        
        try:
            sago_mapped_qualifications = []
            def post_sago_surveys(surveyId):
                sago_survey_qualifications = requests.get(f'{SAGO_BASEURL}api/v2/survey/survey-qualifications/{surveyId}',headers=sagoheader)
                if sago_survey_qualifications.status_code not in [200,201] or 'SurveyQualifications' not in sago_survey_qualifications.json() or len(sago_survey_qualifications.json()['SurveyQualifications']) == 0:

                    client_survey_pause('survey_pause','sago',[],[surveyId])

                    return
                sago_mapped_qualifications.append({"client_qualifications" : sago_survey_qualifications.json()['SurveyQualifications'],"survey_number": surveyId})
                
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                yield_results = list(executor.map(post_sago_surveys, sago_survey_number))
            try:
                sago_mapped_qualifications_list = [sago_mapped_qualifications[:100],sago_mapped_qualifications[100:200],sago_mapped_qualifications[200:300],sago_mapped_qualifications[300:400],sago_mapped_qualifications[400:500],sago_mapped_qualifications[500:600],sago_mapped_qualifications[600:700],sago_mapped_qualifications[700:800],sago_mapped_qualifications[800:900],sago_mapped_qualifications[900:1000],sago_mapped_qualifications[1000:1100],sago_mapped_qualifications[1100:1200],sago_mapped_qualifications[1200:1300],sago_mapped_qualifications[1300:1400],sago_mapped_qualifications[1400:1500],sago_mapped_qualifications[1500:1600],sago_mapped_qualifications[1600:1700],sago_mapped_qualifications[1700:1800],sago_mapped_qualifications[1800:1900],sago_mapped_qualifications[1900:2000],sago_mapped_qualifications[2000:2100],sago_mapped_qualifications[2100:2200],sago_mapped_qualifications[2200:2300],sago_mapped_qualifications[2300:2400],sago_mapped_qualifications[2400:2500],sago_mapped_qualifications[2500:2600],sago_mapped_qualifications[2600:2700],sago_mapped_qualifications[2700:2800],sago_mapped_qualifications[2800:2900],sago_mapped_qualifications[2900:3000],sago_mapped_qualifications[3000:3100],sago_mapped_qualifications[3100:3200],sago_mapped_qualifications[3200:3300],sago_mapped_qualifications[3300:3400],sago_mapped_qualifications[3400:3500],sago_mapped_qualifications[3500:3600],sago_mapped_qualifications[3600:3700],sago_mapped_qualifications[3700:3800],sago_mapped_qualifications[3800:3900],sago_mapped_qualifications[3900:]]

                def post_sago_qualifications(qualifications):
                    client_survey_of_quotas_lists_celery_pvp({"client_name":"sago","qualifications" : qualifications})
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    yield_results = list(executor.map(post_sago_qualifications, sago_mapped_qualifications_list))
            except Exception as error:
                ClientSupplierAPIErrorLog.objects.create(client_name = 'sagoapi',line_number = '351',error_details = error)
                return JsonResponse({"message": "Something Want Wrong"})
        except Exception as error:
            ClientSupplierAPIErrorLog.objects.create(client_name = 'sagoapi',line_number = '354',error_details = error)
            return JsonResponse({"message": "Something Want Wrong"})
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'sagoapi',line_number = '357',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})

@api_view(['GET'])
def ClientSurveyFetchAPI(request):
    if settings.CELERY:
        CeleryRunLog.objects.create(taskname = 'ClientSurveyFetchAPI Started')
        close_old_connections()
        try:
            if ClientSupplierEnableDisableAPI.objects.get(client_name = 'toluna').is_enable:
                get_toluna_surveys()
                AddUpdateDefaultSupplier('toluna')
                CeleryRunLog.objects.create(taskname = 'Toluna Surveys Created')
        except Exception as error:
            ClientSupplierAPIErrorLog.objects.create(client_name = 'toluna',line_number = '369',error_details = error)
            pass
        try:
            if ClientSupplierEnableDisableAPI.objects.get(client_name = 'zamplia').is_enable:
                get_zamplia_surveys()
                AddUpdateDefaultSupplier('zamplia')
                CeleryRunLog.objects.create(taskname = 'Zamplia Surveys Created')
        except Exception as error:
            ClientSupplierAPIErrorLog.objects.create(client_name = 'zamplia',line_number = '377',error_details = error)
            pass
        try:
            if ClientSupplierEnableDisableAPI.objects.get(client_name = 'sago').is_enable:
                SagoClientSurveyFetchAPI()
                AddUpdateDefaultSupplier('sago')
                CeleryRunLog.objects.create(taskname = 'Sago Surveys Created')
        except Exception as error:
            ClientSupplierAPIErrorLog.objects.create(client_name = 'sago',line_number = '385',error_details = error)
            pass             
        try:
            supplierbuyer_projectgroup_create()
        except Exception as error:
            ClientSupplierAPIErrorLog.objects.create(client_name = 'Supplier_Buyer_Updated',line_number = '413',error_details = error)
            pass
        # try:
        #     PanelEnabledSurveyFetchAPI()
        # except Exception as error:
        #     ClientSupplierAPIErrorLog.objects.create(client_name = 'OPINIONSDEALS',line_number = '118',error_details = error)
        #     pass
        close_old_connections()        
        return JsonResponse({"message": "Success"})
    else:
        CeleryRunLog.objects.create(taskname = 'ClientSurveyFetchAPI - CELERY OFF')
        return JsonResponse({"message": "CELERY OFF"})
    
@shared_task
def DeletePast3MonthsLogs():
    try:
        if settings.CELERY:
            CeleryRunLog.objects.create(taskname = 'DeletePast3MonthsLogs Started')
            CeleryRunLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            ClientSupplierAPIErrorLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            ClientSupplierFetchSurveysLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            EmployeeLoginLog.objects.all().delete()
            ProjectLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            ProjectErrorLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            ProjectGroupLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            ProjectGroupErrorLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            ProjectGroupPanelLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            ProjectGroupADPanelLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            CustomerLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            SupplierLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            SupplierEnableDisableLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            SubSupplierLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            SubSupplierEnableDisableLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            ProjectGroupSupplierLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            InvoiceLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            DraftInvoiceLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            ProjectGroupPrescreenerLogs.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            RespondentDetailErrorLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            InvoiceExceptionsLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            SupplierInvoiceLogs.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            SurveyEntryLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            CeleryAPICallLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            ProjectReconciliationLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            ProjectSupplierCPIUpdateLog.objects.exclude(created_at__gte = datetime.now() - timedelta(days = 30)).delete()
            CeleryRunLog.objects.create(taskname = 'DeletePast3MonthsLogs End')
            return JsonResponse({"message": "Success"})
        else:
            return JsonResponse({"message": "CELERY OFF"})
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'DeletePast3Months',line_number = '425',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})


def supplierbuyer_projectgroup_create():
    try:
        if settings.CELERY:
            CeleryRunLog.objects.create(taskname = 'supplierbuyer_projectgroup_create Started')
            SupplierBuyerProjectGroupCreateView()
            CeleryConversionCalculation()
            CeleryRunLog.objects.create(taskname = 'supplierbuyer_projectgroup_create End')
            return JsonResponse({"message": "Success"})
        else:
            return JsonResponse({"message": "CELERY OFF"})
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'SupplierBuyer',line_number = '295',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})


@shared_task
def survey_priority_set():
    try:
        if settings.CELERY:
            CeleryRunLog.objects.create(taskname = 'survey_priority_set Started')
            SurveyPriorityCelery()
            CeleryRunLog.objects.create(taskname = 'survey_priority_set End')
            return JsonResponse({"message": "Success"})
        else:
            return JsonResponse({"message": "CELERY OFF"})
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'SurveyPrioritySet',line_number = '318',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})

    
def PanelEnabledSurveyFetchAPI():

    try:
        project_grp_list = ProjectGroup.objects.filter(project_group_status = "Live",enable_panel = True)
        survey_list =  ProjectGroupSerializer(project_grp_list,many=True).data
        panel_source = SupplierOrganisation.objects.get(supplier_type = "4")
        survey_preescreener_list = [
            survey_list[0:50], survey_list[50:100], survey_list[100:150], survey_list[150:200], survey_list[200:250],
            survey_list[250:300], survey_list[300:350], survey_list[350:400], survey_list[400:450], survey_list[450:500],
            survey_list[500:550], survey_list[550:600], survey_list[600:650], survey_list[650:700], survey_list[700:750],
            survey_list[750:800], survey_list[800:850], survey_list[850:900], survey_list[900:950], survey_list[950:1000],
            survey_list[1000:1050], survey_list[1050:1100], survey_list[1100:1150], survey_list[1150:1200], survey_list[1200:1250],
            survey_list[1250:1300], survey_list[1300:1350], survey_list[1350:1400], survey_list[1400:1450], survey_list[1450:1500],
            survey_list[1500:1550], survey_list[1550:1600], survey_list[1600:1650], survey_list[1650:1700], survey_list[1700:1750],
            survey_list[1750:1800], survey_list[1800:1850], survey_list[1850:1900], survey_list[1900:1950], survey_list[1950:2000],
            survey_list[2000:2050], survey_list[2050:2100], survey_list[2100:2150], survey_list[2150:2200], survey_list[2200:2250],
            survey_list[2250:2300], survey_list[2300:2350], survey_list[2350:2400], survey_list[2400:2450], survey_list[2450:2500],
            survey_list[2500:2550], survey_list[2550:2600], survey_list[2600:2650], survey_list[2650:2700], survey_list[2700:2750],
            survey_list[2750:2800], survey_list[2800:2850], survey_list[2850:2900], survey_list[2900:2950], survey_list[2950:3000],
            survey_list[3000:3050], survey_list[3050:3100], survey_list[3100:3150], survey_list[3150:3200], survey_list[3200:3250],
            survey_list[3250:3300], survey_list[3300:3350], survey_list[3350:3400], survey_list[3400:3450], survey_list[3450:3500],
            survey_list[3500:3550], survey_list[3550:3600], survey_list[3600:3650], survey_list[3650:3700], survey_list[3700:3750],
            survey_list[3750:3800], survey_list[3800:3850], survey_list[3850:3900], survey_list[3900:3950], survey_list[3950:4000],
            survey_list[4000:4050], survey_list[4050:4100], survey_list[4100:4150], survey_list[4150:4200], survey_list[4200:4250],
            survey_list[4250:4300], survey_list[4300:4350], survey_list[4350:4400], survey_list[4400:4450], survey_list[4450:4500],
            ]
        
        def survey_preescreener_data(survey_prescreener):
            if len(survey_prescreener) != 0:
                requests.post(f'{settings.OPINIONSDEALSNEW_BASE_URL}survey-create-opinionsdeal',
                             json={'survey':survey_prescreener,'panel_source':panel_source.id})

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(survey_preescreener_data, survey_preescreener_list))

        requests.post(f'{settings.OPINIONSDEALSNEW_BASE_URL}survey-status-update-opinionsdeal', json=list(project_grp_list.values_list('project_group_number', flat=True)))
        
        survey_priority_resp = RountingPriority.objects.filter(
            project_group__project_group_status = "Live",
            project_group__enable_panel = True).values_list(
            'project_group__project_group_number',flat=True
        )
        
        requests.post(f'{settings.OPINIONSDEALSNEW_BASE_URL}survey-priority-create-opinionsdeal', json=list(survey_priority_resp))
        CeleryRunLog.objects.create(taskname = 'Opinions Deal Survey Updated')
        return   
    except Exception as e:
        OpinionsDealErrorLog.objects.create(client_name = "Opinions Deal", line_number = "552", error_details = e)
        return JsonResponse({"message": "Opinions Deal Error Found"})


@shared_task
def FinalIdsSendTwiceInWeekAPI():
    try:
        if settings.CELERY:
            CeleryRunLog.objects.create(taskname = 'FinalIdsSendTwiceInWeekAPI Started')
            project_number_list = list(SupplierIdsMarks.objects.filter(
                project__project_status__in=["Invoiced"],
                final_ids_sent = False,
                final_ids_available_by__lte = timezone.now().date(),scrubbed = True
                ).values_list('project__project_number', flat=True))
            
            ProjectGroupSupplier_obj = ProjectGroupSupplier.objects.filter(project_group__project__project_number__in = project_number_list, supplier_org__supplier_type = '1')
            
            supplier_list = set(list(ProjectGroupSupplier_obj.values_list('supplier_org', flat=True)))

            def parellel_send_final_ids_func(supplier):
                
                sup = SupplierOrganisation.objects.get(id =supplier)

                supplier_email_list = list(SupplierContact.objects.filter(supplier_id__id=supplier, send_final_ids=True).values_list('supplier_email',flat=True).order_by().distinct('supplier_email'))

                project_number_list_for_email = list(set(ProjectGroupSupplier_obj.filter(supplier_org__id = supplier).values_list('project_group__project__project_number', flat=True)))

                uuid4_str = uuid.uuid4().hex
                finalids_project_list_code = hashlib.md5(uuid4_str.encode()).hexdigest()

                supplierFinalIdsDeploy.objects.create(project_list=project_number_list_for_email, supplier = sup, final_ids_deployed_by_id = 1, project_list_code = finalids_project_list_code)

                URL = f"{settings.SUPPLIER_DASHBOARD_FRONTEND_URL}#/authentication/finalids/ictXUesVWsi7cKcq30A1XLDkA4w813LuqLph3QpV5W3jFdydmBYi5B/{sup.supplier_code}/{finalids_project_list_code}"

                html_message = render_to_string('supplier_final_ids_email/final_ids_available_email_template.html',{'downloadidsurl':URL, 'projectlist':project_number_list_for_email})

                to_emails = supplier_email_list
                if settings.SERVER_TYPE == 'production':
                    cc_emails = 'projectmanagement@panelviewpoint.com'
                else:
                    cc_emails = 'tech@panelviewpoint.com'
                
                subject = f'Final Ids - PANEL VIEWPOINT: {sup.supplier_name} - {timezone.now().date()}'
                sendEmailSendgripAPIIntegration(from_email = ('finalids@panelviewpoint.com', 'Final IDs'),to_emails=to_emails, subject=subject, html_message=html_message, cc_emails = cc_emails)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                yield_results = list(executor.map(parellel_send_final_ids_func, supplier_list))
            
            SupplierIdsMarks_obj = SupplierIdsMarks.objects.filter(project__project_number__in = project_number_list)
            SupplierIdsMarks_obj.update(final_ids_sent = True, final_ids_sent_date = timezone.now().date(), final_ids_sent_by_id = 1)
            CeleryRunLog.objects.create(taskname = 'FinalIdsSendTwiceInWeekAPI End')
            return JsonResponse({"message": "Success"})
        else:
            return JsonResponse({"message": "CELERY OFF"})
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'FinalIdsSendTwiceInWeek',line_number = '582',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})
    
@shared_task
def DailyWorkStatusEmail():

    try:
        todaydate = datetime.now().date()
    
        invoiced_data = Invoice.objects.values(
            currency = F('invoice_currency__currency_iso')).annotate(
                this_month_invoice_total_amount = Round(Coalesce(Sum('invoice_total_amount',filter=Q(invoice_date__month = datetime.now().month,invoice_date__year = datetime.now().year)),0,output_field=FloatField()),2),
                this_year_invoice_total_amount = Round(Coalesce(Sum('invoice_total_amount',filter=Q(invoice_date__year = datetime.now().year)),0,output_field=FloatField()),2)
                ).exclude(
                    this_month_invoice_total_amount=None,this_year_invoice_total_amount=None
                    )

        client_stats = RespondentDetail.objects.filter(
                end_time_day__year = datetime.now().year,end_time_day__month = datetime.now().month,url_type='Live').values(
                    customer_name = F('respondentdetailsrelationalfield__project__project_customer__cust_org_name')).annotate(
                        revenue=Round(Coalesce(
                            Sum('project_group_cpi', filter=Q(resp_status__in=['4','9'])), 0.0),2), 
                        expense=Round(Coalesce(
                            Sum('supplier_cpi', filter=Q(resp_status='4'), ), 0.0),2), 
                        margin=Case(
                            When(Q(revenue=0.0)|Q(revenue=None),then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))),
                            default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'),output_field=models.DecimalField(max_digits=7,decimal_places=2)),
                        ), 
                        completes = Count('id', filter=Q(resp_status = 4)),
                    ).exclude(revenue=0).order_by('-revenue','-margin')
        
        supplier_stats = RespondentDetail.objects.filter(
                end_time_day__year = datetime.now().year,end_time_day__month = datetime.now().month,url_type='Live').values(
                    supplier_name = F('respondentdetailsrelationalfield__source__supplier_name')).annotate(
                        revenue=Round(Coalesce(
                            Sum('project_group_cpi', filter=Q(resp_status__in=['4','9'])), 0.0),2), 
                        expense=Round(Coalesce(
                            Sum('supplier_cpi', filter=Q(resp_status='4'), ), 0.0),2), 
                        margin=Case(
                            When(Q(revenue=0.0)|Q(revenue=None),then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))),
                            default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'),output_field=models.DecimalField(max_digits=7,decimal_places=2)),
                        ), 
                        completes = Count('id', filter=Q(resp_status = 4)),
                    ).exclude(revenue=0).order_by('-revenue','-margin')
        
        pm_stats = RespondentDetail.objects.filter(
                end_time_day__year = datetime.now().year,url_type='Live').values(
                    pmid = F('respondentdetailsrelationalfield__project__project_manager')).annotate(
                        first_name = F('respondentdetailsrelationalfield__project__project_manager__first_name'),
                        last_name = F('respondentdetailsrelationalfield__project__project_manager__last_name'),
                        revenue=Round(Coalesce(
                            Sum('project_group_cpi', filter=Q(resp_status__in=['4','9'])), 0.0),2), 
                        expense=Round(Coalesce(
                            Sum('supplier_cpi', filter=Q(resp_status='4'), ), 0.0),2), 
                        margin=Case(
                            When(Q(revenue=0.0)|Q(revenue=None),then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))),
                            default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'),output_field=models.DecimalField(max_digits=7,decimal_places=2)),
                        ), 
                        completes = Count('id', filter=Q(resp_status = 4)),
                    ).exclude(revenue=0).order_by('-revenue','-margin')
        
        today = timezone.now().date()
        seven_days_ago = today - timedelta(days=7)
        sevendaysstats = RespondentDetail.objects.filter(
            end_time_day__gte=seven_days_ago,end_time_day__lte=today).values(
                date = F('end_time_day')).annotate(
                    visit = Count('id'),
                    incomplete = Count('id', filter=Q(resp_status = '3')),
                    completes = Count('id', filter=Q(resp_status = '4')),
                    terminate = Count('id', filter=Q(resp_status__in = ['5','2','7'])),
                ).order_by('date')
        
        if settings.SERVER_TYPE == 'production':
            to_emails = ['narendra@panelviewpoint.com','deepak@panelviewpoint.com','geeta@panelviewpoint.com','sahil@panelviewpoint.com']
        else:
            to_emails = ['sahil@panelviewpoint.com']
        html_message = render_to_string('AutomatedEmailNotifications/dailyupdates.html',{
            'invoiced_data': list(invoiced_data),
            'clientrespdata': client_stats,
            'supplierrespdata': supplier_stats,
            'pmrespdata': pm_stats,
            'todaydate' : todaydate,
            '7daysstats' : sevendaysstats
        })
        subject = f'Daily Updates - {todaydate}'
        sendEmailSendgripAPIIntegration(
            from_email = ('tech@panelviewpoint.com'),
            to_emails=to_emails,
            subject=subject,
            html_message=html_message
        )
        CeleryRunLog.objects.create(taskname = 'DailyWorkStatusEmail Completed')
        return JsonResponse({"message": "Success"})
    except Exception as error:
        ClientSupplierAPIErrorLog.objects.create(client_name = 'Daily-update-to-owner',line_number = '634',error_details = error)
        return JsonResponse({"message": "Something Want Wrong"})