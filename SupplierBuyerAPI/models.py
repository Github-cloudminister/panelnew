from django.db import models
from Project.models import ProjectGroup
from Supplier.models import SubSupplierOrganisation, SupplierOrganisation

# Create your models here.
class SupplierBuyerProjectGroup(models.Model):
    project_group = models.OneToOneField(ProjectGroup, on_delete=models.CASCADE)
    qualification = models.JSONField(default = dict)

class SupplierBuyerAPIModel(models.Model):
    supplier_org_id = models.OneToOneField(SupplierOrganisation, on_delete=models.CASCADE,related_name='supplier_buyer_apid')
    buyer_api_enable = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=255, unique=True)
    request_api_url = models.URLField(max_length=500, blank=True, default="")

class SubSupplierBuyerAPIModel(models.Model):
    sub_supplier_org_id = models.OneToOneField(SubSupplierOrganisation, on_delete=models.CASCADE,related_name='sub_supplier_buyer_apid')
    buyer_api_enable = models.BooleanField(default=False)
    secret_key = models.CharField(max_length=255, unique=True)
    request_api_url = models.URLField(max_length=500, blank=True, default="")