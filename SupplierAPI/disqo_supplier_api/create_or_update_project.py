from rest_framework import status
from rest_framework.response import Response
from QuestionSupplierAPI.models import *
from Project.models import *
from Prescreener.models import *
from Surveyentry.models import *
from SupplierAPI.disqo_supplier_api.custom_functions import *
import requests

disqo_project_status = {
    "Cancel": "CLOSED",  # Cancel
    "Booked": "HOLD_FOR_USER_INCLUSION_LIST",  # Bid
    "Live": "OPEN",  # Live
    "Paused": "COMPLETED",  # Paused
    "Closed": "COMPLETED",  # Closed
    "Reconciled": "CLOSED",  # Reconciled
    "ReadyForInvoice": "CLOSED",  # Invoiced
    "ReadyForInvoiceApproved": "CLOSED",  # Invoiced
    "Invoiced": "CLOSED",  # Invoiced
    "Archived": "CLOSED",  # Archived
}

disqo_quotas_status = {
    "Cancel": "PAUSED",  # Cancel
    "Booked": "PAUSED",  # Bid
    "Live": "LIVE",  # Live
    "Paused": "PAUSED",  # Paused
    "Closed": "PAUSED",  # Closed
    "Reconciled": "PAUSED",  # Reconciled
    "Invoiced": "PAUSED",  # Invoiced
    "ReadyForInvoice": "PAUSED",  # Invoiced
    "ReadyForInvoiceApproved": "PAUSED",  # Invoiced
    "Archived": "PAUSED",  # Archived
}

# Get AuthKeyDetails
def getAuthKeyDetail(projectgrp_supp_obj):
    return SupplierOrgAuthKeyDetails.objects.get(supplierOrg=projectgrp_supp_obj.supplier_org)

def get_DisqoAuthKeyHeader(projectgrp_supp_obj):
    authkey_obj = getAuthKeyDetail(projectgrp_supp_obj)
    
    headers = {
				'Content-Type': 'application/json',
				'Authorization': authkey_obj.authkey
			}
    return headers

# DisqoAPI Create Project function
def DisqoAPICreateProjectFunc(projectgrp_supp_obj):
    headers = get_DisqoAuthKeyHeader(projectgrp_supp_obj)
    authkey_detail_obj = getAuthKeyDetail(projectgrp_supp_obj)
    supplierId = authkey_detail_obj.supplier_id
    clientId = authkey_detail_obj.client_id
    base_url = authkey_detail_obj.staging_base_url

    # Call function for create payload
    dict_payload = get_project_detail(projectgrp_supp_obj, supplierId)

    projectgrp_supp_obj.cpi = dict_payload['cpi']

    # Don't allow Survey Creation on Disqo's as well as our End if Survey CPI is less than the Supplier CPI
    if dict_payload['cpi'] > projectgrp_supp_obj.project_group.project_group_cpi:
        ProjectGroupSupplier.objects.filter(pk=projectgrp_supp_obj.pk).delete()
        return Response({'detail': 'Supplier CPI is more than the CPI alloted for the Project/Survey'}, status=status.HTTP_400_BAD_REQUEST)

    projectgrp_supp_obj.save()

    # POST - Create project details in Disqo API
    resp = requests.post(
            f'{base_url}/v1/clients/{clientId}/projects',
            json=dict_payload,
            headers=headers
        )

    if resp.status_code in [200, 201]:
        # PUT - Update project status in Disqo API
        resp_2 = requests.put(
            f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}/status',
            json={"status": disqo_project_status[projectgrp_supp_obj.supplier_status]},
            headers=headers
        )

        res_data = resp_2.json()
        dict_payload_2 = get_quotas_details(dict_payload)

        # POST - Create quotas details in Disqo API
        resp_3 = requests.post(
                f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}/quotas',
                json=dict_payload_2,
                headers=headers
            )

        if resp_3.status_code in [200, 201]:
            # PUT - Update quotas status in Disqo API
            quotas_id = dict_payload_2['id']
            resp_4 = requests.put(
                    f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}/quotas/{quotas_id}/status',
                    json={"status": disqo_quotas_status[projectgrp_supp_obj.supplier_status]},
                    headers=headers
                )
            if resp_4.status_code in [200, 201]:
                pass
            else:
                return Response({'detail': 'Project and Quotas created successfully but Quotas status unable to update..!','resp': resp_4.json()}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': 'Project created successfully but Quotas not created..!','resp': resp_3.json()}, status=status.HTTP_400_BAD_REQUEST)
        return Response(data=res_data, status=status.HTTP_201_CREATED)
    else:
        ProjectGroupSupplier.objects.filter(pk=projectgrp_supp_obj.pk).delete()
        return Response({'detail': 'Unable to create project due to cpi mismatch', "resp": resp.json()}, status=status.HTTP_400_BAD_REQUEST)


# DisqoAPI Update Project function
def DisqoAPIUpdateProjectFunc(projectgrp_supp_obj):
    headers = get_DisqoAuthKeyHeader(projectgrp_supp_obj)
    authkey_detail_obj = getAuthKeyDetail(projectgrp_supp_obj)
    supplierId = authkey_detail_obj.supplier_id
    clientId = authkey_detail_obj.client_id
    base_url = authkey_detail_obj.staging_base_url

    # Call function for create payload
    dict_payload = get_project_detail(projectgrp_supp_obj, supplierId)

    projectgrp_supp_obj.cpi = dict_payload['cpi']

    # Don't allow Survey Update on Disqo's as well as our End if Survey CPI is less than the Supplier CPI
    if dict_payload['cpi'] > projectgrp_supp_obj.project_group.project_group_cpi:
        # Pause Survey Status on DIsqo's End
        resp_2 = requests.put(
            f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}/status',
            json={"status": disqo_project_status['Paused']},
            headers=headers
        )
        # Pause Survey's Quotas Status on DIsqo's End
        quotas_id = "QUOTA-" + dict_payload["id"]
        resp_4 = requests.put(
                    f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}/quotas/{quotas_id}/status',
                    json={"status": disqo_quotas_status['Paused']},
                    headers=headers
                )
        return Response({'detail': 'Supplier CPI is more than the CPI alloted for the Project/Survey'}, status=status.HTTP_400_BAD_REQUEST)

    projectgrp_supp_obj.save()

    # PUT - Update project details in Disqo API
    resp = requests.put(
            f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}',
            json=dict_payload,
            headers=headers
        )

    if resp.status_code in [200, 201]:
        # PUT - Update project status in Disqo API
        resp_2 = requests.put(
            f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}/status',
            json={"status": disqo_project_status[projectgrp_supp_obj.supplier_status]},
            headers=headers
        )

        res_data = resp_2.json()
        dict_payload_2 = get_quotas_details(dict_payload)

        # PUT - Update quotas details in Disqo API
        quotas_id = dict_payload_2['id']
        resp_3 = requests.put(
                f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}/quotas/{quotas_id}',
                json=dict_payload_2,
                headers=headers
            )

        if resp_3.status_code in [200, 201]:
            # PUT - Update quotas status in Disqo API
            resp_4 = requests.put(
                    f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}/quotas/{quotas_id}/status',
                    json={"status": disqo_quotas_status[projectgrp_supp_obj.supplier_status]},
                    headers=headers
                )
            if resp_4.status_code in [200, 201]:
                pass
            else:
                return Response({'detail': 'Project and Quotas created successfully but Quotas status unable to update..!','resp': resp_4.json()}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'detail': 'Project created successfully but Quotas not created..!','resp': resp_3.json()}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data=res_data, status=status.HTTP_201_CREATED)
    else:
        return Response({'detail': 'Unable to create project due to cpi mismatch', "resp":resp.json()}, status=status.HTTP_400_BAD_REQUEST)

# DisqoAPI Update Project Status function
def DisqoAPIUpdateProjectStatusFunc(projectgrp_supp_obj):
    headers = get_DisqoAuthKeyHeader(projectgrp_supp_obj)
    authkey_detail_obj = getAuthKeyDetail(projectgrp_supp_obj)
    supplierId = authkey_detail_obj.supplier_id
    clientId = authkey_detail_obj.client_id
    base_url = authkey_detail_obj.staging_base_url

    # Call function for create payload
    dict_payload = {"status": disqo_project_status[projectgrp_supp_obj.supplier_status]}

    # PUT - Update project status in Disqo API
    resp = requests.put(
            f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}/status',
            json=dict_payload,
            headers=headers
        )

    if resp.status_code in [200, 201]:
        res_data = resp.json()

        # PUT - Update quotas status in Disqo API
        quotas_id = "QUOTA-" + str(projectgrp_supp_obj.project_group.project_group_number)
        resp_2 = requests.put(
                f'{base_url}/v1/clients/{clientId}/projects/{projectgrp_supp_obj.project_group.project_group_number}/quotas/{quotas_id}/status',
                json={"status": disqo_quotas_status[projectgrp_supp_obj.supplier_status]},
                headers=headers
            )
        if resp_2.status_code in [200, 201]:
            pass
        else:
            return Response({'detail': 'Project status has been updated successfully but Quotas status has not been updated..!','resp': resp_2.json(), "supplier_status":projectgrp_supp_obj.supplier_status}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Project status has been updated successfully..!', "supplier_status":projectgrp_supp_obj.supplier_status}, status=status.HTTP_200_OK)
    else:
        return Response({'detail': 'Unable to update project status', "resp":resp.json()}, status=status.HTTP_400_BAD_REQUEST)