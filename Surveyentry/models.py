from django.db.models.fields import BooleanField
from django.utils import tree
from Prescreener.models import ProjectGroupPrescreener
from Supplier.models import SupplierOrganisation
from django.contrib.auth.models import update_last_login
from django.db import models
import datetime,json
from django.utils.translation import gettext as _
from affiliaterouter.models import VisitorSurveyRedirect
from employee.models import EmployeeProfile
from Project.models import ProjectGroup, Language, Project, ProjectGroupSubSupplier, ProjectGroupSupplier
from employee.models import Country
from Questions.models import TranslatedQuestion, TranslatedAnswer
from employee.models import Country
from django.utils import timezone



status_choices = (
    ("Cancel", 'Cancel'),  # Cancel
    ("Booked", 'Booked'),  # Bid
    ("Live", 'Live'),  # Live
    ("Paused", 'Paused'),  # Paused
    ("Closed", 'Closed'),  # Closed
    ("Reconciled", 'Reconciled'),  # Reconciled
    ("ReadyForInvoice", 'ReadyForInvoice'),  # ReadyForInvoice
    ("ReadyForInvoiceApproved", 'ReadyForInvoiceApproved'),  # ReadyForInvoice
    ("Invoiced", 'Invoiced'),  # Invoiced
    ("Archived", 'Archived'),  # Archived
)

respondent_status = (
    ("1", "Visit"),  # Hit our page
    ("2", "Internal Terminate"),  # Hit our page
    ("3", "Incomplete"),  # Redirected towards client side
    ("4", "Complete"),
    ("5", "Terminate"),
    ("6", "Quotafull"),
    ("7", "Security Terminate"),
    ("8", "Complete Rejected by client"), #Client Rejected at Reconciliation Time
    ("9", "Client Rejected")  #PVP Rejected Scrub Time
)

url_choices = (
    ("Live", "Live"),
    ("Test", "Test"),
)

us_choices = (
    ("1", "Manual"),
    ("2", "Router"),
    ("3", "ReRouter"),
    ("4", "SupplierBuyer"),
    ("5", "SubSupplierBuyer")
)


class RespondentDetail(models.Model):

    source = models.CharField(max_length=6, default="0")
    url_type = models.CharField(max_length=4, choices=url_choices, default="Live")
    us = models.CharField(max_length=4, choices=us_choices, default="1")
    project_number = models.CharField(max_length=20, default="")
    project_group_number = models.CharField(max_length=25, default="")
    project_group_cpi = models.FloatField(default=0)
    supplier_cpi = models.FloatField(default=0)
    resp_status = models.CharField(max_length=1, choices=respondent_status, default="1")
    final_detailed_reason = models.CharField(max_length=1000, default="")
    start_time = models.DateTimeField(auto_now_add=True)
    end_time_day = models.DateField(_("Date"), default=datetime.date.today)
    end_time = models.DateTimeField(default=timezone.now)
    duration = models.CharField(max_length=20, default=0)
    supplier_id_rejected = models.BooleanField(default=False)
    client_landing_url = models.CharField(max_length=2000, null=True, blank=True) # for check Lucid CPI when complete survey
    
    def __str__(self):
        return self.source + '-' + self.project_number + '-' + self.project_group_number + '-' + self.source + '-' + str(self.supplier_cpi) + '--' +self.resp_status

class RespondentPageDetails(models.Model):
    respondent = models.OneToOneField(RespondentDetail, null=True, blank=True, on_delete = models.CASCADE)
    last_page_seen = models.CharField(max_length=2000, null=True, blank=True)
    url_extra_params = models.JSONField(blank=True, null=True,default=dict)
    total_question_shown = models.IntegerField(default = 0)
    entry_link = models.CharField(max_length=500, null=True, blank=True)
    clientredirect_link = models.CharField(max_length=500, null=True, blank=True)
    suppliersideredirect_link = models.CharField(max_length=500, null=True, blank=True)
    endpageurl_link = models.CharField(max_length=500, null=True, blank=True)
    postbackurl_link = models.CharField(max_length=500, null=True, blank=True)

class RespondentDetailsRelationalfield(models.Model):
    respondent = models.OneToOneField(RespondentDetail, null=True, blank=True, on_delete = models.CASCADE)
    source = models.ForeignKey(SupplierOrganisation, null=True, blank=True, on_delete = models.CASCADE)
    project = models.ForeignKey(Project, null=True, blank=True, on_delete = models.CASCADE)
    project_group = models.ForeignKey(ProjectGroup, null=True, blank=True, on_delete = models.CASCADE)
    project_group_supplier = models.ForeignKey(ProjectGroupSupplier, null=True, blank=True, on_delete=models.SET_NULL)
    project_group_sub_supplier = models.ForeignKey(ProjectGroupSubSupplier, null=True, blank=True, on_delete=models.SET_NULL, default=None)

class RespondentURLDetail(models.Model):

    project_redirect_type = (
        ('0', 'Static'),
        ('1', 'Dynamic'),
    )

    respondent = models.OneToOneField(RespondentDetail, on_delete = models.CASCADE)
    actual_url = models.TextField(null=True, default="")
    url_safe_string = models.CharField(max_length=100, default="")
    user_agent = models.CharField(max_length=1000, default="")
    ip_address = models.CharField(max_length=100, default="")         # Start IP Address Store
    end_ip_address = models.CharField(max_length=100, default="")     # End IP Address Store
    pid = models.CharField(max_length=100, default="")
    userid = models.CharField(max_length=100, default="",null=True, blank=True)
    RID = models.CharField(max_length=50, default="")
    project_redirect_type = models.CharField(max_length=1, choices=project_redirect_type, default="1")
    ruid = models.CharField(max_length=50, default="", null=True, blank=True)
    pub_id = models.CharField(max_length=100, null=True, blank=True)
    rsid = models.CharField(max_length=100, null=True, blank=True)
    sub_sup_id = models.CharField(max_length=100, null=True, blank=True)


class RespondentReconcilation(models.Model):

    verify_status = (
        ('1', 'Yes'),
        ('2', 'No'),
    )

    respondent = models.OneToOneField(RespondentDetail, on_delete = models.CASCADE)
    verified = models.CharField(max_length=1, choices=verify_status)
    previous_status = models.CharField(max_length=1, choices=respondent_status, default="3")
    previous_final_detailed_reason = models.CharField(max_length=1000, default="")
    verified_at = models.DateTimeField(auto_now=True)
    verified_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='verified_by')


class RespondentDeviceDetail(models.Model):

    respondent = models.OneToOneField(RespondentDetail, on_delete = models.CASCADE)
    operating_system = models.CharField(max_length=255, default="")
    browser = models.CharField(max_length=255, default="")
    mobile = models.BooleanField(default=False)
    tablet = models.BooleanField(default=False)
    desktop = models.BooleanField(default=False)
    touch_capable = models.BooleanField(default=False)
    bot = models.BooleanField(default=False)
    mac_address = models.CharField(max_length=255, default="")


class RespondentProjectDetail(models.Model):

    respondent = models.OneToOneField(RespondentDetail, on_delete = models.CASCADE)
    project_group_status = models.CharField(max_length=23, choices=status_choices, default="Booked")
    project_group_loi = models.IntegerField(default=0)
    project_group_completes = models.CharField(max_length=10, default="")
    project_group_clicks = models.CharField(max_length=10, default="")
    project_group_redirectID = models.CharField(max_length=20, default="")
    clientURL = models.URLField(max_length=500, default="")
    project_group_security_check = models.BooleanField(default = True) 
    project_group_ip_check = models.BooleanField(default=True)
    project_group_pid_check = models.BooleanField(default=True)
    research_defender_oe_check = models.BooleanField(default=True)
    respondent_risk_check = models.BooleanField(default=True)
    failure_check = models.BooleanField(default=True)
    duplicate_check = models.BooleanField(default=True)
    threat_potential_check = models.BooleanField(default=True)
    duplicate_score = models.IntegerField(default=80)
    project_group_allowed_svscore = models.IntegerField(default=20)
    project_group_allowed_dupescore = models.IntegerField(default=80)
    project_group_allowed_fraudscore = models.IntegerField(default=50)


class RespondentSupplierDetail(models.Model):

    respondent = models.OneToOneField(RespondentDetail, on_delete = models.CASCADE)
    supplier_status = models.CharField(max_length=23, choices=status_choices, default="Booked")
    supplier_requiredN = models.IntegerField(default=0)
    supplier_required_clicks = models.IntegerField(default=0)
    supplier_complete_url = models.URLField(max_length=500, null=True, default="")
    supplier_terminate_url = models.URLField(max_length=500, null=True, default="")
    supplier_quotafull_url = models.URLField(max_length=500, null=True, default="")
    supplier_securityterminate_url = models.URLField(max_length=500, null=True, default="")
    supplier_internal_terminate_redirect_url = models.URLField(max_length=500, null=True, blank=True, default="")
    supplier_terminate_no_project_available = models.URLField(max_length=500, null=True, blank=True, default="")
    supplier_postback_url = models.URLField(max_length=500, null=True, default="")
    supplier_postback_url_response = models.TextField(null=True, default="")
    hash_value = models.CharField(max_length=150, default="")
    supplier_lucid_min_cpi = models.FloatField(null=True)

    def __str__(self):
        return self.respondent.project_number + ' - ' + self.respondent.project_group_number


class AffiliateRouterExtraURLParams(models.Model):

    respondent = models.OneToOneField(RespondentDetail, on_delete = models.CASCADE)
    ubid = models.CharField(max_length=500, unique=True, null=True)
    zoneid = models.CharField(max_length=500, unique=True, null=True)
    campaignid = models.CharField(max_length=500, null=True)
    os = models.CharField(max_length=50, null=True)
    country = models.CharField(max_length=5, null=True)
    cost = models.FloatField(null=True)
    device = models.CharField(max_length=50, null=True)
    browser = models.CharField(max_length=100, null=True)
    browserversion = models.CharField(max_length=10, null=True)
    osversion = models.CharField(max_length=20, null=True)
    countryname = models.CharField(max_length=100, null=True)
    region = models.CharField(max_length=100, null=True)
    useragent = models.CharField(max_length=50, null=True)
    language = models.CharField(null=True, max_length=100)
    connection_type = models.CharField(max_length=50, null=True)
    carrier = models.CharField(max_length=100, null=True)
    clickID = models.CharField(max_length=100, null=True, unique=True)
    bannerid = models.CharField(max_length=100, null=True, unique=True)
    user_activity = models.CharField(max_length=100, null=True)
    payout = models.FloatField(null=True)
    zone_type = models.CharField(max_length=50, null=True)


class respondent_survalidate_detail(models.Model):

    respondent = models.OneToOneField(RespondentDetail, null=False, on_delete=models.CASCADE)
    dupescore = models.IntegerField(default=0)
    svscore = models.IntegerField(default=0)
    svid = models.IntegerField(default=0)
    country_accept = models.CharField(max_length=255,null=True, default='')
    country_block = models.CharField(max_length=255,null=True, default='')
    d0 = models.IntegerField(default=0)
    d1 = models.IntegerField(default=0)
    d2 = models.IntegerField(default=0)
    d3 = models.IntegerField(default=0)
    d4 = models.IntegerField(default=0)
    d5 = models.IntegerField(default=0)
    d6 = models.IntegerField(default=0)
    reason = models.CharField(max_length=255,null=True, default='')
    f1r = models.CharField(max_length=255,null=True, default='')
    fraudscore = models.IntegerField(default=0)
    f1 = models.IntegerField(default=0)
    f2 = models.IntegerField(default=0)
    f3 = models.IntegerField(default=0)
    f4 = models.IntegerField(default=0)
    f5 = models.IntegerField(default=0)
    f6 = models.IntegerField(default=0)
    f7 = models.IntegerField(default=0)
    f8 = models.IntegerField(default=0)
    f9 = models.IntegerField(default=0)
    f10 = models.IntegerField(default=0)
    country = models.CharField(max_length=50,null=True, default='')
    is_mobile = models.IntegerField(default=0)
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)


class ProjectGroupPrescreenerDataStore(models.Model):
    respondent = models.ForeignKey(RespondentDetail, null=False, on_delete=models.CASCADE)
    prescreener_question = models.ForeignKey(ProjectGroupPrescreener, null = True, on_delete=models.SET_NULL, default = None)
    translated_question_id = models.ForeignKey(TranslatedQuestion, on_delete = models.CASCADE)
    selected_options = models.ManyToManyField(TranslatedAnswer)
    answer_file = models.FileField(upload_to='answer_file/', null=True, blank=True)
    received_response = models.TextField(default="")
    calculated_response = models.IntegerField(default=0)
    text_evalution_flag = models.BooleanField(default=False)
    text_evalution_result = models.CharField(max_length=100, default="")

class SurveyEntryWelcomePageContent(models.Model):
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    row_1_text = models.TextField(null=True, blank=True)
    row_2_text = models.TextField(null=True, blank=True)
    row_3_text = models.TextField(null=True, blank=True)
    row_4_text = models.TextField(null=True, blank=True)
    row_5_text = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

class GEOIPAPItable(models.Model):
    RespondentDetail = models.OneToOneField(RespondentDetail, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, null=True, blank = True, on_delete = models.SET_NULL)
    city = models.CharField(max_length= 100, default = "")
    latitude = models.CharField(max_length=100, default = "")
    longitude = models.CharField(max_length=100, default = "")

class DisqoQueryParam(models.Model):
    respondent = models.OneToOneField(RespondentDetail, null=False, on_delete=models.CASCADE)
    auth = models.CharField(max_length=255, null=True, blank=True, default="")
    clientId = models.IntegerField(default=0)
    pid = models.CharField(max_length=100, null=True, blank=True, default="")
    projectId = models.CharField(max_length=255, null=True, blank=True, default="")
    quotaIds = models.TextField(null=True, blank=True, default="")
    supplierId = models.CharField(max_length=100, null=True, blank=True, default="")
    tid = models.CharField(max_length=100, null=True, blank=True, default="")

class RespondentRoutingDetail(models.Model):
    respondent = models.OneToOneField(RespondentDetail, null=True, on_delete=models.CASCADE)
    is_routing = models.BooleanField(default=False)
    previous_project_group_number = models.CharField(max_length=25, default="")
    base_supplier_cpi = models.FloatField(default=0)



class ComputedOnHoldProjectsRespStats(models.Model):
    project_name = models.CharField(max_length=100, null=True)
    project_status = models.CharField(max_length=100, null=True)
    customer = models.CharField(max_length=100, null=True)
    completes = models.IntegerField(null=True)
    revenue = models.FloatField(null=True)
    expense = models.FloatField(null=True)
    margin = models.FloatField(null=True)
    project_number = models.CharField(max_length=100, null=True)
    last_complete_date = models.CharField(max_length=100, null=True)
    customercode = models.IntegerField(null=True)
    user_id = models.IntegerField(null=True)

class RespondentResearchDefenderDetail(models.Model):
    respondent = models.ForeignKey(RespondentDetail, null=False, on_delete=models.CASCADE)
    q_id = models.CharField(max_length=250, null=True, blank=True, default="")
    entered_text = models.CharField(max_length=2500, null=True, blank=True, default="")
    encoded_page_load_time = models.CharField(max_length=2500, null=True, blank=True, default="")
    encoded_pasted_text_data = models.CharField(max_length=2500, null=True, blank=True, default="")
    encoded_answer_typed_time = models.CharField(max_length=2500, null=True, blank=True, default="")
    encoded_answer_submited_time = models.CharField(max_length=2500, null=True, blank=True, default="")
    page_load_time = models.PositiveBigIntegerField(default=0)
    pasted_text_data = models.CharField(max_length=2500, null=True, blank=True, default="")
    answer_typed_time = models.PositiveBigIntegerField(default=0)
    answer_submited_time = models.PositiveBigIntegerField(default=0)
    s_text_length = models.PositiveSmallIntegerField(default=50)
    sn_ud = models.CharField(max_length=2500, null=True, blank=True, default="")
    sy_nr = models.CharField(max_length=2500, null=True, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

class ResearchDefenderResponseDetail(models.Model):
    research_defender = models.OneToOneField(RespondentResearchDefenderDetail, null=False, on_delete=models.CASCADE)
    entered_text = models.CharField(max_length=2500, null=True, blank=True, default="")
    entered_q_id = models.CharField(max_length=2500, null=True, blank=True, default="")
    entered_similarity_text_length = models.CharField(max_length=2500, null=True, blank=True, default="")
    entered_sn_ud = models.CharField(max_length=2500, null=True, blank=True, default="")
    entered_sy_nr = models.CharField(max_length=2500, null=True, blank=True, default="")
    language_detected = models.CharField(max_length=2500, null=True, blank=True, default="")
    pasted_response = models.PositiveIntegerField(default=0)
    typed_response_time = models.FloatField(default=0)
    page_view_time = models.FloatField(default=0)
    garbage_words_score = models.FloatField(default=0)
    similarity_text = models.FloatField(default=0)
    garbage_words = models.PositiveIntegerField(default=0)
    language_detected_score = models.FloatField(default=0)
    profanity_check_score = models.FloatField(default=0)
    pasted_response_score = models.FloatField(default=0)
    profanity_check = models.PositiveIntegerField(default=0)
    engagement_score = models.FloatField(default=0)
    composite_score = models.PositiveIntegerField(default=0)
    client_blacklist = models.CharField(max_length=50, null=True, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)



class ResearchDefenderSearch(models.Model):
    failure_reason_choices = (
        # Returns a code based on the respondent’s fraudulent status (Duplicate entrant, TOR users etc..). Below are the following code and its description:
        ("01","Everything all right"),
        ("02","Duplicate entrant into survey"),
        ("03","User Emulator"),
        ("04","Nefarious VPN usage detected"),
        ("05","TOR network detected"),
        ("06","Public proxy server detected"),
        ("07","Web proxy service used"),
        ("08","Web crawler usage detected"),
        ("09","Internet fraudster detected"),
        ("10","Retail and ad-tech fraudster detected "),
        ("11","IP Address subnet detected"),
        ("12","Recent Abuse detected"),
        ("13","Duplicate Survey Group detected"),
        ("14","Navigator Webdriver detected"),
        ("15","Developer tool detected"),
    )
    respondent = models.OneToOneField(RespondentDetail, null=False, on_delete=models.CASCADE)
    survey_number = models.CharField(max_length=100, null=True)
    country_mismatch = models.FloatField(default=0)
    destination = models.CharField(max_length=250, null=True)
    duplicate_potential = models.CharField(max_length=100, null=True)
    failure_reason = models.CharField(max_length=2, choices=failure_reason_choices, default="01")
    duplicate_initial_ud = models.CharField(max_length=250, null=True)
    flag = models.FloatField(default=0)
    duplicate_score = models.FloatField(default=0)
    sn_ud = models.CharField(max_length=250, null=True)
    threat_potential = models.CharField(max_length=100, null=True)
    country_code = models.CharField(max_length=50, null=True)
    country = models.CharField(max_length=50, null=True)
    respondent_risk = models.FloatField(default=0)
    respondent_ud = models.CharField(max_length=250, null=True)
    threat_potential_score = models.FloatField(default=0)


class ResearchDefenderFailureReasonDataStore(models.Model):
    respondent = models.OneToOneField(RespondentDetail, null=True, on_delete=models.CASCADE)
    failure_reason = models.CharField(max_length=250, default="")
    defender_response = models.JSONField(max_length=1000, default = dict)
    


class AffialiateRouterRelationField(models.Model):
    visitor_survey_redirect = models.ForeignKey(VisitorSurveyRedirect, on_delete=models.SET_NULL, null=True)
    respondent = models.OneToOneField(RespondentDetail, null=True, on_delete=models.SET_NULL)

class clientBackTrackingDetails(models.Model):
    respondent = models.ForeignKey(RespondentDetail, null=False, on_delete=models.CASCADE)
    captured_url_params = models.JSONField(max_length=1000, default = dict)


class RespondentProjectGroupSubSupplier(models.Model):
    respondent = models.OneToOneField(RespondentDetail, null=True, on_delete=models.CASCADE)
    project_group_sub_supplier = models.ForeignKey(ProjectGroupSubSupplier, null=True, blank=True, on_delete=models.SET_NULL)
    sub_supplier_requiredN = models.IntegerField(default=0)
    sub_supplier_required_clicks = models.IntegerField(default=0)
    sub_supplier_complete_url = models.URLField(max_length=500, null=True, default="")
    sub_supplier_terminate_url = models.URLField(max_length=500, null=True, default="")
    sub_supplier_quotafull_url = models.URLField(max_length=500, null=True, default="")
    sub_supplier_securityterminate_url = models.URLField(max_length=500, null=True, default="")
    sub_supplier_internal_terminate_redirect_url = models.URLField(max_length=500, null=True, blank=True, default="")
    sub_supplier_terminate_no_project_available = models.URLField(max_length=500, null=True, blank=True, default="")
    sub_supplier_postback_url = models.URLField(max_length=500, null=True, default="")
    sub_supplier_postback_url_response = models.TextField(null=True, default="")
    hash_value = models.CharField(max_length=150, default="")

class RespondentDetailTolunaFields(models.Model):
    respondent = models.OneToOneField(RespondentDetail, on_delete = models.CASCADE, related_name='survey_entry_toluna_field')
    redirected_survey_incidence = models.IntegerField(null=True)
    redirected_survey_wave_id = models.IntegerField(null=True)
    redirected_survey_quota_id = models.CharField(max_length=100, null=True)
    member_code = models.CharField(max_length=100, null=True, unique=True) # FOR GENERATING MEMBERS ON TOLUNA'S END
    survey_supply_code = models.CharField(max_length=100, null=True, blank=True)
    supplier_code = models.CharField(max_length=100, null=True, blank=True)
    visitor_amount = models.FloatField(null=True)
    country_iso = models.CharField(max_length=5, null=True)
    user_prescreener_response = models.JSONField(max_length=1000, null = True)
    qualified_quota = models.CharField(max_length=1000, null = True)