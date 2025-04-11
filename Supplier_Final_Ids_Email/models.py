from django.db import models
from Project.models import Project
from employee.models import EmployeeProfile
from Supplier.models import SupplierOrganisation

# Create your models here.



class SupplierIdsMarks(models.Model):
    
    status_choices = (
        ("Yes", 'Yes'),
        ("No", 'No'),
        )

    project = models.OneToOneField(Project, on_delete=models.SET_NULL, null=True)
    reconciled_date = models.DateField(auto_now_add=True)
    reconciled_by = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='reconciled_projects')
    scrubbed = models.BooleanField(default=False)
    scrubbed_date = models.DateField(null=True)
    scrubbed_by = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE,related_name='scrubbed_projects', null=True)
    supplier_ids_approval = models.BooleanField(default=False)
    supplier_ids_approval_date = models.DateTimeField(auto_now_add=True, editable=False, null=True)
    supplier_ids_approved_by = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='supplier_ids_approved_by', null=True)
    final_ids_available_by = models.DateField(null=True)
    
    final_ids_sent = models.BooleanField(default = False)
    final_ids_sent_date = models.DateField(null=True)
    final_ids_sent_by = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='final_ids_sent_by', null=True)

    def __str__(self):
        return self.project.project_number



class supplierFinalIdsDeploy(models.Model): # TABLE EXCLUSIVELY FOR SENDING FINAL IDS ASYNCHRONOUSLY
    project_list = models.JSONField(null=True)
    supplier = models.ForeignKey(SupplierOrganisation, on_delete=models.SET_NULL, null=True, default = '')
    project_list_code = models.CharField(max_length=500, default="", null=True)
    final_ids_deployed_by = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='final_ids_deployed_by', null=True)
