# ******** Django Libraris ********
from django.template.loader import render_to_string
from django.db.models import *

# in-project imports
from Surveyentry.models import RespondentDetail
from Supplier_Final_Ids_Email.models import SupplierIdsMarks
from SupplierInvoice.models import *

# automated email notifications imports
from automated_email_notifications.email_configurations import *
from django.conf import settings

def SupplierFinalIdsBySupplierSendEmail(**kwargs):
   
    project_numbers = kwargs.get('project_number_list', None)
    project_number_list = project_numbers.split(',') if type(project_numbers) == str else project_numbers
    supplier_id_list = kwargs.get('supplier_id_list', None)
    final_ids_sent_by = kwargs.get('final_ids_sent_by', None)

    if supplier_id_list:
        ProjectGroupSupplier_obj = ProjectGroupSupplier.objects.filter(project_group__project__project_number__in = project_number_list, supplier_org__id__in=supplier_id_list,project_group__project__project_status__in=["Invoiced"])
    
    else:
        ProjectGroupSupplier_obj = ProjectGroupSupplier.objects.filter(project_group__project__project_number__in = project_number_list, project_group__project__project_status__in=["Invoiced"])

    supplier_list = list(ProjectGroupSupplier_obj.values_list('supplier_org', flat=True))
    project_number_list_2 = list(ProjectGroupSupplier_obj.values_list('project_group__project__project_number', flat=True))

    _table_data = RespondentDetail.objects.filter(project_number__in = project_number_list_2, url_type='Live', resp_status = 4,source__in = supplier_list).values('source', 'project_number', 'supplier_cpi', 'respondentdetailsrelationalfield__project').annotate(completes=Count('project_number')).order_by('source')    

    parameter_table_data = []
    for ta in _table_data:
        parameter_table_data.append(ta)
        sup = SupplierOrganisation.objects.get(id = ta['source'])
        proj = Project.objects.get(id = ta['respondentdetailsrelationalfield__project'])
        supplierinvoicerow_obj, created = SupplierInvoiceRow.objects.get_or_create(supplier_org=sup, project=proj, cpi = ta['supplier_cpi'])
    
    for supplier in supplier_list:
        sup = SupplierOrganisation.objects.get(id =supplier)
        supplier_email_list = list(SupplierContact.objects.filter(supplier_id__id=supplier, send_final_ids=True).values_list('supplier_email',flat=True).order_by().distinct('supplier_email'))

        URL = f"{settings.SUPPLIER_DASHBOARD_URL}ictXUesVWsi7cKcq30A1XLDkA4w813LuqLph3QpV5W3jFdydmBYi5B?s={sup.supplier_code}&p={project_number_list}"
        html_message = render_to_string('supplier_final_ids_email/supplier_final_ids_email_send.html',{'downloadidsurl':URL,'resp_relationsfield_list':_table_data})
        to_emails = supplier_email_list
        if settings.SERVER_TYPE == 'production':
            cc_emails = 'projectmanagement@panelviewpoint.com'
        else:
            cc_emails = 'tech@panelviewpoint.com'
        subject = f'Final Ids - PANEL VIEWPOINT: {timezone.now().date()}- {sup.supplier_name}'
        sendEmail = sendEmailSendgripAPIIntegration(from_email = ('finalids@panelviewpoint.com', 'Final IDs'),to_emails=to_emails, subject=subject, html_message=html_message, cc_emails = cc_emails)

        email_sent_successfully = True

        if email_sent_successfully:
            supplier_sent_status = True
        else:
            supplier_sent_status = False

        try:
            supplier_data, supplieridsmark_created = SupplierIdsMarks.objects.update_or_create(project=project_number_list,
            defaults={'final_ids_sent': supplier_sent_status, 'final_ids_sent_date':timezone.now().date(), 'final_ids_sent_by':final_ids_sent_by})
        except:
            pass
 

    return 'Please raise!'
  

def ProjectClosureZeroCompletesNotificationEmailSend(project_number_list):
    # ========== BEGIN::Commented by Bhautik at 22-03-2022 ==========
    project_list_obj = Project.objects.filter(project_number__in = project_number_list, project_status__in = ['Reconciled','ReadyForInvoice','ReadyForInvoiceApproved','Invoiced'])

    if project_list_obj.exists():

        for project_obj in project_list_obj:
            project_number = project_obj.project_number

            progrp_supp_list = ProjectGroupSupplier.objects.filter(project_group__project=project_obj).values_list('supplier_org__id', flat=True)


            resp_source_list = RespondentDetail.objects.filter(project_number=project_number, url_type="Live", resp_status="4")
            excluded_progrp_supp_list = progrp_supp_list.exclude(supplier_org__id__in = list(resp_source_list.values_list('source', flat=True))).order_by('supplier_org__id').distinct('supplier_org__id')


            _table_data = resp_source_list.values('source', 'project_number', 'supplier_cpi', 'respondentdetailsrelationalfield__project').annotate(completes=Count('project_number')).order_by('source')
            for rowdata in _table_data:
                if int(rowdata['source']) > 0:
                    supplier_obj = SupplierOrganisation.objects.get(id=rowdata['source'])
                    if SupplierInvoiceRow.objects.filter(supplier_org = supplier_obj,project = project_obj,cpi = rowdata['supplier_cpi']).exists():
                        continue
                    else:
                        # if 
                        SupplierInvoiceRow.objects.create(
                            supplier_org = supplier_obj,
                            project = project_obj,                
                            cpi = rowdata['supplier_cpi'],
                            completes = rowdata['completes']
                        )
                else:
                    continue

            # for supplier_org_id in list(excluded_progrp_supp_list):
            #     supplier_email_list = list(SupplierContact.objects.values_list('supplier_email',flat=True).filter(supplier_id=supplier_org_id, send_final_ids=True).order_by().distinct())
            #     supplier_obj = SupplierOrganisation.objects.get(id=supplier_org_id)
            #     supplier_names = supplier_obj.supplier_name
                
                
            #     # ************ BEGIN:: Send data to email-template, read csv and attach csv to email and send email using SendGrid ************
            #     html_message = render_to_string('supplier_final_ids_email/zero_completes_supplier_final_ids_email_send.html', {})
                
            #     to_emails = supplier_email_list
            #     subject = f'Project Closer Notification: {project_number} || {supplier_names}'
            #     if settings.SERVER_TYPE == 'production':
            #         cc_emails = 'finalids@panelviewpoint.com'
            #     else:
            #         cc_emails = 'pythonteam@slickservices.in'

            #     sendEmail = sendEmailSendgripAPIIntegration(to_emails=to_emails, subject=subject, html_message=html_message, cc_emails = cc_emails, proj_manager_cc_email=project_obj.project_manager.email)
        return 'Zero Completes Final ids sent successfully'
    else:
        return 'Project is not reconciled yet.'