from django.db import models
from Project.models import ProjectGroup, ProjectGroupSupplier


# Create your models here.
class CounterDetails(models.Model):
    project_group = models.ForeignKey(ProjectGroup, null=True, on_delete=models.SET_NULL)
    project_group_supplier = models.ForeignKey(ProjectGroupSupplier, null=True, on_delete=models.SET_NULL)
    project_group_supplier_counter = models.IntegerField(default=0)

# class supplierFinalIdsProjectList()