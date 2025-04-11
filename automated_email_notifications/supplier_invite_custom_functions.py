# ******** Django libraris ********
from django.db.models import Count, Q, F
from django.conf import settings
from django.template.loader import render_to_string

# in-project imports
from Project.models import *
from SupplierInviteOnProject.models import *
from Surveyentry.custom_function import get_object_or_none

# automated email notifications imports
from Surveyentry.models import RespondentDetail
from automated_email_notifications.email_configurations import *

# third-party libraries
import json

def sendSupplierInviteOnProject(*args,**kwargs):
    project_number = kwargs['project_number']
    data = kwargs['data']
    incidence = data.get('incidence', '')
    loi = data.get('loi', '')
    country_list = data.get('country', '')
    message = data.get('message', '')

    project_obj = Project.objects.get(project_number=project_number)
    country_qs = Country.objects.filter(id__in=country_list)
    country_names = country_qs.values_list('country_name',flat=True)
        
    supp_invite_obj = SupplierInvite.objects.create(project=project_obj,  incidence=incidence, loi=loi, message=message)
    supp_invite_obj.country.set(country_qs)

    for supplier_invite in data['supplier_invite_detail']:
        supplier_org = supplier_invite.get('supplier_org', '')
        supplier_contact = supplier_invite.get('supplier_contact', '')
        budget = supplier_invite.get('budget', '')
        completes = supplier_invite.get('completes', '')
        supplier_org_obj = SupplierOrganisation.objects.get(id = supplier_org)
        supplier_contact_list = SupplierContact.objects.filter(supplier_id=supplier_org_obj, id__in=supplier_contact.split(','), send_supplier_updates=True)
        supplier_contact_email_list = list(supplier_contact_list.values_list('supplier_email',flat=True))
        supp_invite_dtl_obj = SupplierInviteDetail.objects.create(supplier_invite=supp_invite_obj, supplier_org=supplier_org_obj, budget=budget, completes=completes)
        supp_invite_dtl_obj.supplier_contact.set(supplier_contact_list)

        # ****************************************
        # START::Send Email on Project Accept
        # ****************************************
        html_message = render_to_string('SupplierInviteOnProject/emailtemplates/emailinvitation.html',{
            'supplier_name':supplier_org_obj.supplier_name,
            'project_name': project_obj.project_name,
            'project_number': project_obj.project_number,
            'ir': incidence,
            'loi': loi,
            'complete': completes,
            'cpi': budget,
            'message': message,
            'country_list':country_names,
            })

        from_email = 'supply@panelviewpoint.com'
        to_emails = supplier_contact_email_list
        subject=f'RFQ || {project_obj.project_number} | {supplier_org_obj.supplier_name}'

        if settings.SERVER_TYPE == 'production':
            cc_emails = 'projects@panelviewpoint.com'
        else:
            cc_emails = 'tech@panelviewpoint.com'

        sendEmailSendgripAPIIntegration(from_email=from_email,to_emails=to_emails, subject=subject, html_message=html_message, cc_emails = cc_emails, proj_manager_cc_email=project_obj.project_manager.email)
        # ****************************************
        # END::Send Email on Project Accept
        # ****************************************

    return 'Supplier Invite on project sent successfully..!'


def sendSupplierSuppliersMidfieldUpdate(project_group_number, *args,**kwargs):
    supplier_org_id = kwargs['supplier_midfield_dict']['supplier_org']
    supplier_contacts = kwargs['supplier_midfield_dict']['supplier_contacts']
    notes = kwargs['supplier_midfield_dict']['notes']
    project_number = kwargs.get('project_number')
    project_manager_email = kwargs.get('project_manager_email')
    
    supplier_org_obj = get_object_or_none(SupplierOrganisation, id=supplier_org_id)
    if supplier_org_obj != None:
        supplier_name = supplier_org_obj.supplier_name
    else:
        supplier_name = ''
    supplier_contact_list = SupplierContact.objects.filter(supplier_id=supplier_org_id, id__in=supplier_contacts, send_supplier_updates=True)
    supplier_contact_email_list = list(supplier_contact_list.values_list('supplier_email', flat=True))

    resp_stats_supplierWise = RespondentDetail.objects.filter(source=supplier_org_id, project_group_number=project_group_number, url_type='Live').values(progrp_supp_id=F('respondentdetailsrelationalfield__project_group_supplier_id')).annotate(
        completes=Count('id', filter=Q(resp_status='4')), 
        visits=Count('id'), 
        incompletes=Count('id',filter=Q(resp_status='3')), 
        terminates=Count('resp_status',filter=Q(resp_status='5')),
        quota_full=Count('resp_status',filter=Q(resp_status='6')), 
        security_terminate=Count('resp_status',filter=Q(resp_status='7')), 
        supplier_completes=F('respondentdetailsrelationalfield__project_group_supplier__completes'), 
        supplier_clicks=F('respondentdetailsrelationalfield__project_group_supplier__clicks'), supplier_cpi=F('respondentdetailsrelationalfield__project_group_supplier__cpi')
        )
    if resp_stats_supplierWise.count() == 0:
        resp_stats_supplierWise = [{
            'completes': 0, 
            'visits': 0, 
            'incompletes': 0, 
            'terminates': 0, 
            'quota_full': 0, 
            'security_terminate': 0, 
            'supplier_completes': 0, 
            'supplier_clicks': 0, 
            'supplier_cpi': 0
        }]

    html_message = render_to_string('SupplierInviteOnProject/email_midfield_update.html', {
        'message': notes,
        'prjgrpsupplier_stats': resp_stats_supplierWise,
    })

    from_email = 'supply@panelviewpoint.com'
    to_emails = supplier_contact_email_list
    subject=f'RFQ || {project_number} || {project_group_number} || {supplier_name}'

    if settings.SERVER_TYPE == 'production':
        cc_emails = 'projects@panelviewpoint.com'
    else:
        cc_emails = 'tech@panelviewpoint.com'

    send_email_func = sendEmailSendgripAPIIntegration(from_email=from_email,to_emails=to_emails, subject=subject, html_message=html_message, cc_emails = cc_emails, proj_manager_cc_email=project_manager_email)

    if send_email_func.status_code in [200, 201]:
        return 'Supplier Midfield Updates sent successfully..!'
    return json.loads(send_email_func.content)
