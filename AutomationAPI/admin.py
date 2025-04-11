from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(CeleryRunLog)
admin.site.register(ClientSupplierEnableDisableAPI)
admin.site.register(ClientSupplierFetchSurveysLog)
admin.site.register(ClientSupplierAPIErrorLog)
