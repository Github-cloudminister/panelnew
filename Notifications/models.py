from django.db import models

from Project.models import Project, ProjectGroup
from employee.models import EmployeeProfile

# Create your models here.
class EmployeeNotifications(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True,blank=True)
    project_group = models.ForeignKey(ProjectGroup, on_delete=models.SET_NULL, null=True,blank=True)
    description = models.CharField(max_length=1000000,null=True,blank=True)
    is_viewed = models.BooleanField(default=False,null=True,blank=True)
    viewed_at = models.DateTimeField(null=True,blank=True)
    
    created_for = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL,null=True,blank=True, related_name='employee_notifications_created_for')
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL,null=True,blank=True, related_name='employee_notifications_created_by')
    created_at = models.DateTimeField(auto_now_add=True)