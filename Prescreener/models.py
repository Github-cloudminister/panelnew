from django.db import models

from Project.models import ProjectGroup, ProjectGroupSupplier
from Questions.models import TranslatedQuestion, TranslatedAnswer
from employee.models import EmployeeProfile


class ProjectGroupPrescreener(models.Model):

    # Fields
    project_group_id = models.ForeignKey(ProjectGroup, on_delete=models.CASCADE)
    translated_question_id = models.ForeignKey(TranslatedQuestion, on_delete = models.CASCADE)
    allowedoptions = models.ManyToManyField(TranslatedAnswer, blank=True)
    allowedRangeMin = models.CharField(max_length=100, default="0")
    allowedRangeMax = models.CharField(max_length=100, default="100")
    sequence = models.IntegerField(default=1)
    is_enable = models.BooleanField(default=True)
    allowed_zipcode_list = models.JSONField(max_length=1000000, default=list)
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='prescreener_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='prescreener_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('sequence',)

    def __str__(self):
        return "{}--{}".format(self.project_group_id.project_group_name, self.translated_question_id.translated_question_text)

class ProjectGroupSupplierPrescreenerEnabled(models.Model):

    prj_grp_supplier = models.ForeignKey(ProjectGroupSupplier, on_delete=models.CASCADE, related_name='prj_grp_supp_prscrner_enable')
    prj_grp_prescreener = models.ForeignKey(ProjectGroupPrescreener, on_delete = models.CASCADE, related_name='prj_grp_supp_prscrner_enable')