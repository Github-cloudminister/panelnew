from django.contrib import admin
from django.contrib.auth.models import Permission
from CompanyBankDetails.models import CompanyInvoiceBankDetail
from SupplierAPI.models import LucidCountryLanguageMapping
from .models import CustomerOrganization, ClientContact, Currency
from Supplier.models import SupplierOrganisation, SupplierContact
from employee.models import EmployeeProfile
from Project.models import *
from Surveyentry.models import *
from Questions.models import *
from Prescreener.models import *
from Landingpage.models import *
from QuestionSupplierAPI.models import *
from Recontact_Section.models import *
from automated_email_notifications.models import *
from Supplier_Final_Ids_Email.models import SupplierIdsMarks, supplierFinalIdsDeploy
from SupplierInvoice.models import SupplierInvoice, SupplierInvoicePayment, SupplierInvoiceRow
from SupplierInviteOnProject.models import *
from affiliaterouter.models import *
from Invoice.models import DraftInvoiceRow
from scrubsupplierids.models import *

admin.site.register(Permission)
admin.site.register(CompanyInvoiceBankDetail)
admin.site.register(CustomerOrganization)
admin.site.register(ClientContact)
admin.site.register(Currency)
admin.site.register(CustomerOrgAuthKeyDetails)
admin.site.register(SupplierOrganisation)
admin.site.register(SupplierContact)
admin.site.register(SupplierAPIAdditionalfield)
admin.site.register(SubSupplierOrganisation)
admin.site.register(SubSupplierContact)
admin.site.register(EmployeeProfile)
admin.site.register(UserTokenVerifyPasswordReset)
admin.site.register(Country)
admin.site.register(LucidCountryLanguageMapping)
admin.site.register(Language)
admin.site.register(MultipleURL)
admin.site.register(Recontact)
admin.site.register(RespondentReconcilation)
admin.site.register(RespondentDeviceDetail)
admin.site.register(RespondentProjectDetail)
admin.site.register(RespondentPageDetails)
admin.site.register(SurveyEntryWelcomePageContent)
admin.site.register(GEOIPAPItable)
admin.site.register(DisqoQueryParam)
admin.site.register(RespondentRoutingDetail)
admin.site.register(ComputedOnHoldProjectsRespStats)
admin.site.register(respondent_survalidate_detail)
admin.site.register(QuestionCategory)
admin.site.register(ParentQuestion)
admin.site.register(ParentAnswer)
admin.site.register(TranslatedQuestion)
admin.site.register(TranslatedAnswer)
admin.site.register(ProjectGroupPrescreener)
admin.site.register(ZipCode)
admin.site.register(ProjectGroupSupplierPrescreenerEnabled)
admin.site.register(capturePostbackHits)
admin.site.register(SupplierOrgAuthKeyDetails)
admin.site.register(DisqoAPIPricing)
admin.site.register(QuestionsMapping)
admin.site.register(AnswersMapping)
admin.site.register(CounterDetails)
admin.site.register(SupplierIdsMarks)
admin.site.register(supplierFinalIdsDeploy)
admin.site.register(SupplierInvoiceRow)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    search_fields = ('project_number',)

@admin.register(ProjectGroup)
class ProjectGroupAdmin(admin.ModelAdmin):
    search_fields = ('project_group_number', 'project__project_number',)
    list_display = ('__str__', 'enable_panel','ad_enable_panel',)

@admin.register(ProjectGroupSupplier)
class ProjectGroupSupplierAdmin(admin.ModelAdmin):
    search_fields = ('supplier_org__id', 'project_group__project_group_number', 'project_group__project__project_number')
    list_display = ('__str__',)
    list_filter = ('supplier_status',)

@admin.register(ProjectGroupSubSupplier)
class ProjectGroupSubSupplierAdmin(admin.ModelAdmin):
    search_fields = ('sub_supplier_org__id', 'project_group__project_group_number', 'project_group__project__project_number')
    list_display = ('__str__',)
    list_filter = ('sub_supplier_status',)

@admin.register(RespondentDetail)
class RespondentDetailAdmin(admin.ModelAdmin):
    search_fields = ('source', 'project_number', 'project_group_number', 'respondenturldetail__pid', 'respondenturldetail__RID')

@admin.register(RespondentURLDetail)
class RespondentURLDetailAdmin(admin.ModelAdmin):
    search_fields = ('RID',)

@admin.register(RespondentSupplierDetail)
class RespondentSupplierDetailAdmin(admin.ModelAdmin):
    search_fields = ('respondent__source', 'respondent__project_number', 'respondent__project_group_number', 'respondent__respondenturldetail__pid', 'respondent__respondenturldetail__RID')

@admin.register(ProjectGroupPrescreenerDataStore)
class ProjectGroupPrescreenerDataStoreAdmin(admin.ModelAdmin):
    search_fields = ('respondent__source', 'respondent__id', 'respondent__project_number', 'respondent__project_group_number')
    list_filter = ('translated_question_id__parent_question__parent_question_type',)

@admin.register(RespondentDetailsRelationalfield)
class RespondentSupplierDetailAdmin(admin.ModelAdmin):
    search_fields = ('respondent__source', 'respondent__project_number', 'respondent__project_group_number', 'respondent__respondenturldetail__pid', 'respondent__respondenturldetail__RID')

@admin.register(RespondentResearchDefenderDetail)
class ProjectGroupAdmin(admin.ModelAdmin):
    search_fields = ('sy_nr', 'respondent__project_number', 'respondent__source', 'sn_ud',)

@admin.register(ResearchDefenderResponseDetail)
class ProjectGroupAdmin(admin.ModelAdmin):
    search_fields = ('research_defender__sy_nr', 'research_defender__respondent__source', 'research_defender__respondent__project_number', 'research_defender__sn_ud',)

# SupplierInvoice models
@admin.register(SupplierInvoice)
@admin.register(SupplierInvoicePayment)
class ProjectGroupAdmin(admin.ModelAdmin):
    search_fields = ('supplier_org__id', 'supplier_org__supplier_name', 'project__id', 'project__project_number',)

# SupplierInvite models
@admin.register(SupplierInvite)
class ProjectGroupAdmin(admin.ModelAdmin):
    search_fields = ('project__id', 'project__project_number', 'country__country_code', 'country__country_name',)

@admin.register(SupplierInviteDetail)
class ProjectGroupAdmin(admin.ModelAdmin):
    search_fields = ('supplier_org__id', 'supplier_org__supplier_name', 'supplier_contact__supplier_email', 'supplier_invite__project__id', 'supplier_invite__project__project_number',)

# RountingPriority
@admin.register(RountingPriority)
class RountingPriorityAdmin(admin.ModelAdmin):
    search_fields = ('project_group__project_group_name', 'project_group__project_group_number',)

@admin.register(DraftInvoiceRow)
class ProjectGroupSupplierAdmin(admin.ModelAdmin):
    search_fields = ('id', 'project__project_number', 'po_number',)
