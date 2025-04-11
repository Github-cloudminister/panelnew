from django.test import TestCase

# This API based Script Create For Internal Development/Testing Only

# Need to Set Blow 4 Fields only And run this test.py
BASEURL = 'http://192.168.1.16:8001/'
NumberOfProjectCreate = 100
Token = '0fcba6e2bbf1a0a59b43a60bd43bf9db3963267dbe3fe61bce707e3966e1e62e'
userid = 2



import requests
header = {'Authorization':f'Token {Token}'}
import random,string,concurrent.futures
number = 'abcdxyz'
# Create Company
companyjson = {
    "company_address1": "test company 1 test company 1",
    "company_address2": "test company 1 test company 1",
    "company_cin_number": "ABCD1234",
    "company_city": "Ahmedabad",
    "company_contact_number": "+1234567891",
    "company_country": 244,
    "company_email": "admin@test.com",
    "company_invoice_prefix_international_currency": f"International{''.join(random.choices(string.ascii_uppercase + string.digits, k = 3))}",
    "company_invoice_prefix_local_currency": f"Local{''.join(random.choices(string.ascii_uppercase + string.digits, k = 3))}",
    "company_invoice_suffix_international_currency": "5001",
    "company_invoice_suffix_local_currency": "1001",
    "company_local_currency": 156,
    "company_name": f"test company {number}",
    "company_pan_number": "ABCD12345",
    "company_state": "Gujarat",
    "company_tax_number": "GSTNARENDRAMODIGST",
    "company_zipcode": "12345",
}

createcompanyobj = requests.post(f'{BASEURL}3Mj4eXMf565PoJ/api-route/company-detail-data',json=companyjson, headers=header).json()
# Create Company Bank
companybankjson = {
    "account_number": f"1234567890{number}",
    "account_type": "1",
    "bank_address": "test Address 1234",
    "bank_name": "test bank 1",
    "company_address1": "",
    "company_address2": "",
    "company_cin_number": "",
    "company_city": "",
    "company_contact_number": "",
    "company_country": "",
    "company_details": int(createcompanyobj["id"]),
    "company_email": "",
    "company_iban_number": "ABCD1234",
    "company_name": "",
    "company_pan_number": "",
    "company_routing_number": f"1234{number}",
    "company_state": "",
    "company_tax_number": "",
    "company_website": "",
    "company_zipcode": "",
    "id": "",
    "ifsc_code": "ABCD1234",
    "swift_code": "ABCD1234"
}

createcompanybankobj = requests.post(f'{BASEURL}/3Mj4eXMf565PoJ/api-route/company-invoice-bank-detail',json=companybankjson, headers=header).json()
#Create Supplier
supplierjson = {
    "additional_field": {},
    "max_authorized_cpi": 10,
    "max_completes_on_diy": 10,
    "supplier_address1": "test Address 1",
    "supplier_address2": "test company 1 test company 1",
    "supplier_city": "Ahmedabad",
    "supplier_complete_url": "https://www.slickservices.in?PID=%%PID%%",
    "supplier_country": 244,
    "supplier_internal_terminate_redirect_url": "https://www.slickservices.in?PID=%%PID%%",
    "supplier_name": f"Manual Supplier {number}",
    "supplier_payment_details": "test details 1",
    "supplier_quality_type": "2",
    "supplier_quotafull_url": "https://www.slickservices.in?PID=%%PID%%",
    "supplier_securityterminate_url": "https://www.slickservices.in?PID=%%PID%%",
    "supplier_state": "Gujarat",
    "supplier_terminate_no_project_available": "https://www.slickservices.in?PID=%%PID%%",
    "supplier_terminate_url": "https://www.slickservices.in?PID=%%PID%%",
    "supplier_type": "1",
    "supplier_zip": "12345"
}

suppliercreateobj = requests.post(f'{BASEURL}/3Mj4eXMf565PoJ/api-route/supplier',json=supplierjson, headers=header).json()
#Create Suppplier Contact
suppliercontactjson = {
    "contact_number": "+1234567890",
    "email": "AdminData@gmail.com",
    "first_name": "Admin",
    "last_name": "Data",
    "supplier_id": int(suppliercreateobj['id'])
}

suppliercontactcreateobj = requests.post(f'{BASEURL}/3Mj4eXMf565PoJ/api-route/supplier-contact',json=suppliercontactjson, headers=header).json()
#Create Customer
customercreatejson = {
    "address_1": f"customer {number}",
    "address_2": f"customer {number}",
    "city": "Ahmedabad",
    "company_invoice_bank_detail": int(createcompanybankobj['id']),
    "country": 244,
    "cpi_calculation_method": "1",
    "currency": 156,
    "cust_org_name": f"customer {number}",
    "customer_organization_type": "1",
    "invoice_currency": 156,
    "organization_name": f"customer-{number}/{''.join(random.choices(string.ascii_uppercase + string.digits, k = 5))}",
    "other_details": f"customer {number}",
    "payment_terms": 3,
    "pincode": "12345",
    "sales_person_id": 2,
    "ship_to_address_1": f"customer {number}",
    "ship_to_address_2": f"customer {number}",
    "ship_to_city": "Ahmedabad",
    "ship_to_country": 244,
    "ship_to_pincode": "12345",
    "ship_to_state": "Gujarat",
    "state": "Gujarat",
    "taxVAT_number": "ABCD1234",
    "threat_potential_score": "60",
    "website": "https://supplier.com"
}

customercreateobj = requests.post(f'{BASEURL}/3Mj4eXMf565PoJ/api-route/customer',json=customercreatejson, headers=header).json()
#Create Customer Contact
customercontactjson = {
    "client_contact_number": "+1234567890",
    "client_email": "test@gmail.com",
    "client_firstname": "Admin",
    "client_lastname": "Data",
    "customer_id": int(customercreateobj['id'])
}

customercontactcreateobj = requests.post(f'{BASEURL}/3Mj4eXMf565PoJ/api-route/client-contact',json=customercontactjson, headers=header).json()
    
def AutoDataCreateScript(number):
    #Create Project
    projectcreatejson = {
        "Bid_number": None,
        "id": None,
        "project_category": "1",
        "project_client_contact_person": int(customercontactcreateobj['id']),
        "project_client_invoicing_contact_person": int(customercontactcreateobj['id']),
        "project_currency": 156,
        "project_customer": int(customercreateobj['id']),
        "project_manager": userid,
        "project_name": f"Test Project {number}",
        "project_notes": f"<p>test {number}</p>\n",
        "project_po_number": "1234ABC",
        "project_redirectID": None,
        "project_redirect_type": "0",
        "project_revenue_month": 4,
        "project_revenue_year": 2025,
        "project_sales_person": userid,
        "project_type": "1"
    }
    
    projectcreateobj = requests.post(f'{BASEURL}/3Mj4eXMf565PoJ/api-route/project',json=projectcreatejson, headers=header).json()

    for pg in range(0,5):
        #Create Project
        projectgroupjson = {
            "enable_panel": False,
            "id": None,
            "panel_reward_points": None,
            "project": int(projectcreateobj['id']),
            "project_audience_type": "1",
            "project_device_type": "1",
            "project_group_clicks": 1000,
            "project_group_client_url_type": "1",
            "project_group_completes": 1000,
            "project_group_country": 244,
            "project_group_cpi": 3,
            "project_group_enddate": "2030-12-13",
            "project_group_incidence": 60,
            "project_group_language": 41,
            "project_group_live_url": "https://www.slickservices.in?RID=%%RID%%",
            "project_group_loi": 1,
            "project_group_name": f"Test Survey {pg}",
            "project_group_startdate": "2024-04-28",
            "project_group_status": "Booked",
            "project_group_test_url": "https://www.slickservices.in?RID=%%RID%%",
            "threat_potential_score": 0
        }
        
        projectgroupcreateobj = requests.post(f'{BASEURL}/3Mj4eXMf565PoJ/api-route/project-group',json=projectgroupjson, headers=header).json()
        #Project Group Live
        projectgrouplive = {
            "id" : int(projectgroupcreateobj['id']),
            "project_group_status" : "Live"
        }   

        projectgrouplive = requests.put(
            f'{BASEURL}/3Mj4eXMf565PoJ/api-route/project-group/{projectgroupcreateobj["id"]}/status',json=projectgrouplive, headers=header).json()
        #Project Group Update
        projectgroupupdatejson = {
            "duplicate_check": False,
            "duplicate_score": "0",
            "enable_panel": False,
            "excluded_project_group": [
                projectgroupcreateobj['project_group_number']
            ],
            "failure_check": False,
            "failure_reason": [
                ""
            ],
            "id": int(projectgroupcreateobj['id']),
            "panel_reward_points": None,
            "project": int(projectcreateobj['id']),
            "project_audience_type": "1",
            "project_device_type": "1",
            "project_group_allowed_dupescore": 0,
            "project_group_allowed_fraudscore": 0,
            "project_group_allowed_svscore": 0,
            "project_group_clicks": 1000,
            "project_group_client_url_type": "1",
            "project_group_completes": 1000,
            "project_group_country": 244,
            "project_group_cpi": 1,
            "project_group_enddate": "2030-12-13",
            "project_group_incidence": 60,
            "project_group_ip_check": True,
            "project_group_language": 41,
            "project_group_live_url": "https://www.slickservices.in?RID=%%RID%%",
            "project_group_loi": 1,
            "project_group_name": projectgroupcreateobj['project_group_name'],
            "project_group_number": projectgroupcreateobj['project_group_number'],
            "project_group_pid_check": True,
            "project_group_security_check": False,
            "project_group_startdate": "2024-04-28",
            "project_group_status": "Live",
            "project_group_test_url": "https://www.slickservices.in?RID=%%RID%%",
            "research_defender_oe_check": True,
            "respondent_risk_check": False,
            "show_on_DIY": False,
            "threat_potential_check": False,
            "threat_potential_score": "0"
        }
          
        projectgroupupdateobj = requests.put(
            f'{BASEURL}/3Mj4eXMf565PoJ/api-route/project-group/{int(projectgroupcreateobj["id"])}',json=projectgroupupdatejson, headers=header).json()
        #Supplier Add
        supplierAddJson = {
            "clicks": 100,
            "completes": "100",
            "cpi": 1,
            "projectId": int(projectcreateobj['id']),
            "project_group": int(projectgroupcreateobj['id']),
            "supplier_complete_url": "https://www.slickservices.in?PID=%%PID%%",
            "supplier_internal_terminate_redirect_url": "https://www.slickservices.in?PID=%%PID%%",
            "supplier_org": int(suppliercreateobj['id']),
            "supplier_postback_url": "",
            "supplier_quotafull_url": "https://www.slickservices.in?PID=%%PID%%",
            "supplier_securityterminate_url": "https://www.slickservices.in?PID=%%PID%%",
            "supplier_status": "Live",
            "supplier_terminate_no_project_available": "https://www.slickservices.in?PID=%%PID%%",
            "supplier_terminate_url": "https://www.slickservices.in?PID=%%PID%%"
        }

        requests.post(f'{BASEURL}/3Mj4eXMf565PoJ/api-route/projectgroup-supplier',json=supplierAddJson, headers=header).json()
    
    print(f"------------------Task - {number} Completed-------------")
    
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    yield_results = list(executor.map(AutoDataCreateScript, range(1,NumberOfProjectCreate+1)))