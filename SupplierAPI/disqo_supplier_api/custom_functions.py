from django.core.exceptions import ObjectDoesNotExist
from Project.models import *
from Prescreener.models import *
from Surveyentry.models import *
from hashlib import blake2b


def get_project_detail(projectgrp_supp_obj, supplierId):

    project_type_dict = {
        '1': 'AD_HOC',
        '2': 'TRACKING_QUARTERLY',
        '3': 'IHUT',
        '4': 'QUALITATIVE_SCREENING',
        '5': 'Panel Sourcing',
        '6': 'Qual',
        '7': 'IR Check',
        '8': 'Other',
        '9': 'DIARY',
        '10': 'RECONTACT',
        '11': 'WAVE_STUDY'
    }

    device_type_dict = {
        '1': ['DESKTOP', 'PHONE', 'TABLET'],
        '2': ['DESKTOP'],
        '3': ['TABLET'],
        '4': ['PHONE'],
        '5': ['DESKTOP', 'TABLET'],
        '6': ['DESKTOP', 'PHONE'],
        '7': ['TABLET', 'PHONE'],
    }

    studyType = project_type_dict[ projectgrp_supp_obj.project_group.project.project_type ]

    devices = device_type_dict[ projectgrp_supp_obj.project_group.project.project_device_type ]

    url = projectgrp_supp_obj.supplier_survey_url
    redirectUrl = projectgrp_supp_obj.supplier_internal_terminate_redirect_url
    loi = projectgrp_supp_obj.project_group.project_group_loi
    incidence = projectgrp_supp_obj.project_group.project_group_incidence
    completesWanted = projectgrp_supp_obj.completes
    clicksWanted = projectgrp_supp_obj.clicks

    try:
        disqo_api_pricing_obj = DisqoAPIPricing.objects.get(min_loi__lte = loi, max_loi__gte = loi, min_incidence__lte = incidence, max_incidence__gte = incidence).cpi
    except ObjectDoesNotExist:
        disqo_api_pricing_obj = 0

    cpi = disqo_api_pricing_obj
    country_code = projectgrp_supp_obj.project_group.project_group_country.country_code

    dict_payload = {
        "id": projectgrp_supp_obj.project_group.project_group_number,
        "supplierId": supplierId,
        "studyType": studyType,
        "url": url.replace('&PID=%%PID%%', '').replace('&PID=XXXXX', '') + '&api_supplier=disqo',
        "redirectUrl": redirectUrl,
        "loi": loi,
        "conversionRate": incidence,
        "cpi": cpi,
        "completesWanted": completesWanted,
        "qualifications": {},
        "devices": devices,
        "country" : country_code,
        "clicksWanted":clicksWanted,
        "enforceScreenOut":True,
        "trackingField":'CLICKS'
    }

    qualification_qs = ProjectGroupPrescreener.objects.filter(
        project_group_id = projectgrp_supp_obj.project_group,is_enable = True).exclude(translated_question_id__disqo_question_key__exact='')
			
      
    dict1 = {}
    dict1['and'] = []

    for item in qualification_qs:
        if item.translated_question_id.is_active == False:
            disqo_question = list(item.translated_question_id.parent_question.questionsmapping_set.all().values_list('supplier_api_que_key',flat=True))[0]

            
            if disqo_question in ('age'):
                min_ranges = item.allowedRangeMin.split(',')
                max_ranges = item.allowedRangeMax.split(',')
                
                dict1['and'].append(
                        {
                            'range':{
                                'values':[{'gte':age_range[0],'lte':age_range[1]} for age_range in zip(min_ranges,max_ranges)],
                                'question':disqo_question
                            }
                        }
                    )
            elif disqo_question in ('anychildage'):
                disqo_answer = item.allowedoptions.filter(parent_answer__answersmapping__supplier_org = projectgrp_supp_obj.supplier_org).values_list('parent_answer__answersmapping__supplier_api_ans_key', flat=True)
                
                childage = set()
                childgender = set()
                for item in disqo_answer:
                    childage.add(item.split('_')[0])
                    childgender.add(item.split('_')[1])

                dict1['and'].append(
                        {
                            'range':{
                                'values':[{'gte':ans_key,'lte':ans_key} for ans_key in list(childage)],
                                'question':disqo_question
                            }
                        }
                    )
                dict1['and'].append(
                        {
                            'range':{
                                'values':list(childgender),
                                'question':'anychildgender'
                            }
                        }
                    )
            elif disqo_question in ('geopostalcode'):
                ziplist = list(ZipCode.objects.values_list('zip_code', flat=True).filter(project_group_id__project_group_number = projectgrp_supp_obj.project_group.project_group_number))
                if len(ziplist) != 0:
                    dict1['and'].append(
                        {
                            'equals':{
                                'values': ziplist,
                                'question':disqo_question
                            }
                        }
                    )
            else:
                disqo_answer = item.allowedoptions.filter(parent_answer__answersmapping__supplier_org = projectgrp_supp_obj.supplier_org).values_list('parent_answer__answersmapping__supplier_api_ans_key', flat=True)

                if disqo_answer.count() > 0:
                    dict1['and'].append(
                            {
                                'equals':{
                                    'values': list(set(list(disqo_answer))),
                                    'question':disqo_question
                                }
                            }
                        )
        else:
            # If Question From New Mapped Question
            disqo_question = item.translated_question_id.disqo_question_key
            if disqo_question in ('age'):
                min_ranges = item.allowedRangeMin.split(',')
                max_ranges = item.allowedRangeMax.split(',')
                
                dict1['and'].append(
                        {
                            'range':{
                                'values':[{'gte':age_range[0],'lte':age_range[1]} for age_range in zip(min_ranges,max_ranges)],
                                'question':disqo_question
                            }
                        }
                    )
            elif disqo_question in ('geopostalcode'):
                ziplist = item.allowed_zipcode_list
                if len(ziplist) != 0:
                    dict1['and'].append(
                        {
                            'equals':{
                                'values': list(ziplist),
                                'question':disqo_question
                            }
                        }
                    )
            else:
                disqo_answer = item.allowedoptions.values_list('disqo_answer_id', flat=True)
    
                if disqo_answer.count() > 0:
                    dict1['and'].append(
                            {
                                'equals':{
                                    'values': list(filter(None, set(disqo_answer))),
                                    'question':disqo_question
                                }
                            }
                        )
            
    dict_payload.update({'qualifications':dict1})

    return dict_payload


def get_quotas_details(dict_payload):
    dict_payload_2 = {
        "id": "QUOTA-" + dict_payload["id"],
        "completesWanted": dict_payload["completesWanted"],
        "clicksWanted": dict_payload["clicksWanted"],
        "qualifications": dict_payload["qualifications"]
    }

    return dict_payload_2