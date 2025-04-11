from django.db import models

from employee.models import EmployeeProfile

# Create your models here.



class EmailTemplateData(models.Model):
    template_name = models.CharField(max_length=250)
    subject_line = models.CharField(max_length=250)
    template_body = models.CharField(max_length=15000)

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='email_temp_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='email_temp_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.template_name