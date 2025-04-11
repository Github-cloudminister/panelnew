from django.db import models
from Project.models import *

# Create your models here.
class EmailSubject(models.Model):
    email_subject_line = models.CharField(max_length=255, null=False)

class EmailInvite(models.Model):
    survey_number = models.ForeignKey(ProjectGroup, on_delete=models.CASCADE)
    no_of_invites = models.IntegerField(default=0)
    schedule = models.DateTimeField()
    email_subjectline = models.ForeignKey(EmailSubject, null=True, on_delete=models.SET_NULL)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    update_at = models.DateTimeField(auto_now=True)