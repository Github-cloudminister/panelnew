import requests

from Questions.models import TranslatedAnswer
from .models import *
from .serializers import *
from Project.permissions import *
from Prescreener.models import ProjectGroupPrescreener
from django.conf import settings
from django.db.models import F


def create_panel(project_group):
    panel_source = SupplierOrganisation.objects.get(supplier_type = "4")
    survey_screener_list = ProjectGroupPrescreener.objects.filter(project_group_id=project_group, is_enable = True)
    if survey_screener_list.count() > 0:
        # ****************** Check Gender exist or not ***********************
        gender_dict = {"Male":1,"Female":2, "Others":3, "Prefer not to answer":4}
        gender_list = []
        try:
            gender_obj = survey_screener_list.get(translated_question_id__parent_question__parent_question_number = "Gender")
            for gen in gender_obj.allowedoptions.all():
                if gen.translated_answer in gender_dict:
                    gender_list.append(gender_dict[gen.translated_answer])
        except:
            gender_list = [1,2,3,4]
        # ****************** End Check Gender exist or not ***********************
        
        # ****************** Check Age exist or not ***********************
        try:
            getAge = survey_screener_list.get(translated_question_id__parent_question__parent_question_number = "Age")
            min_age = getAge.allowedRangeMin
            max_age = getAge.allowedRangeMax
        except:
            min_age = 0
            max_age = 0
        # ****************** End Check Age exist or not ***********************

        survey_profile = {
            "gender": gender_list,
            "min_age": min_age,
            "max_age": max_age,
            "country": project_group.project_group_country.country_code,
            "preferred_language": project_group.project_group_language.language_code
        }
    else:
        survey_profile = {
            "gender": [1,2,3,4],
            "min_age": 18,
            "max_age": 99,
            "country": project_group.project_group_country.country_code,
            "preferred_language": project_group.project_group_language.language_code
        }
    data = {
        "survey_number": project_group.project_group_number,
        "survey_name": project_group.project_group_name,
        "survey_url": project_group.project_group_surveyurl + '&source='+ str(panel_source.id),
        "survey_category": project_group.project.project_category,
        "survey_loi": project_group.project_group_loi,
        "survey_reward_points": project_group.panel_reward_points,
        "survey_cpi": project_group.project_group_cpi,
        "survey_status": project_group.project_group_status,
        "allow_duplicate": False,
        "survey_profile": survey_profile,
        }
    req2 = requests.post(settings.OPINIONSDEALSNEW_BASE_URL + 'panel/survey/create', json=data)

    return req2

def delete_panel_data(project_group):
    req = requests.post( settings.OPINIONSDEALSNEW_BASE_URL + 'panel/survey/delete/' + str(project_group.project_group_number))
    return req


def play_paused_panel_data(project_group):
    req = requests.post( settings.OPINIONSDEALSNEW_BASE_URL + 'panel/survey/update/' + str(project_group.project_group_number))
    return req


def create_slick_router(project_group):

    data = {
        "project_group_number": project_group.project_group_number,
        "project_group_name": project_group.project_group_name,
        "project_group_surveyurl": project_group.project_group_surveyurl + '&source=',
        "project_category": project_group.project.project_category,
        "project_group_loi": project_group.project_group_loi,
        "panel_reward_points": project_group.panel_reward_points,
        "project_group_cpi": project_group.project_group_cpi,
        "project_group_status": project_group.project_group_status,
        "project_group_language": project_group.project_group_language.id,
        "project_group_country": project_group.project_group_country.id
        }
    req2 = requests.post(settings.SLICK_ROUTER_URL + 'slick/survey/create', json=data)
    return req2


def panel_survey_questions_create_update(project_group):
    panel_source = SupplierOrganisation.objects.get(supplier_type = "4")
    survey_screener_list = ProjectGroupPrescreener.objects.filter(project_group_id=project_group, is_enable = True)

    survey_question_answer_list = []    
    if survey_screener_list.count() > 0:
        # ****************** Check Gender exist or not ***********************

        for survey_screener in survey_screener_list:
            survey_question_answer_list.append(
                {
                    "parent_question_table_id":survey_screener.translated_question_id.id,
                    "internal_question_id" : survey_screener.translated_question_id.Internal_question_id,
                    "translated_question_text":survey_screener.translated_question_id.translated_question_text,
                    "allowedoptions":list(survey_screener.allowedoptions.all().values("translated_answer","internal_answer_id",parent_answer_table_id = F("id")) if survey_screener.allowedoptions.all() else []) ,
                    "allowedRangeMin":survey_screener.allowedRangeMin,
                    "allowedRangeMax":survey_screener.allowedRangeMax,
                    "sequence":survey_screener.sequence,
                    "is_enable":survey_screener.is_enable,
                    "allowed_zipcode_list":survey_screener.allowed_zipcode_list
                }
            )

        # gender_dict = {"Male":1,"Female":2, "Others":3, "Prefer not to answer":4}
        # gender_list = []
        # try:
        #     gender_obj = survey_screener_list.get(translated_question_id__parent_question__parent_question_number = "Gender")
        #     for gen in gender_obj.allowedoptions.all():
        #         if gen.translated_answer in gender_dict:
        #             gender_list.append(gender_dict[gen.translated_answer])
        # except:
        #     gender_list = [1,2,3,4]
        # # ****************** End Check Gender exist or not ***********************
        
        # # ****************** Check Age exist or not ***********************
        # try:
        #     getAge = survey_screener_list.get(translated_question_id__parent_question__parent_question_number = "Age")
        #     min_age = getAge.allowedRangeMin
        #     max_age = getAge.allowedRangeMax
        # except:
        #     min_age = 0
        #     max_age = 0
        # # ****************** End Check Age exist or not ***********************

        # survey_profile = {
        #     "gender": gender_list,
        #     "min_age": min_age,
        #     "max_age": max_age,
        #     "country": project_group.project_group_country.country_code,
        #     "preferred_language": project_group.project_group_language.language_code
        # }
    else:
        pass
        # survey_profile = {
        #     "gender": [1,2,3,4],
        #     "min_age": 18,
        #     "max_age": 99,
        #     "country": project_group.project_group_country.country_code,
        #     "preferred_language": project_group.project_group_language.language_code
        # }
    data = {
        "survey_number": project_group.project_group_number,
        "survey_name": project_group.project_group_name,
        "survey_url": project_group.project_group_surveyurl + '&source='+ str(panel_source.id),
        "survey_category": project_group.project.project_category,
        "survey_loi": project_group.project_group_loi,
        "survey_incidence": project_group.project_group_incidence,
        "survey_reward_points": project_group.panel_reward_points,
        "survey_cpi": project_group.project_group_cpi,
        "survey_status": project_group.project_group_status,
        "allow_duplicate": False,
        "country": project_group.project_group_country.country_code,
        "preferred_language": project_group.project_group_language.language_code,
        "survey_device_type": project_group.project_device_type,
        "survey_profile": survey_question_answer_list,
        }

    return data