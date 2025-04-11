# ********** django libraries **************
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import *

# ********** in-project imports **************
from Prescreener.models import ProjectGroupPrescreener
from QuestionSupplierAPI.models import *
from Project.models import ZipCode

# ********** third-party libraries **************
import json, hashlib
from datetime import datetime

def get_theorem_survey_details(projectgrp_supp_obj):
    return json.dumps({
        "name":projectgrp_supp_obj.project_group.project_group_number+'-API', 
        "entry_url_prod":projectgrp_supp_obj.supplier_survey_url+'&transaction_id={transaction_id}',
        "entry_url_test":projectgrp_supp_obj.supplier_survey_url+'&transaction_id={transaction_id}',
        "estimated_length_of_interview":projectgrp_supp_obj.project_group.project_group_loi,
        "estimated_conversion_rate":projectgrp_supp_obj.project_group.project_group_incidence,
        "cpi":round(projectgrp_supp_obj.cpi, 2),
        "max_authorized_cpi":round(projectgrp_supp_obj.cpi, 2),
        "start_at":datetime.strftime(projectgrp_supp_obj.project_group.project_group_startdate, "%Y-%m-%dT%H:%M:%SZ"),
        "end_at":datetime.strftime(projectgrp_supp_obj.project_group.project_group_enddate, "%Y-%m-%dT%H:%M:%SZ"),
        "country_id": projectgrp_supp_obj.project_group.project_group_country.theorem_country_id
        }).replace(" ","").replace("http://", "https://")

def create_hashed_url(survey_url, body=None, secret_key=None):
    if body == None:
        secret_url = "{}{}".format(survey_url, secret_key)
    else:
        secret_url = "{}{}{}".format(survey_url, body, secret_key)
    h = hashlib.sha3_256()
    h.update(secret_url.encode('utf-8'))
    if "?" in survey_url:
        hashed_url = "{}&enc={}".format(survey_url, h.hexdigest())
    else:
        hashed_url = "{}?enc={}".format(survey_url, h.hexdigest())
    return hashed_url

def get_theorem_quotas_details(projectgrp_supp_obj, state="inactive"):
    qualification_qs = ProjectGroupPrescreener.objects.filter(project_group_id = projectgrp_supp_obj.project_group, is_enable = True,translated_question_id__parent_question__questionsmapping__in=QuestionsMapping.objects.filter(supplier_org=projectgrp_supp_obj.supplier_org))
			
    questions_list = []

    for item in qualification_qs:
        dict1 = {}
        disqo_question = list(item.translated_question_id.parent_question.questionsmapping_set.all().values_list('supplier_api_que_key',flat=True))[0]

        if disqo_question in ('1','Age'):
            min_ranges = item.allowedRangeMin.split(',')
            max_ranges = item.allowedRangeMax.split(',')

            age_list = []
            for age_range in zip(min_ranges, max_ranges):
                for i in range(int(age_range[0]), int(age_range[1]) + 1):
                    age_list.append(i)
            
            questions_list.append(
                    {
                        'answer_ids':age_list,
                        'question_id':disqo_question
                    }
                )
        elif disqo_question in ('3', 'Zip'):
            ziplist = ZipCode.objects.values_list('zip_code', flat=True).filter(project_group_id__project_group_number = projectgrp_supp_obj.project_group.project_group_number)
            
            questions_list.append(
                {
                    'postal_codes': list(ziplist),
                    'question_id':disqo_question
                }
            )
        else:
            disqo_answer = item.allowedoptions.filter(parent_answer__answersmapping__supplier_org = projectgrp_supp_obj.supplier_org).values_list('parent_answer__answersmapping__supplier_api_ans_key', flat=True)

            if disqo_answer.count() > 0:
                questions_list.append(
                        {
                            'answer_ids': list(set(list(disqo_answer))),
                            'question_id':disqo_question
                        }
                    )

    return json.dumps({
            "name":f"{projectgrp_supp_obj.project_group.project_group_number}-Quota",
            "target_completes":projectgrp_supp_obj.completes,
            "state":state,
            "questions":questions_list,
        }).replace(" ","").replace("http://", "https://")

def get_theorem_status(status, name=None):
    theorem_survey_status = {
        "Cancel": "complete",  # Cancel
        "Booked": "draft",  # Bid
        "Live": "start",  # Live
        "Paused": "pause",  # Paused
        "Closed": "complete",  # Closed
        "Reconciled": "complete",  # Reconciled
        "Invoiced": "complete",  # Invoiced
        "Archived": "complete",  # Archived
    }

    theorem_survey_response_status = {
        "Cancel": "completed",  # Cancel
        "Booked": "draft",  # Bid
        "Live": "running",  # Live
        "Paused": "paused",  # Paused
        "Closed": "completed",  # Closed
        "Reconciled": "completed",  # Reconciled
        "Invoiced": "completed",  # Invoiced
        "Archived": "completed",  # Archived
    }

    theorem_quotas_status = {
        "Cancel": "inactive",  # Cancel
        "Booked": "inactive",  # Bid
        "Live": "active",  # Live
        "Paused": "inactive",  # Paused
        "Closed": "inactive",  # Closed
        "Reconciled": "inactive",  # Reconciled
        "Invoiced": "inactive",  # Invoiced
        "Archived": "inactive",  # Archived
    }
    if name.lower() == 'survey-status':
        return theorem_survey_status[status]
    elif name.lower() == 'survey-response-status':
        return theorem_survey_response_status[status]
    else:
        return theorem_quotas_status[status]
