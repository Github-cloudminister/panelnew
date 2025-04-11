# django imports
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone

# in-project imports
from employee.models import *
from Customer.models import *
from Supplier.models import *


# third-party module imports
from datetime import datetime


class Language(models.Model):

    # Fields
    language_code = models.CharField(max_length=3)
    language_name = models.CharField(max_length=80)

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='language_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='language_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-modified_at',)

    def __str__(self):
        return '{}'.format(self.language_name)


status_choices = (
    # ("Cancel", 'close'),  # Cancel
    # ("Booked", 'edit'),  # Bid
    # ("Live", 'pause'),  # Live
    # ("Paused", 'play'),  # Paused
    # ("Closed", 'stop'),  # Closed
    ("Cancel", 'Cancel'),  # Cancel
    ("Booked", 'Booked'),  # Bid
    ("Live", 'Live'),  # Live
    ("Paused", 'Paused'),  # Paused
    ("Closed", 'Closed'),  # Closed
    ("Reconciled", 'Reconciled'),  # Reconciled
    ("ReadyForAudit", 'ReadyForAudit'),  # ReadyForAudit
    ("ReadyForInvoice", 'ReadyForInvoice'),  # ReadyForInvoice
    ("ReadyForInvoiceApproved", 'ReadyForInvoiceApproved'),  # ReadyForInvoice
    ("Invoiced", 'Invoiced'),  # Invoiced
    ("Archived", 'Archived'),  # Archived
    ("Backup", 'Backup'),  # Archived
)
backup_status_choices = {
    'Pending' : 'Pending',
    'Backup' : 'Backup',
}
device_type = (
        ('1', 'All'),
        ('2', 'Desktop/Laptop Only'),
        ('3', 'Tablet Only'),
        ('4', 'Mobile Only'),
        ('5', 'Dekstop + Tablet'),
        ('6', 'Dekstop + Mobile'),
        ('7', 'Tablet + Mobile'),
        ('8', 'UNKNOWN'),
    )


class Project(models.Model):

    # choices
    project_category = (
        ('1', 'Automotive'),
        ('2', 'Beauty/Cosmetics'),
        ('3', 'Beverages - Alcoholic'),
        ('4', 'Beverages - Non Alcoholic'),
        ('5', 'Education'),
        ('6', 'Electronics/Computer/Software'),
        ('7', 'Entertainment (Movies, Music, TV, Etc)'),
        ('8', 'Fashion/Clothing'),
        ('9', 'Financial Services/Insurance'),
        ('10', 'Food/Snacks'),
        ('11', 'Gambling/Lottery'),
        ('12', 'Healthcare/Pharmaceuticals'),
        ('13', 'Home (Utilities/Appliances, ...)'),
        ('14', 'Home Entertainment (DVD,VHS)'),
        ('15', 'Home Improvement/Real Estate/Construction'),
        ('16', 'IT (Servers,Databases, Etc)'),
        ('17', 'Personal Care/Toiletries'),
        ('18', 'Pets'),
        ('19', 'Politics'),
        ('20', 'Publishing (Newspaper, Magazines, Books)'),
        ('21', 'Restaurants'),
        ('22', 'Sports/Outdoor'),
        ('23', 'Telecommunications (Phone, Cell Phone, Cable)'),
        ('24', 'Tobacco (Smokers)'),
        ('25', 'Toys'),
        ('26', 'Transportation/Shipping'),
        ('27', 'Travel'),
        ('28', 'Websites/Internet/E-Commerce'),
        ('29', 'other'),
        ('30', 'Sensitive Content'),
        ('31', 'Explicit Content'),
        ('32', 'Gaming'),
        ('33', 'HRDM'),
        ('34', 'Job/Career'),
        ('35', 'Shopping'),
        ('36', 'Parenting'),
        ('37', 'Religion'),
        ('38', 'ITDM'),
        ('39', 'Marketing/Advertising'),
        ('40', 'Other - B2B'),
        ('41', 'Ailment'),
        ('42', 'Social Media'),
        ('43', 'SBOs (Small Business Owners)'),
        ('44', 'Engineering'),
        ('45', 'Manufacturing'),
        ('46', 'Retail'),
        ('47', 'Opinion Elites'),
        ('48', 'Retail'),
    )



    project_type = (
        ('1', 'Adhoc'),
        ('2', 'Tracker'),
        ('3', 'IHUT'),
        ('4', 'Community Recruit'),
        ('5', 'Panel Sourcing'),
        ('6', 'Qual'),
        ('7', 'IR Check'),
        ('8', 'Other'),
        ('9', 'Diary'),
        ('10', 'Recontact'),
        ('11', 'Wave Study'),
        ('12', 'Client Supply API Projects'),
        ('13', 'Dummy Project'),

    )
    
    project_redirect_type = (
        ('0', 'Static'),
        ('1', 'Dynamic'),
    )

    project_invoicing_month = (
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    )

    critical_level = (
        ('1','Low'), #Green color in frontend
        ('2','Medium'), #Yellow color in frontend
        ('3','High'), #Red color in frontend
    )

    # Fields
    project_name = models.CharField(max_length=200)
    project_number = models.CharField(max_length=100)
    project_po_number = models.CharField(max_length=100, default='')
    project_category = models.CharField(
        max_length=2, choices=project_category, default='1')
    project_device_type = models.CharField(
        max_length=1, choices=device_type, default='2')
    project_type = models.CharField(
        max_length=2, choices=project_type, default='5')
    project_status = models.CharField(
        max_length=30, choices=status_choices, default="Live")
    project_redirectID = models.CharField(max_length=100)
    project_revenue_month = models.CharField(
        max_length=2, choices=project_invoicing_month, default=datetime.now().month)

    project_revenue_year = models.IntegerField(default=datetime.now().year)

    project_total_revenue = models.BigIntegerField(default=0)
    project_notes = models.TextField()

    # Relationship Fields
    bid = models.ForeignKey('Bid.Bid', on_delete=models.CASCADE,null=True,blank=True)
    project_client_invoicing_contact_person = models.ForeignKey(
        ClientContact, on_delete=models.CASCADE, related_name='invoicing_contact_person')
    project_client_contact_person = models.ForeignKey(
        ClientContact, on_delete=models.CASCADE, related_name='client_contact_person')
    project_manager = models.ForeignKey(
        EmployeeProfile, on_delete=models.PROTECT, related_name='project_manager')
    secondary_project_manager = models.ForeignKey(
        EmployeeProfile, on_delete=models.PROTECT, related_name='secondary_project_manager',null=True,blank=True)
    project_customer = models.ForeignKey(
        CustomerOrganization, on_delete=models.CASCADE)

    project_currency = models.ForeignKey(
        Currency, on_delete=models.CASCADE)
    project_country = models.ManyToManyField(Country, blank=True)
    project_language = models.ManyToManyField(Language, blank=True)
    project_sales_person = models.ForeignKey(
        EmployeeProfile, on_delete=models.PROTECT, related_name='project_sales_person')

    project_redirect_type = models.CharField(max_length=1, choices=project_redirect_type, default="1")

    #Notes for project list
    project_criticality_level = models.CharField(max_length=1, choices=critical_level, blank=True, null=True, default="") 
    project_list_notes = models.TextField(null=True, blank=True)
    
    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='project_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='project_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)
    scrubproject = models.BooleanField(default=False)
    prj_sticky_board = models.BooleanField(default=False)

    ad_scrubproject = models.BooleanField(default=False)  ## Advertozy Sub Supplier Scrub Field

    class Meta:
        # ordering = ('-modified_at',)
        ordering = ('-id',)
        db_table = 'project_project'

    def __str__(self):
        return '{}'.format(self.project_number+'--'+str(self.pk))


def failure_reason_default_list():
    return ["02","03","04","05","06","07","08","09","10","11","12","13","14","15"]


class ProjectGroup(models.Model):

    # choices
    audience_type = (
        ('1', 'B2B'),
        ('2', 'Consumer'),
        ('3', 'Healthcare'),
        ('4', 'Other'),
    )

    # client url type
    client_url_type = (
        ('1', 'Single'),
        ('2', 'Multiple'),
        ('3', 'Recontact'),
    )

    # Fields
    project_group_number = models.CharField(max_length=12, blank=True)
    client_survey_number = models.CharField(max_length=30, blank=True)
    project_group_name = models.CharField(max_length=100)
    project_audience_type = models.CharField(
        max_length=1, choices=audience_type, default='1')
    project_group_status = models.CharField(
        max_length=30, choices=status_choices, default="Live")
    project_group_encodedS_value = models.CharField(max_length=100)
    project_group_encodedR_value = models.CharField(max_length=100)
    project_group_redirectID = models.CharField(max_length=100)

    # URL fields
    project_group_liveurl = models.URLField(max_length=500, null=True, default="") #This is client URL
    project_group_testurl = models.URLField(max_length=500, null=True, default="") #This is client URL
    project_group_surveyurl = models.URLField(max_length=500) # This is internal URL [Source=0]

    # Multiple URLs
    project_group_client_url_type = models.CharField(max_length=10, default="1", choices=client_url_type)

    # Integer fields
    project_group_incidence = models.IntegerField(default=100,
                                                  validators=[
                                                      MaxValueValidator(100),
                                                      MinValueValidator(1)
                                                  ])
    project_group_loi = models.IntegerField(default=1,
                                            validators=[
                                                MaxValueValidator(200),
                                                MinValueValidator(1)
                                            ])
    project_group_completes = models.IntegerField(default=1,
                                                  validators=[
                                                      MinValueValidator(1)
                                                  ])
    project_group_clicks = models.IntegerField(default=0)

    project_group_cpi = models.FloatField(default=0)

    project_group_revenue = models.IntegerField(default=0)
    threat_potential_check = models.BooleanField(default=True)
    threat_potential_score = models.IntegerField(default=30)

    # Date fields
    project_group_startdate = models.DateField(default='')
    project_group_enddate = models.DateField(default='')

    # Json fields
    excluded_project_group = models.JSONField(max_length=1000, blank=True, default = list)

    # boolean fields
    project_group_security_check = models.BooleanField(default=True) 
    project_group_ip_check = models.BooleanField(default=True)
    project_group_pid_check = models.BooleanField(default=True)
    research_defender_oe_check = models.BooleanField(default=True)
    respondent_risk_check = models.BooleanField(default=True)
    failure_check = models.BooleanField(default=True)
    duplicate_check = models.BooleanField(default=True)
    duplicate_score = models.IntegerField(default=80)
    failure_reason = models.JSONField(max_length=10000,default=failure_reason_default_list)
    project_group_allowed_svscore = models.IntegerField(default=0)
    project_group_allowed_dupescore = models.IntegerField(default=0)
    project_group_allowed_fraudscore = models.IntegerField(default=0)
    enable_panel = models.BooleanField(default=False)
    ad_enable_panel = models.BooleanField(default=False)
    show_on_DIY = models.BooleanField(default=True)
    prjgrp_status_setLive_timestamp = models.DateTimeField(default=timezone.now)
    panel_reward_points = models.BigIntegerField(default=0)
    custom_question = models.BooleanField(default=False)
    project_device_type = models.CharField(max_length=1, choices=device_type, default='1')

    # Relationship Fields
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='group_project')
    project_group_country = models.ForeignKey(
        Country, on_delete=models.CASCADE, related_name='group_country')
    project_group_language = models.ForeignKey(
        Language, on_delete=models.CASCADE, related_name='group_language')
    # project_group_exclusion_duplicate_ip = models.ManyToManyField('self', null=True, related_name='project_group_exclusion_duplicate_ip')

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='group_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='group_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-modified_at',)

    def __str__(self):
        return '{}'.format(str(self.project_group_number) + '--' + str(self.project.project_number))



class ProjectGroupSupplier(models.Model):

    # Fields
    completes = models.BigIntegerField(default=0)
    clicks = models.IntegerField(default=0)
    cpi = models.FloatField(default=0)
    supplier_completeurl = models.URLField(max_length=500, null=True, default="", blank = True)
    supplier_terminateurl = models.URLField(max_length=500, null=True, default="", blank = True)
    supplier_quotafullurl = models.URLField(max_length=500, null=True, default="", blank = True)
    supplier_securityterminateurl = models.URLField(max_length=500, null=True, default="", blank = True)
    supplier_postbackurl = models.URLField(max_length=500, null=True, default="", blank = True)
    supplier_survey_url = models.URLField(max_length=500)
    supplier_status = models.CharField(
        max_length=30, choices=status_choices, default="Live")
    theormReachSupplier_survey_id = models.CharField(max_length=300, unique=True, null=True)
    lucidSupplier_survey_id = models.IntegerField(unique=True, null=True)
    # is_hash_url = models.BooleanField(default=False)

    # Fields for API Supplier
    supplier_internal_terminate_redirect_url = models.URLField(max_length=500, null=True, blank=True, default="")
    supplier_terminate_no_project_available = models.URLField(max_length=500, null=True, blank=True, default="")

    # Relationship Fields
    supplier_org = models.ForeignKey(
        SupplierOrganisation, on_delete=models.CASCADE, related_name='supplier_orga')
    project_group = models.ForeignKey(
        ProjectGroup, on_delete=models.CASCADE, related_name='project_group')
    created_from_supplier_dashboard = models.BooleanField(default=False)

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='progrpsupp_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='progrpsupp_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-modified_at',)

    def __str__(self):
        return '{} - {}'.format(self.supplier_org, self.project_group) + self.supplier_status
    

class ProjectGroupSubSupplier(models.Model):

    # Fields
    completes = models.BigIntegerField(default=0)
    clicks = models.IntegerField(default=0)
    cpi = models.FloatField(default=0)
    sub_supplier_completeurl = models.URLField(max_length=500, null=True, default="", blank = True)
    sub_supplier_terminateurl = models.URLField(max_length=500, null=True, default="", blank = True)
    sub_supplier_quotafullurl = models.URLField(max_length=500, null=True, default="", blank = True)
    sub_supplier_securityterminateurl = models.URLField(max_length=500, null=True, default="", blank = True)
    sub_supplier_postbackurl = models.URLField(max_length=500, null=True, default="", blank = True)
    sub_supplier_survey_url = models.URLField(max_length=500)
    sub_supplier_status = models.CharField(max_length=30, choices=status_choices, default="Live")
    theormReachSupplier_survey_id = models.CharField(max_length=300, unique=True, null=True)
    lucidSupplier_survey_id = models.IntegerField(unique=True, null=True)
    # is_hash_url = models.BooleanField(default=False)

    # Fields for API Supplier
    sub_supplier_internal_terminate_redirect_url = models.URLField(max_length=500, null=True, blank=True, default="")
    sub_supplier_terminate_no_project_available = models.URLField(max_length=500, null=True, blank=True, default="")

    # Relationship Fields
    sub_supplier_org = models.ForeignKey(
        SubSupplierOrganisation, on_delete=models.CASCADE, related_name='sub_supplier_orga')
    project_group_supplier = models.ForeignKey(
        ProjectGroupSupplier, on_delete=models.CASCADE, related_name='project_group_supplier_fk')
    project_group = models.ForeignKey(
        ProjectGroup, on_delete=models.CASCADE, related_name='project_groups')
    created_from_supplier_dashboard = models.BooleanField(default=False)

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='progrpsubsupp_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='progrpsubsupp_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-modified_at',)

    def __str__(self):
        return '{} - {}'.format(self.sub_supplier_org, self.project_group) + self.sub_supplier_status




class ZipCode(models.Model):

    zip_code = models.CharField(max_length=20)
    project_group_id = models.ForeignKey(ProjectGroup, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True, editable=False)
    uploaded_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='zip_code_uploadby')
    question_id =  models.ForeignKey('Questions.TranslatedQuestion', on_delete=models.CASCADE,null=True)

class MultipleURL(models.Model):
    
    project_group = models.ForeignKey(ProjectGroup, on_delete=models.CASCADE)
    client_url = models.URLField(max_length=500) #This is client URL
    client_url_id = models.CharField(max_length=255, default="", null=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ('is_used', 'id')


class ProjectGroupStatsCalculations(models.Model):
    project_group = models.OneToOneField(ProjectGroup, on_delete=models.CASCADE)
    total_visits = models.IntegerField(default=0)
    starts = models.IntegerField(default=0)
    internal_terminate = models.IntegerField(default=0)
    incompletes = models.IntegerField(default=0)
    completes = models.IntegerField(default=0)
    terminates = models.IntegerField(default=0)
    quota_full = models.IntegerField(default=0)
    security_terminate = models.IntegerField(default=0)
    complete_rejected_by_client = models.IntegerField(default=0)
    client_rejected = models.IntegerField(default=0)
    expense = models.FloatField(default=0)
    revenue = models.FloatField(default=0)
    incidence = models.FloatField(default=0)
    median_LOI = models.FloatField(default=0)
    margin = models.FloatField(default=0)

class ProjeGroupForceStop(models.Model):
    project_group = models.OneToOneField(ProjectGroup, on_delete=models.CASCADE)
    current_status = models.CharField(max_length=30, choices=status_choices, default="Live")


class ProjectCPIApprovedManager(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    approved_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True)
    created_by = models.DateTimeField(auto_now_add=True, editable=False)


class ProjectGroupPriorityStats(models.Model):
    project_group = models.OneToOneField(ProjectGroup, on_delete=models.CASCADE)
    visits = models.IntegerField(default=0)
    completes = models.IntegerField(default=0)
    internal_conversion = models.IntegerField(default=0)

class ProjectNotesConversation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    notes = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

class ProjectBackup(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    Backup_status = models.CharField(max_length=30, choices=backup_status_choices, default="Pending")