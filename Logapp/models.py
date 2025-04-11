from django.db import models
from Invoice.models import *
from Prescreener.models import ProjectGroupPrescreener
from Project.models import *
from Supplier.models import *
from SupplierInvoice.models import SupplierInvoice
from affiliaterouter.models import Visitors
from employee.models import * 

class EmployeeLoginLog(models.Model):
    login_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True)
    login_at = models.DateTimeField(auto_now_add=True, editable=False)

class ProjectLog(models.Model):
    created_data =  models.TextField(null=True,blank=True)
    updated_data =  models.TextField(null=True,blank=True)
    status =  models.CharField(max_length=50, null=True)
    project =  models.ForeignKey(Project, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
class ProjectErrorLog(models.Model):
    error_description =  models.TextField(null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class ProjectGroupLog(models.Model):
    created_data =  models.TextField(null=True,blank=True)
    updated_data =  models.TextField(null=True,blank=True)
    status =  models.CharField(max_length=50, null=True)
    projectgroup =  models.ForeignKey(ProjectGroup, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class ProjectGroupErrorLog(models.Model):
    error_description =  models.TextField(null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)


class ProjectGroupPanelLog(models.Model):
    panel_enabled = models.BooleanField(default=False)
    panel_disabled = models.BooleanField(default=False)
    projectgroup =  models.ForeignKey(ProjectGroup, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return self.projectgroup.project_group_number


class ProjectGroupADPanelLog(models.Model):
    adpanel_enabled = models.BooleanField(default=False)
    adpanel_disabled = models.BooleanField(default=False)
    projectgroup =  models.ForeignKey(ProjectGroup, on_delete=models.SET_NULL, null=True,blank=True)
    projectgroupsubsupplier =  models.ForeignKey(ProjectGroupSubSupplier, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return self.projectgroup.project_group_number

class CustomerLog(models.Model):
    created_data =  models.TextField(null=True,blank=True)
    updated_data =  models.TextField(null=True,blank=True)
    customer = models.ForeignKey(CustomerOrganization, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class SupplierLog(models.Model):
    created_data =  models.TextField(null=True,blank=True)
    updated_data =  models.TextField(null=True,blank=True)
    supplier = models.ForeignKey(SupplierOrganisation, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class SupplierEnableDisableLog(models.Model):
    add_enabled = models.CharField(max_length=20,null=True,blank=True)
    remove_enabled = models.CharField(max_length=20,null=True,blank=True)
    supplier = models.ForeignKey(SupplierOrganisation, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class SubSupplierLog(models.Model):
    created_data =  models.TextField(null=True,blank=True)
    updated_data =  models.TextField(null=True,blank=True)
    sub_supplier = models.ForeignKey(SubSupplierOrganisation, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class SubSupplierEnableDisableLog(models.Model):
    add_enabled = models.CharField(max_length=20,null=True,blank=True)
    remove_enabled = models.CharField(max_length=20,null=True,blank=True)
    sub_supplier = models.ForeignKey(SubSupplierOrganisation, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class ProjectGroupSupplierLog(models.Model):
    created_data =  models.TextField(null=True,blank=True)
    updated_data =  models.TextField(null=True,blank=True)
    project_group_supplier =  models.ForeignKey(ProjectGroupSupplier, on_delete=models.SET_NULL, null=True,blank=True)
    supplier =  models.ForeignKey(SupplierOrganisation, on_delete=models.SET_NULL, null=True,blank=True)
    projectgroup =  models.ForeignKey(ProjectGroup, on_delete=models.SET_NULL, null=True,blank=True)
    status =  models.CharField(max_length=50, null=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class InvoiceLog(models.Model):
    created_data =  models.TextField(null=True,blank=True)
    updated_data =  models.TextField(null=True,blank=True)
    status =  models.CharField(max_length=50, null=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class DraftInvoiceLog(models.Model):
    created_data =  models.TextField(null=True,blank=True)
    updated_data =  models.TextField(null=True,blank=True)
    status =  models.CharField(max_length=50, null=True)
    draftinvoice = models.ForeignKey(DraftInvoice, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class ProjectGroupPrescreenerLogs(models.Model):
    add_questions =  models.TextField(null=True,blank=True)
    removed_questions =  models.TextField(null=True,blank=True)
    projectgroup_pescreener =  models.ForeignKey(ProjectGroupPrescreener, on_delete=models.SET_NULL, null=True,blank=True)
    projectgroup =  models.ForeignKey(ProjectGroup, on_delete=models.SET_NULL, null=True,blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class RespondentDetailErrorLog(models.Model):
    question_response = models.TextField(null=True,blank=True)
    PID = models.CharField(max_length=255)
    projectgroup =  models.CharField(max_length=255)
    error_logs = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    
class InvoiceExceptionsLog(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    request_data = models.CharField(max_length=10000, null=True, blank=True)
    exception_raise = models.CharField(max_length=10000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)

class SupplierInvoiceLogs(models.Model):

    created_data =  models.TextField(null=True,blank=True)
    updated_data =  models.TextField(null=True,blank=True)
    supplierinvoice = models.ForeignKey(SupplierInvoice, on_delete=models.SET_NULL,null=True,blank=True)
    supplier_code = models.CharField(max_length=50, default="" ,null=True,blank=True)
    ip_address = models.CharField(max_length=50, default="" ,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class SurveyEntryLog(models.Model):

    error_description = models.TextField(null=True,blank=True)
    glsid = models.CharField(max_length=100, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class RouterException(models.Model):
    visitor = models.ForeignKey(Visitors, on_delete=models.CASCADE)
    detailed_reason = models.CharField(max_length=100000,null=True, blank=True)

class CeleryAPICallLog(models.Model):
    APIname = models.CharField(max_length=250, default="" ,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)


class ProjectReconciliationLog(models.Model):
    project =  models.ForeignKey(Project, on_delete=models.SET_NULL, null=True,blank=True)
    reconciliation = models.BooleanField(default=False)
    error = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        project_no = self.project
        if project_no != None:
            return project_no.project_number
        else:
            return self.error 


class ProjectSupplierCPIUpdateLog(models.Model):
    old_cpi = models.FloatField(default=0)
    new_cpi = models.FloatField(default=0)
    source = models.CharField(max_length=6, default="0")
    project_number = models.CharField(max_length=20, default="")
    project_group_number = models.CharField(max_length=25, default="")
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)