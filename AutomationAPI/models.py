from django.db import models

# Create your models here.
class ClientSupplierAPIErrorLog(models.Model):
    inputdata = models.TextField()
    client_name = models.CharField(max_length=50,null=True,blank=True)
    line_number = models.CharField(max_length=50,null=True,blank=True)
    error_details = models.CharField(max_length=5000,null=True,blank=True)
    project_group_number = models.CharField(max_length=250,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CeleryRunLog(models.Model):
    taskname = models.CharField(max_length=50,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class ClientSupplierFetchSurveysLog(models.Model):
    clientname = (
        ('toluna', 'toluna'),
        ('zamplia', 'zamplia'),
        ('sago', 'sago')
    )
    client_name = models.CharField(max_length=50, choices=clientname)
    total_surveys_fetch = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

class ClientSupplierEnableDisableAPI(models.Model):
    clientname = (
        ('toluna', 'toluna'),
        ('zamplia', 'zamplia'),
        ('sago', 'sago')
    )
    client_name = models.CharField(max_length=50, choices=clientname)
    is_enable = models.BooleanField(default = True)


class OpinionsDealErrorLog(models.Model):
    inputdata = models.TextField()
    client_name = models.CharField(max_length=50,null=True,blank=True)
    line_number = models.CharField(max_length=50,null=True,blank=True)
    error_details = models.CharField(max_length=1000,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)