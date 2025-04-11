from Supplier.models import SupplierOrganisation
from django.db import models
from Questions.models import *
from django.db.models import Deferrable, UniqueConstraint

# Create your models here.
class QuestionsMapping(models.Model):
    parent_que_id = models.ForeignKey(ParentQuestion, on_delete=models.CASCADE, null=True)
    supplier_org = models.ForeignKey(SupplierOrganisation, on_delete=models.CASCADE, null=True)
    supplier_api_que_key = models.CharField(max_length=85, null=True)
    supplier_api_que_parameter = models.CharField(max_length=85, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['supplier_org', 'parent_que_id'], name="unique_supplier_parent_que")
            ]


class AnswersMapping(models.Model):
    supplier_org = models.ForeignKey(SupplierOrganisation, on_delete=models.CASCADE, null=True)
    parent_ans_id = models.ForeignKey(ParentAnswer, on_delete=models.CASCADE, null=True)
    ques_mapping_id = models.ForeignKey(QuestionsMapping, on_delete=models.CASCADE, null=True)
    supplier_api_ans_key = models.CharField(max_length=85, null=True)
    supplier_api_ans_parameter = models.CharField(max_length=85, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['supplier_org', 'parent_ans_id','ques_mapping_id'], name="unique_supplier_parent_ans")
            ]
