# ********** django libraries **************
from django.conf import settings

# ********** in-project imports **************
from Project.models import ProjectGroupSupplier, ProjectGroup
from SupplierAPI.models import *
from SupplierAPI.theorem_reach_apis.custom_functions import get_theorem_survey_details, create_hashed_url, get_theorem_quotas_details, get_theorem_status

# ********** third-party libraries **************
from datetime import datetime, timedelta
import requests,base64,hashlib,json

def create_theormReach_survey_func(projectgrp_supp_obj):
    secret_key = projectgrp_supp_obj.supplier_org.supplierorgauthkeydetails.secret_key
    base_url = projectgrp_supp_obj.supplier_org.supplierorgauthkeydetails.production_base_url
    create_survey_url = f'{base_url}surveys'
    headers = {
    "Content-Type": "application/json",
    "X-Api-Key": projectgrp_supp_obj.supplier_org.supplierorgauthkeydetails.api_key
    }

    # =============== BEGIN::POST - Create survey details in TheoremReach API ===============
    post_body = get_theorem_survey_details(projectgrp_supp_obj)
    hashed_url = create_hashed_url(create_survey_url, body=post_body, secret_key=secret_key)
    response = requests.post(hashed_url, headers=headers, data=post_body)
    json_response = response.json()
    # =============== BEGIN::POST - Create survey details in TheoremReach API ===============

    if response.status_code in [200,201]:
        json_response = json_response['data']
        json_response_state = json_response['state']
        theoremreach_survey_id = json_response['id']

        projectgrp_supp_obj.theormReachSupplier_survey_id = theoremreach_survey_id
        projectgrp_supp_obj.save()

        # =============== BEGIN::POST - Create quotas details in TheoremReach API ===============
        create_quotas_url = f'{base_url}surveys/{theoremreach_survey_id}/quotas'
        quotas_status = get_theorem_status(projectgrp_supp_obj.supplier_status,name='quotas-status')
        body = get_theorem_quotas_details(projectgrp_supp_obj, state=quotas_status)
        hashed_url = create_hashed_url(create_quotas_url, body=body, secret_key=secret_key)
        response = requests.post(hashed_url, headers=headers, data=body)
        json_response = response.json()
        # =============== END::POST - Create quotas details in TheoremReach API ===============

        # =============== BEGIN::Get status ===============
        survey_response_status = get_theorem_status(projectgrp_supp_obj.supplier_status, name="survey-response-status")
        survey_status = get_theorem_status(projectgrp_supp_obj.supplier_status, name="survey-status")
        # =============== END::Get status ===============

        if response.status_code in [200, 201] and survey_response_status != json_response_state:
            # =============== BEGIN::PUT - Update survey status in TheoremReach API ===============
            update_status_url = f"{base_url}surveys/{theoremreach_survey_id}/{survey_status}"
            body = {}
            hashed_url = create_hashed_url(update_status_url, secret_key=secret_key)
            response = requests.post(hashed_url, headers=headers, data=body)
            # =============== END::PUT - Update survey status in TheoremReach API ===============

    return {'json_response':response.json(),'status_code':response.status_code}