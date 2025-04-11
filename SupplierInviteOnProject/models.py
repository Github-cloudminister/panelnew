# django libraties
from django.db import models

# in-project imports
from Project.models import *

# Create your models here.
class SupplierInvite(models.Model):
    project = models.ForeignKey(Project, null=True, on_delete=models.CASCADE)
    incidence = models.IntegerField(default=100,
                                        validators=[
                                            MaxValueValidator(100),
                                            MinValueValidator(1)
                                        ])
    loi = models.IntegerField(default=1,
                                validators=[
                                    MaxValueValidator(200),
                                    MinValueValidator(1)
                                ])
    country = models.ManyToManyField(Country)
    message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class SupplierInviteDetail(models.Model):
    supplier_invite = models.ForeignKey(SupplierInvite, null=True, on_delete=models.CASCADE)
    supplier_org = models.ForeignKey(SupplierOrganisation, null=True, on_delete=models.SET_NULL)
    supplier_contact = models.ManyToManyField(SupplierContact)
    budget = models.FloatField(default=0)
    completes = models.IntegerField(default=0,
                                        validators=[
                                            MinValueValidator(1)
                                        ])