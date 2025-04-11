from django.contrib import admin
from Logapp.models import *

# Register your models here.
admin.site.register(EmployeeLoginLog)
admin.site.register(ProjectLog)
admin.site.register(ProjectErrorLog)
admin.site.register(ProjectGroupLog)
admin.site.register(ProjectGroupErrorLog)
admin.site.register(CustomerLog)
admin.site.register(SupplierLog)
admin.site.register(ProjectGroupSupplierLog)
admin.site.register(InvoiceLog)
admin.site.register(ProjectGroupPrescreenerLogs)
admin.site.register(DraftInvoiceLog)
admin.site.register(RespondentDetailErrorLog)
admin.site.register(InvoiceExceptionsLog)
admin.site.register(SupplierInvoiceLogs)
# admin.site.register(SurveyEntryLog)
admin.site.register(RouterException)
admin.site.register(CeleryAPICallLog)
admin.site.register(SupplierEnableDisableLog)

class EmployeeLoginLogAdmin(admin.ModelAdmin):
    search_fields = ('login_by__email','login_by__first_name')

class ProjectLogAdmin(admin.ModelAdmin):
    search_fields = ('project__project_number')

class ProjectGroupLogAdmin(admin.ModelAdmin):
    search_fields = ('projectgroup__client_survey_number','projectgroup__project_group_number')

class SupplierLogAdmin(admin.ModelAdmin):
    search_fields = ('supplier__supplier_name')

class ProjectGroupSupplierLogAdmin(admin.ModelAdmin):
    search_fields = ('projectgroup__project_group_number')

class InvoiceLogAdmin(admin.ModelAdmin):
    search_fields = ('invoice__invoice_number')

class DraftInvoiceLogAdmin(admin.ModelAdmin):
    search_fields = ('draftinvoice','draftinvoice__project__project_number')

class ProjectGroupPrescreenerLogsAdmin(admin.ModelAdmin):
    search_fields = ('projectgroup__project_group_number')

class RespondentDetailErrorLogAdmin(admin.ModelAdmin):
    search_fields = ('projectgroup')

class InvoiceExceptionsLogAdmin(admin.ModelAdmin):
    search_fields = ('invoice__invoice_number')

class SupplierInvoiceLogsAdmin(admin.ModelAdmin):
    search_fields = ('invoiceid','supplier_code')

@admin.register(SurveyEntryLog)
class SurveyEntryLogAdmin(admin.ModelAdmin):
    search_fields = ('glsid',)
    list_display = ('glsid','error_description')

@admin.register(ProjectGroupPanelLog)
class ProjectGroupPanelLogAdmin(admin.ModelAdmin):
    list_display = ('__str__',)


@admin.register(ProjectGroupADPanelLog)
class ProjectGroupADPanelLogAdmin(admin.ModelAdmin):
    list_display = ('__str__',)

@admin.register(ProjectReconciliationLog)
class ProjectReconciliationLogAdmin(admin.ModelAdmin):
    search_fields = ('project__project_number',)
    list_display = ('__str__',)


@admin.register(ProjectSupplierCPIUpdateLog)
class ProjectSupplierCPIUpdateLogAdmin(admin.ModelAdmin):
    search_fields = ('project_number',)
    list_display = ('project_number','project_group_number','source')