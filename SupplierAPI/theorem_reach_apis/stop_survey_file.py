import hashlib
import json
from django.conf import settings
import requests


# Just For Temporary Testing Purposes for more info check the "third-party-credentials.txt" file from project root directory
# def stop_survey_func(projectgrpsupp_obj):
#     body = json.dumps({"":""}).replace(" ","")

#     secret_key = projectgrpsupp_obj.supplier_org.supplierorgauthkeydetails.secret_key

#     headers = {
#     "Content-Type": "application/json",
#     "X-Api-Key": projectgrpsupp_obj.supplier_org.supplierorgauthkeydetails.api_key
#     }

#     if projectgrpsupp_obj.supplier_org.supplier_url_code == 'theormReach':
#         base_url = f'{projectgrpsupp_obj.supplier_org.supplierorgauthkeydetails.production_base_url}surveys/{projectgrpsupp_obj.theormReachSupplier_survey_id}/pause'

#         secret_url = "{}{}{}".format(base_url, body, secret_key)
#         h = hashlib.sha3_256()
#         h.update(secret_url.encode('utf-8'))
#         hashed_url = "{}?enc={}".format(base_url, h.hexdigest())
#         response = requests.post(hashed_url, headers=headers, data=body)
#         json_response = response.json()
#         return response.status_code
