from django.db import models

# Create your models here.

class capturePostbackHits(models.Model):
    capturedURL = models.TextField(default="")
    method_name = models.CharField(max_length=100, default ="")