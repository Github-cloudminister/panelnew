# ********** django libraries **************
from django.conf import settings

# ********** in-project imports **************
from Project.models import ProjectGroupSupplier, ProjectGroup
from SupplierAPI.models import *
from SupplierAPI.theorem_reach_apis.custom_functions import get_theorem_survey_details, create_hashed_url, get_theorem_quotas_details, get_theorem_status

# ********** third-party libraries **************
from datetime import datetime, timedelta
import requests,base64,hashlib,json

def update_survey_func(projectgrp_supp_obj):
    secret_key = projectgrp_supp_obj.supplier_org.supplierorgauthkeydetails.secret_key
    theorm_reach_id = projectgrp_supp_obj.theormReachSupplier_survey_id
    base_url = projectgrp_supp_obj.supplier_org.supplierorgauthkeydetails.production_base_url
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": projectgrp_supp_obj.supplier_org.supplierorgauthkeydetails.api_key
    }

    # =============== BEGIN::PUT - Update surveys details in TheoremReach API ===============
    update_survey_url = f'{base_url}surveys/{theorm_reach_id}'
    update_body = get_theorem_survey_details(projectgrp_supp_obj)
    hashed_url = create_hashed_url(update_survey_url, body=update_body, secret_key=secret_key)
    response = requests.put(hashed_url, headers=headers, data=update_body)
    json_response = response.json()
    # =============== END::PUT - Update surveys details in TheoremReach API ===============

    if response.status_code in [200,201]:
        json_response = json_response['data']
        json_response_state = json_response['state']
        theoremreach_survey_id = json_response['id']
        quotas_list = json_response['quotas']

        # projectgrp_supp_obj.theormReachSupplier_survey_id = theoremreach_survey_id
        # projectgrp_supp_obj.save()

        # =============== BEGIN::PUT - Update quotas details in TheoremReach API ===============
        for quotas_dtl in quotas_list:
            update_quotas_url = f"{base_url}quotas/{quotas_dtl['id']}"
            quotas_status = get_theorem_status(projectgrp_supp_obj.supplier_status, name="quotas-status")
            body = get_theorem_quotas_details(projectgrp_supp_obj, state=quotas_status)
            hashed_url = create_hashed_url(update_quotas_url, body=body, secret_key=secret_key)
            response_2 = requests.put(hashed_url, headers=headers, data=body)
            json_response_2 = response_2.json()
            if response_2.status_code not in [200, 201]:
                return {'json_response':json_response_2,'status_code':response_2.status_code}
        # =============== END::PUT - Update quotas details in TheoremReach API ===============

        # =============== BEGIN::Get status ===============
        survey_response_status = get_theorem_status(projectgrp_supp_obj.supplier_status, name="survey-response-status")
        survey_status = get_theorem_status(projectgrp_supp_obj.supplier_status, name="survey-status")
        # =============== END::Get status ===============

        if response.status_code in [200, 201] and survey_response_status != json_response_state:
            # =============== BEGIN::PUT - Update survey status in TheoremReach API ===============
            update_status_url = f"{base_url}surveys/{theoremreach_survey_id}/{survey_status}"
            hashed_url = create_hashed_url(update_status_url, secret_key=secret_key)
            body = {}
            response = requests.post(hashed_url, headers=headers, data=body)
            json_response = response.json()
            # =============== END::PUT - Update survey status in TheoremReach API ===============

    return {'json_response':json_response,'status_code':response.status_code}


def update_theorem_status(projectgrp_supp_obj):
    # =============== BEGIN::Get status ===============
    survey_response_status = get_theorem_status(projectgrp_supp_obj.supplier_status, name="survey-response-status")
    survey_status = get_theorem_status(projectgrp_supp_obj.supplier_status, name="survey-status")
    quotas_status = get_theorem_status(projectgrp_supp_obj.supplier_status,name='quotas-status')
    # =============== END::Get status ===============

    secret_key = projectgrp_supp_obj.supplier_org.supplierorgauthkeydetails.secret_key
    theorm_reach_id = projectgrp_supp_obj.theormReachSupplier_survey_id
    base_url = projectgrp_supp_obj.supplier_org.supplierorgauthkeydetails.production_base_url
    theoremreach_survey_id = projectgrp_supp_obj.theormReachSupplier_survey_id
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": projectgrp_supp_obj.supplier_org.supplierorgauthkeydetails.api_key
    }

    # =============== BEGIN::PUT - Update quotas details in TheoremReach API ===============
    list_quotas_url = f'{base_url}surveys/{theorm_reach_id}/quotas'
    hashed_url = create_hashed_url(list_quotas_url, secret_key=secret_key)
    response = requests.get(hashed_url, headers=headers)
    json_response = response.json()
    if response.status_code in [200, 201]:
        quotas_list = json_response['data']
        for quotas_dtl in quotas_list:
            update_quotas_url = f"{base_url}quotas/{quotas_dtl['id']}"
            quotas_status = get_theorem_status(projectgrp_supp_obj.supplier_status, name="quotas-status")
            body = json.dumps({"state":quotas_status}).replace(" ", "")
            hashed_url = create_hashed_url(update_quotas_url, body=body, secret_key=secret_key)
            response_2 = requests.put(hashed_url, headers=headers, data=body)
            json_response_2 = response_2.json()
            if response_2.status_code not in [200, 201]:
                return {'json_response':json_response_2,'status_code':response_2.status_code}

    # =============== END::PUT - Update quotas details in TheoremReach API ===============

    # =============== BEGIN::PUT - Update survey status in TheoremReach API ===============
    update_status_url = f"{base_url}surveys/{theoremreach_survey_id}/{survey_status}"
    hashed_url = create_hashed_url(update_status_url, secret_key=secret_key)
    body = {}
    response = requests.post(hashed_url, headers=headers, data=body)
    json_response = response.json()
    # =============== END::PUT - Update survey status in TheoremReach API ===============
    return {'json_response':json_response,'status_code':response.status_code}