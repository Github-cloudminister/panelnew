from asgiref.sync import sync_to_async
from Logapp.views import *
from Notifications.models import EmployeeNotifications
from Project.models import *
from SupplierAPI.disqo_supplier_api.create_or_update_project import *
from SupplierAPI.theorem_reach_apis.update_survey_file import update_theorem_status
from SupplierAPI.lucid_supplier_api.buyer_surveys import update_lucid_survey
from automated_email_notifications.email_configurations import *
import os
from django.conf import settings


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def update_status(id, status,*args, **kwargs):
    action = kwargs.get('action', None)
    user = kwargs.get('user', None)
    project_group_supplier_obj = []
    sub_supplier = []

    if action == 'change-project-status':

        project_obj = Project.objects.filter(id=id)
        project_obj.update(project_status = status)
        EmployeeNotifications.objects.create(project = project_obj.first(),description = f"Project Number = {project_obj.first().project_number} Status Updated to {status}",created_for = project_obj.first().project_manager,created_by = user)
        project_log('','',status,id,user)

        if status != 'Live':
            project_group_obj = ProjectGroup.objects.filter(project__in=project_obj)

            project_group_supplier_obj = ProjectGroupSupplier.objects.filter(project_group__in=project_group_obj)

            sub_supplier = ProjectGroupSubSupplier.objects.filter(project_group_supplier__in = project_group_supplier_obj, project_group_supplier__supplier_org__supplier_type = "5")
            
            project_group_obj.update(project_group_status = status)
            project_group_supplier_obj.update(supplier_status = status)
            sub_supplier.update(sub_supplier_status = status)
        
        if status == 'Live':
            ProjectGroup.objects.filter(project__in=project_obj,project_group_status = 'Closed').update(project_group_status = 'Paused')
            ProjectGroupSupplier.objects.filter(project_group__project__in=project_obj,supplier_status = 'Closed').update(supplier_status = 'Paused')
            ProjectGroupSubSupplier.objects.filter(project_group__project__in = project_obj,sub_supplier_status = 'Closed').update(sub_supplier_status = 'Paused')

        if status in ['Invoiced','ReadyForInvoice','ReadyForInvoiceApproved','Reconciled']:
            return
        
    elif action == 'change-projectgroup-status':
        project_group_obj = ProjectGroup.objects.filter(id=id)

        Project.objects.filter(id = project_group_obj.first().project.id).update(project_status = 'Live')
        
        project_group_supplier_obj = ProjectGroupSupplier.objects.filter(project_group__in=project_group_obj)

        sub_supplier = ProjectGroupSubSupplier.objects.filter(project_group_supplier__in = project_group_supplier_obj, project_group_supplier__supplier_org__supplier_type = "5")

        project_group_obj.update(project_group_status = status)
        project_group_supplier_obj.update(supplier_status = status)
        sub_supplier.update(sub_supplier_status = status)

        projectgroup_log(f'','',status,project_group_obj.first().id,user)
        project_log(f'status-{status} when ProjectGroup-{project_group_obj.first().project_group_number} Status Updated','',status,project_group_obj.first().project.id,user)
        EmployeeNotifications.objects.create(project = project_group_obj.first().project,project_group = project_group_obj.first(),description = f"Project Group Number = {project_group_obj.first().project_group_number} Status Updated to {status}",created_for = project_group_obj.first().project.project_manager,created_by = user)

        if status in ['Invoiced','ReadyForInvoice','ReadyForInvoiceApproved','Reconciled','Live']:
            return
        
    elif action == 'change-projectgroupsupplier-status':
        supplier = ProjectGroupSupplier.objects.filter(id=id)
        supplier.update(supplier_status = status)
        projectgroupsupplier_log('','',supplier.first(),supplier.first().supplier_org.id,supplier.first().project_group.id,status,user)
        EmployeeNotifications.objects.create(project = supplier.first().project_group.project,description = f"Project Group Supplier = {supplier.first().supplier_org.supplier_name} of Project Group Number = {supplier.first().project_group.project_group_number} Status Updated to {status}",created_for = supplier.first().project_group.project.project_manager,created_by = user)

        if status == 'Live':
            Project.objects.filter(id = supplier.first().project_group.project.id).update(project_status = 'Live')
            ProjectGroup.objects.filter(id = supplier.first().project_group.id).update(project_group_status = 'Live')

            project_log(f'status-{status} when ProjectGroupSupplier-{supplier.first().supplier_org} Status Updated','',status,supplier.first().project_group.project.id,user)
            projectgroup_log(f'status-{status} when ProjectGroupSupplier-{supplier.first().supplier_org} Status Updated','',status,supplier.first().project_group.id,user)
        else:
            sub_supplier = ProjectGroupSubSupplier.objects.filter(project_group_supplier__in = supplier, project_group_supplier__supplier_org__supplier_type = "5")
            sub_supplier.update(sub_supplier_status = status)

        if status in ['Invoiced','ReadyForInvoice','ReadyForInvoiceApproved','Reconciled']:
            return
    

    if action in ['change-project-status','change-projectgroup-status', 'change-projectgroupsupplier-status']:

        for project_group_supplier in project_group_supplier_obj:

            if project_group_supplier.supplier_org.supplier_url_code == 'lucid':
                update_lucid_survey(project_group_supplier)
            if project_group_supplier.supplier_org.supplier_url_code in ["disqo", "Disqo"]:
                DisqoAPIUpdateProjectStatusFunc(project_group_supplier)
            if project_group_supplier.supplier_org.supplier_url_code in ["theormReach"]:
                update_theorem_status(project_group_supplier)
    return "Success"