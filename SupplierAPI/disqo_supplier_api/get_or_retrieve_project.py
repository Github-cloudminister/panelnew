from rest_framework import status
from rest_framework.response import Response
from QuestionSupplierAPI.models import *
from Project.models import *
from Prescreener.models import *
from Surveyentry.models import *
from SupplierAPI.disqo_supplier_api.custom_functions import *
import requests

def getAuthKeyDetail(projectgrp_supp_obj=None):
    if projectgrp_supp_obj:
        return SupplierOrgAuthKeyDetails.objects.get(supplierOrg=projectgrp_supp_obj.supplier_org)
    else:
        return SupplierOrgAuthKeyDetails.objects.get(supplierOrg__supplier_url_code__in=['disqo','DISQO'])


def get_DisqoAuthKeyHeader(projectgrp_supp_obj=None):
    if projectgrp_supp_obj:
        authkey_obj = getAuthKeyDetail(projectgrp_supp_obj)
    else:
        authkey_obj = getAuthKeyDetail()
        
    headers = {
				'Content-Type': 'application/json',
				'Authorization': authkey_obj.authkey
			}
    return headers

# DisqoAPI Get Projects List function
def DisqoAPIGetProjectsFunc():
    headers = get_DisqoAuthKeyHeader()
    authkey_detail_obj = getAuthKeyDetail()
    supplierId = authkey_detail_obj.supplier_id
    clientId = authkey_detail_obj.client_id
    base_url = authkey_detail_obj.staging_base_url
    

    resp = requests.get(
			f'{base_url}/v1/clients/{clientId}/projects',
			headers=headers)

    if resp.status_code in [200, 201]:
        res_data = resp.json()
        return Response(data=res_data, status=status.HTTP_201_CREATED)
    else:
        return Response(resp.text, status=status.HTTP_400_BAD_REQUEST)


# DisqoAPI Retrieve Project function
def DisqoAPIRetrieveProjectFunc(projectgrp_supp_obj):
    headers = get_DisqoAuthKeyHeader(projectgrp_supp_obj)
    authkey_detail_obj = getAuthKeyDetail(projectgrp_supp_obj)
    supplierId = authkey_detail_obj.supplier_id
    clientId = authkey_detail_obj.client_id
    base_url = authkey_detail_obj.staging_base_url

    resp = requests.get(
				f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}',
				headers=headers)

    if resp.status_code in [200, 201]:
        res_data = resp.json()
        return Response(data=res_data, status=status.HTTP_201_CREATED)
    else:
        return Response(resp.text, status=status.HTTP_400_BAD_REQUEST)