from django.db import models
from Customer.models import CustomerOrganization,Country
from Project.models import Language, ProjectGroup
from Supplier.models import SubSupplierOrganisation, SupplierOrganisation

class ClientDBCountryLanguageMapping(models.Model): # CULTURES IN TOLUNA DOCS
    customer = models.ForeignKey(CustomerOrganization, on_delete=models.CASCADE)
    lanugage_id = models.ForeignKey(Language, on_delete=models.CASCADE, null=True)
    country_id = models.ForeignKey(Country, on_delete=models.CASCADE, null=True)
    toluna_client_language_id = models.CharField(max_length=100)
    zamplia_client_language_id = models.CharField(max_length=100, null=True, blank=True)
    sago_client_language_id = models.CharField(max_length=100, null=True, blank=True)
    client_language_name = models.CharField(max_length=100, null=True)
    client_language_description = models.CharField(max_length=100, null=True)
    country_lang_guid = models.CharField(max_length=500, null=True, blank=True) # AS OF NOW, ONLY FOR TOLUNA CLIENT/BUYER


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['customer', 'lanugage_id','country_id'], name="unique_customer_lanugage_id_country_id")
            ]


    def __str__(self):
        return '{}'.format(self.client_language_name)
    

class ClientQuota(models.Model):
    project_group = models.ForeignKey(ProjectGroup, on_delete=models.CASCADE,null=True,blank=True)
    quota_id = models.IntegerField(unique=True, null=False)
    completes_required = models.IntegerField(default=0)
    completes_remaining = models.IntegerField(default=0)
    quota_json_data = models.JSONField(max_length=5000, default = dict)


class ClientLayer(models.Model):
    client_quota = models.ForeignKey(ClientQuota, on_delete=models.CASCADE)
    layer_id = models.IntegerField(unique=True, null=False)


class ClientSubQuota(models.Model):
    client_layer = models.ForeignKey(ClientLayer, on_delete=models.CASCADE)
    subquota_id = models.IntegerField(unique=True, null=False)
    current_completes = models.IntegerField(default=0)
    target_completes = models.IntegerField(default=0)


class ClientSurveyPrescreenerQuestions(models.Model):

    client_subquota = models.ForeignKey(ClientSubQuota, on_delete=models.CASCADE, null=True)
    client_question_mapping = models.ForeignKey('Questions.TranslatedQuestion', on_delete=models.CASCADE)
    client_answer_mappings = models.ManyToManyField('Questions.TranslatedAnswer', blank=True, editable=False)
    open_end_ans_options = models.TextField(null=True)
    age_range_list = models.JSONField(default = dict)
    allowedRangeMin = models.CharField(max_length=500, null=True)
    allowedRangeMax = models.CharField(max_length=500, null=True)
    date_answer_option = models.DateField(null=True)
    is_routable = models.BooleanField(default=False)
    client_name = models.CharField(max_length=50) # JUST FOR IDENTIFYING WHAT CLIENT'S QUESTION ANSWERS THESE ARE, BY ENTERING CUSTOMER_URL_CODE. ONLY FOR BACKEND PURPOSES


class CustomerDefaultSupplySources(models.Model): # ProjectGroupSupplier Default Values Set During Automation
    customerOrg = models.ForeignKey(CustomerOrganization, on_delete=models.CASCADE)
    supplierOrg = models.ForeignKey(SupplierOrganisation, on_delete=models.CASCADE)
    default_max_cpi = models.FloatField()
    default_max_completes = models.IntegerField()
    default_max_clicks = models.IntegerField()
    is_active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['customerOrg', 'supplierOrg'], name="unique_customer_supplier_new")
            ]


class CustomerDefaultSubSupplierSources(models.Model):
    customerOrg = models.ForeignKey(CustomerOrganization, on_delete=models.CASCADE)
    sub_supplierOrg = models.ForeignKey(SubSupplierOrganisation, on_delete=models.CASCADE)
    default_max_cpi = models.FloatField()
    default_max_completes = models.IntegerField()
    default_max_clicks = models.IntegerField()
    is_active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['customerOrg', 'sub_supplierOrg'], name="unique_customer_sub_supplier_new")
            ]

class SurveyQualifyParametersCheck(models.Model):
    customerOrg = models.OneToOneField(CustomerOrganization, on_delete=models.CASCADE, null=True) # NULL ADDED JUST FOR MIGRATION, REMOVE LATER
    bid_incidence_lte = models.FloatField(default=0)
    bid_incidence_gte = models.FloatField(default=0)
    cpi_lte = models.FloatField(default=0)
    cpi_gte = models.FloatField(default=0)
    bid_loi_gte = models.IntegerField(default=0)
    bid_loi_lte = models.IntegerField(default=0)
    conversion_gte = models.IntegerField(default=0)
    client_country_languages = models.ManyToManyField(ClientDBCountryLanguageMapping)