from django.db import models
from Project.models import ProjectGroup


# Create your models here.
class Recontact(models.Model):
    pid = models.CharField(max_length=100, null=True, default="")
    rid = models.CharField(max_length=50, null=True, default="")
    url = models.URLField(max_length=500, null=True, default="")
    project_group = models.ForeignKey(ProjectGroup, on_delete=models.SET_NULL, null=True, related_name='recontact_project_group')
    is_used = models.BooleanField(default=False)
