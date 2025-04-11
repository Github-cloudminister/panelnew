# ======== in-project imports ========
from Questions.models import ZipCodeMappingTable
from affiliaterouter.models import *
from Project.models import *
import concurrent.futures
from django.conf import settings

max_workers = 10 if settings.SERVER_TYPE == 'localhost' else 50

def get_project_group_priority_surveys(suppliercode,subsuppliercode, country, language,mincpi):
    finalised_survey_list = ProjectGroupSupplier.objects.filter(project_group__rountingpriority__project_group__project_group_status = "Live",supplier_org__supplier_code=suppliercode, project_group__project_group_country__country_code=country, project_group__project_group_language__language_code=language,supplier_status='Live',project_group__project_group_status = 'Live',cpi__gte = mincpi)

    if subsuppliercode:
        finalised_survey_list = finalised_survey_list.filter(
            project_group_supplier_fk__sub_supplier_org__sub_supplier_code = subsuppliercode,
            project_group_supplier_fk__sub_supplier_status = 'Live')

    return finalised_survey_list

def get_project_group_supplier_overall(suppliercode,subsuppliercode, country, language,mincpi):
    finalised_survey_list = ProjectGroupSupplier.objects.filter(supplier_org__supplier_code=suppliercode, project_group__project_group_country__country_code=country, project_group__project_group_language__language_code=language,supplier_status='Live',project_group__project_group_status = 'Live',cpi__gte = mincpi).order_by('-project_group__project_group_incidence')

    if subsuppliercode:
        finalised_survey_list = finalised_survey_list.filter(
            project_group_supplier_fk__sub_supplier_org__sub_supplier_code = subsuppliercode,
            project_group_supplier_fk__sub_supplier_status = 'Live')

    return finalised_survey_list


def get_project_group_supplier_cnt_router_data(suppliercode,subsuppliercode, country, language,mincpi):
    finalised_survey_list = ProjectGroupSupplier.objects.filter(supplier_org__supplier_code=suppliercode, project_group__project_group_country__country_code=country, project_group__project_group_language__language_code=language,supplier_status='Live',project_group__project_group_status = 'Live',project_group__project__project_customer__customer_url_code = "lucid-redirect",cpi__gte = mincpi).order_by('-project_group__project_group_incidence')

    if subsuppliercode:
        finalised_survey_list = finalised_survey_list.filter(
            project_group_supplier_fk__sub_supplier_org__sub_supplier_code = subsuppliercode,
            project_group_supplier_fk__sub_supplier_status = 'Live')

    return finalised_survey_list


def get_project_group_supplier_toluna_data(suppliercode,subsuppliercode, country, language,mincpi):

    finalised_survey_list = ProjectGroupSupplier.objects.filter(supplier_org__supplier_code=suppliercode, project_group__project_group_country__country_code=country, project_group__project_group_language__language_code=language,supplier_status='Live',project_group__project_group_status = 'Live',project_group__project__project_customer__customer_url_code = "toluna",cpi__gte = mincpi).order_by('-project_group__project_group_incidence')
    
    if subsuppliercode:
        finalised_survey_list = finalised_survey_list.filter(
            project_group_supplier_fk__sub_supplier_org__sub_supplier_code = subsuppliercode,
            project_group_supplier_fk__sub_supplier_status = 'Live')

    return finalised_survey_list

def get_project_group_supplier_api_client_data(suppliercode,subsuppliercode, country, language,mincpi):

    finalised_survey_list = ProjectGroupSupplier.objects.filter(supplier_org__supplier_code=suppliercode, project_group__project_group_country__country_code=country, project_group__project_group_language__language_code=language,supplier_status='Live',project_group__project_group_status = 'Live',project_group__project__project_customer__customer_url_code__in = ["toluna","zamplia","sago"],cpi__gte = mincpi).order_by('-project_group__project_group_incidence')
    
    if subsuppliercode:
        finalised_survey_list = finalised_survey_list.filter(
            project_group_supplier_fk__sub_supplier_org__sub_supplier_code = subsuppliercode,
            project_group_supplier_fk__sub_supplier_status = 'Live')

    return finalised_survey_list

def get_project_group_supplier_logic_group_data(suppliercode,subsuppliercode, country, language,mincpi):
    finalised_survey_list = ProjectGroupSupplier.objects.filter(supplier_org__supplier_code=suppliercode, project_group__project_group_country__country_code=country, project_group__project_group_language__language_code=language,supplier_status='Live',project_group__project_group_status = 'Live',project_group__project__project_customer__customer_url_code = "zamplia",cpi__gte = mincpi).order_by('-project_group__project_group_incidence')
    
    if subsuppliercode:
        finalised_survey_list = finalised_survey_list.filter(
            project_group_supplier_fk__sub_supplier_org__sub_supplier_code = subsuppliercode,
            project_group_supplier_fk__sub_supplier_status = 'Live')

    return finalised_survey_list

def get_project_group_supplier_sago_data(suppliercode,subsuppliercode, country, language,mincpi):
    finalised_survey_list = ProjectGroupSupplier.objects.filter(supplier_org__supplier_code=suppliercode, project_group__project_group_country__country_code=country, project_group__project_group_language__language_code=language,supplier_status='Live',project_group__project_group_status = 'Live',project_group__project__project_customer__customer_url_code = "sago",cpi__gte = mincpi).order_by('-project_group__project_group_incidence')
    
    if subsuppliercode:
        finalised_survey_list = finalised_survey_list.filter(
            project_group_supplier_fk__sub_supplier_org__sub_supplier_code = subsuppliercode,
            project_group_supplier_fk__sub_supplier_status = 'Live')

    return finalised_survey_list

def get_project_group_supplier_internal_survey_data(suppliercode,subsuppliercode, country, language,mincpi):
    finalised_survey_list = ProjectGroupSupplier.objects.filter(supplier_org__supplier_code=suppliercode, project_group__project_group_country__country_code=country, project_group__project_group_language__language_code=language,supplier_status='Live',project_group__project_group_status = 'Live',cpi__gte = mincpi).exclude(project_group__project__project_customer__customer_url_code__in = ['toluna','zamplia','sago']).order_by('-project_group__project_group_incidence')

    if subsuppliercode:
        finalised_survey_list = finalised_survey_list.filter(
            project_group_supplier_fk__sub_supplier_org__sub_supplier_code = subsuppliercode,
            project_group_supplier_fk__sub_supplier_status = 'Live')

    return finalised_survey_list


def survey_decision(project_group_supplier_qs,questiondata_qs):

    """
    1) Pass list of Project Group Supplier
    2) Pass This Type Of Json of Internal Questions/Answers ids For Check Best Match Surveys from Project Group Supplier List
    3) Primary It will gives Thouse Surveys Who Matches all Question/Answers if No Any totally Match Than Given Most Appropriate  

    {
        "112258": ["613330"],
        "112393": ["616744","616746"],
        "112498": "12345",                       #Zipcode Answer
        "112499": ["617931"],
        "112521": "11-06-1997"                   #Date Of Birth Answer
    }
    
    """
    excluded_surveys = []
    available_surveys = project_group_supplier_qs
    age_questionid = ['112521','181411','900002']
    zipcode_questionid = ['112498','181412','900073']

    def survey_decision_thred(project_group_supplier):
        for question,answers in questiondata_qs.items():
            question_number_list = list(
                project_group_supplier.project_group.projectgroupprescreener_set.filter(
                    is_enable="True").values_list('translated_question_id__Internal_question_id',flat = True))

            #For Date of Birth Question Answer
            if question in age_questionid and question in question_number_list:

                day,month,year = map(int, answers.split("-"))
                today = datetime.today()
                age = today.year - year - ((today.month, today.day) < (month, day))
                min_age_list = project_group_supplier.project_group.projectgroupprescreener_set.get(
                    translated_question_id__Internal_question_id__in = age_questionid,is_enable="True").allowedRangeMin.split(',')
                max_age_list = project_group_supplier.project_group.projectgroupprescreener_set.get(
                    translated_question_id__Internal_question_id__in = age_questionid,is_enable="True").allowedRangeMax.split(',')
                boolean_list = list(map(lambda x,y:int(age) >= int(x) and int(age) <= int(y),min_age_list,max_age_list))

                if any(boolean_list) == False:
                    excluded_surveys.append(project_group_supplier.project_group.project_group_number)

            # For Zipcode Question Answer
            elif question in zipcode_questionid and question in question_number_list:

                if project_group_supplier.project_group.projectgroupprescreener_set.get(
                    translated_question_id__Internal_question_id__in = zipcode_questionid).allowed_zipcode_list != []:

                    if answers not in project_group_supplier.project_group.projectgroupprescreener_set.get(
                        translated_question_id__Internal_question_id__in = zipcode_questionid).allowed_zipcode_list:
                        excluded_surveys.append(project_group_supplier.project_group.project_group_number)

            #For SS/MS Question Answer
            elif question in question_number_list:

                if not list(set(list(project_group_supplier.project_group.projectgroupprescreener_set.get(translated_question_id__Internal_question_id = question,is_enable="True").allowedoptions.all().values_list('internal_answer_id',flat = True))) & set(answers)):
                    excluded_surveys.append(project_group_supplier.project_group.project_group_number)

            # For City Zip Question Answer
            if question in zipcode_questionid and project_group_supplier.project_group.projectgroupprescreener_set.filter(
                is_enable="True",translated_question_id__parent_question_type = 'CTZIP').count() != 0:
                for question_obj in project_group_supplier.project_group.projectgroupprescreener_set.filter(
                    translated_question_id__parent_question_type = 'CTZIP',is_enable="True"):
                    if answers not in list(ZipCodeMappingTable.objects.filter(
                        parent_answer_id__internal_answer_id__in = list(
                            question_obj.allowedoptions.all().values_list(
                                'internal_answer_id',flat = True))).values_list('zipcode',flat = True)):
                            excluded_surveys.append(project_group_supplier.project_group.project_group_number)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        yield_results = list(executor.map(survey_decision_thred, project_group_supplier_qs))

    # Exclude Thouse Surveys Who have Extra Questions Not asked in Router
    # if no any Survey Than Passed Qualified list

    newavailable_surveys = available_surveys.exclude(project_group__project_group_number__in = excluded_surveys)
    finalized_excluded_surveys = []
    fullfinalsurvey = newavailable_surveys

    def survey_final_decision_thred(survey):
        if not set(list(survey.project_group.projectgroupprescreener_set.filter(is_enable = True).values_list('translated_question_id__Internal_question_id',flat=True))).issubset(set(list(questiondata_qs.keys()))):
            finalized_excluded_surveys.append(survey.project_group.project_group_number)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        yield_results = list(executor.map(survey_final_decision_thred, newavailable_surveys))

    fullfinalsurvey = fullfinalsurvey.exclude(project_group__project_group_number__in = finalized_excluded_surveys)
    return fullfinalsurvey if len(fullfinalsurvey) !=0 else newavailable_surveys