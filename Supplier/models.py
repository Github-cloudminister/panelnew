from django.db import models
from django.core.validators import RegexValidator, MaxValueValidator, MinValueValidator
from django.db.models.base import Model
from django.db.models.fields.related import OneToOneField

from CompanyBankDetails.models import CompanyDetails
from Customer.models import Currency
from employee.models import *


class SupplierOrganisation(models.Model):

    status_choices = (
        ('1', 'Allowed'),
        ('2', 'Blocked'),
    )

    supplier_type_choices = (
        ('1', 'Manual'),
        ('2', 'API'),
        ('3', 'Router'),
        ('4', 'Panel'),
        ('5', 'Panel 2'),
    )

    supplier_rate_model_choices = (
        ('3', 'Manual'), #Project basis
        ('1', 'Flat'),
        ('2', 'Revenue Sharing'),
    )

    supplier_quality_type_choices = (
        ('1', 'Low'),
        ('2', 'Medium'),
        ('3', 'High'),
    )
    cpi_calculation = (
        ('1', 'Including GST'),
        ('2', 'Excluding GST'),
    )

    # Fields
    supplier_code = models.CharField(max_length=50, default="" ,null=True)
    supplier_name = models.CharField(max_length=150)
    max_completes_on_diy = models.IntegerField(default=10)
    # total_surveyside_counts = models.IntegerField(default=0)
    supplier_address1 = models.CharField(max_length=150, null=True)
    supplier_address2 = models.CharField(max_length=150, null=True)
    supplier_city = models.CharField(max_length=25, null=True)
    supplier_state = models.CharField(max_length=25, null=True)
    supplier_country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL)
    company_bank_detail = models.ForeignKey(CompanyDetails, default='1',on_delete=models.SET_NULL,null=True)
    supplier_zip = models.CharField(max_length=10, null=True)
    supplier_TAX_id = models.CharField(max_length=50, null=True, blank=True, default="N/A")
    supplier_currency = models.ForeignKey(Currency, on_delete=models.CASCADE,default=156)
    cpi_calculation_method = models.CharField(choices=cpi_calculation,default = '1', max_length=1)
    supplier_completeurl = models.URLField(max_length=500, null=True, default="")
    supplier_terminateurl = models.URLField(max_length=500, null=True, default="")
    supplier_quotafullurl = models.URLField(max_length=500, null=True, default="")
    supplier_securityterminateurl = models.URLField(max_length=500, null=True, default="")
    supplier_postbackurl = models.URLField(max_length=500, null=True, blank=True, default="")
    supplier_routerurl = models.URLField(max_length=500, null=True, blank=True, default = "")
    supplier_rate_model = models.CharField(max_length=1, choices=supplier_rate_model_choices, default = "3")
    supplier_rate = models.CharField(max_length=5, default = 0.5)

    supplier_paymentdetails = models.TextField(null=True)
    supplier_status = models.CharField(
        max_length=1, choices=status_choices, default='1')
    # visitor_survey_side = models.CharField(
    #     max_length=1, choices=SURVEY_SIDE_CHOICES, default='3')

    # Fields for API Supplier
    supplier_type = models.CharField(max_length=1, choices=supplier_type_choices, default="1")
    supplier_quality_type = models.CharField(max_length=1, choices=supplier_quality_type_choices, default="1")
    supplier_internal_terminate_redirect_url = models.URLField(max_length=500, null=True, blank=True, default="")
    supplier_terminate_no_project_available = models.URLField(max_length=500, null=True, blank=True, default="")
    supplier_url_code = models.CharField(max_length=50, blank=True, null=True, default="")
    max_authorized_cpi = models.FloatField(default=0)

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='supp_org_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='supp_org_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-modified_at',)

    def __str__(self):
        return '{}'.format(self.supplier_name.capitalize())


class SupplierAPIAdditionalfield(models.Model):
    supplier = models.OneToOneField(SupplierOrganisation, on_delete=models.CASCADE)
    hash_security_key = models.CharField(max_length=255, default="", null=True)
    hash_variable_name = models.CharField(max_length=255, default="", null=True)
    enable_hash = models.BooleanField(default=False)
    enable_routing = models.BooleanField(default=False)

class SupplierCPIMapping(models.Model):
    supplier_org = models.ForeignKey(SupplierOrganisation, null=True, on_delete=models.CASCADE)
    cpi = models.FloatField(default=0)
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL)

class SupplierContact(models.Model):

    # Fields
    supplier_firstname = models.CharField(max_length=30)
    supplier_lastname = models.CharField(max_length=30)
    supplier_contactnumber = models.CharField(max_length=14, null=True, validators=[
        RegexValidator(
            regex=r'^\+?1?\d{9,13}$',
            message="Contact number must be in the format of '+123456789'. Up to 13 digits allowed.")]
    )
    supplier_contact_status = models.BooleanField(default=True)
    send_supplier_updates = models.BooleanField(default=True)
    supplier_dashboard_registration = models.BooleanField(default=False)
    send_final_ids = models.BooleanField(default=True)
    supplier_email_notify = models.BooleanField(default=False)
    supplier_email = models.EmailField(max_length=80)
    supplier_mail_sent = models.BooleanField(default=False)

    # Relationship Fields
    supplier_id = models.ForeignKey(
        SupplierOrganisation, on_delete=models.CASCADE)

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='supp_cont_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='supp_cont_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-modified_at',)

    def __str__(self):
        return '{}--{}'.format(self.supplier_firstname.capitalize(), self.supplier_lastname.capitalize())


class SupplierOrgAuthKeyDetails(models.Model):
    supplierOrg = models.OneToOneField(SupplierOrganisation, on_delete=models.CASCADE)
    authkey = models.CharField(max_length=200, null=True, blank=True)
    staging_authkey = models.CharField(max_length=200, null=True, blank=True)
    api_key = models.CharField(max_length=200, null=True, blank=True)
    staging_api_key = models.CharField(max_length=200, null=True, blank=True)
    secret_key = models.CharField(max_length=200, null=True, blank=True)
    staging_secret_key = models.CharField(max_length=200, null=True, blank=True)
    staging_base_url = models.URLField(max_length=500, null=True, blank=True)
    production_base_url = models.URLField(max_length=500, null=True, blank=True)
    client_id = models.CharField(max_length=100, null=True, blank=True)
    supplier_id = models.CharField(max_length=30, null=True, blank=True)


class SupplierInvoicingDetails(models.Model):
    supplier_org = models.OneToOneField(SupplierOrganisation, on_delete=models.CASCADE, related_name='supplier_invoice_details')
    inv_address1 = models.TextField()
    inv_address2 = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    pincode = models.CharField(max_length=25)
    mobile_no = models.CharField(max_length=20)
    supp_tax_no = models.CharField(max_length=50)
    supp_contact_emailID = models.EmailField(max_length=80)
    mangemnt_primary_contact = models.ForeignKey(SupplierContact, on_delete=models.CASCADE, related_name='supplier_invoice_details')
    finalIDs_email_addresses = models.ManyToManyField(SupplierContact)


class SupplierBankDetails(models.Model):
    supplier_inv_detail = models.OneToOneField(SupplierInvoicingDetails, on_delete=models.CASCADE, related_name='supplier_bank_detail')
    bank_name = models.CharField(max_length=50)
    bank_address = models.TextField()
    bank_account_no = models.CharField(max_length=100)
    ifsc_code = models.CharField(max_length=50, null=True)
    swift_code = models.CharField(max_length=50, null=True)
    iban_routing_code = models.CharField(max_length=50, null=True)




class DisqoAPIPricing(models.Model):
    min_loi = models.IntegerField(default=1,
                                validators=[
                                    MaxValueValidator(200),
                                    MinValueValidator(1)
                                ])
    max_loi = models.IntegerField(default=1,
                                validators=[
                                    MaxValueValidator(200),
                                    MinValueValidator(1)
                                ])
    min_incidence = models.IntegerField(default=100,
                                    validators=[
                                        MaxValueValidator(100),
                                        MinValueValidator(1)
                                    ])
    max_incidence = models.IntegerField(default=100,
                                    validators=[
                                        MaxValueValidator(100),
                                        MinValueValidator(1)
                                    ])
    cpi = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)


class SubSupplierOrganisation(models.Model):

    status_choices = (
        ('1', 'Allowed'),
        ('2', 'Blocked'),
    )

    sub_supplier_rate_model_choices = (
        ('3', 'Manual'), #Project basis
        ('1', 'Flat'),
        ('2', 'Revenue Sharing'),
    )

    supplier_quality_type_choices = (
        ('1', 'Low'),
        ('2', 'Medium'),
        ('3', 'High'),
    )

    supplier_org_id = models.ForeignKey(SupplierOrganisation, on_delete=models.CASCADE,related_name='sub_supplier_buyer_apid')
    sub_supplier_code = models.CharField(max_length=50, default="" ,null=True)
    sub_supplier_name = models.CharField(max_length=150)
    max_completes_on_diy = models.IntegerField(default=10)
    sub_supplier_address1 = models.CharField(max_length=150, null=True)
    sub_supplier_address2 = models.CharField(max_length=150, null=True)
    sub_supplier_city = models.CharField(max_length=25, null=True)
    sub_supplier_state = models.CharField(max_length=25, null=True)
    sub_supplier_country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL)
    sub_supplier_zip = models.CharField(max_length=10, null=True)
    sub_supplier_TAX_id = models.CharField(max_length=50, null=True, blank=True, default="N/A")
    sub_supplier_completeurl = models.URLField(max_length=500, null=True, default="")
    sub_supplier_terminateurl = models.URLField(max_length=500, null=True, default="")
    sub_supplier_quotafullurl = models.URLField(max_length=500, null=True, default="")
    sub_supplier_securityterminateurl = models.URLField(max_length=500, null=True, default="")
    sub_supplier_postbackurl = models.URLField(max_length=500, null=True, blank=True, default="")
    sub_supplier_routerurl = models.URLField(max_length=500, null=True, blank=True, default = "")
    sub_supplier_rate_model = models.CharField(max_length=1, choices=sub_supplier_rate_model_choices, default = "3")
    sub_supplier_quality_type = models.CharField(max_length=1, choices=supplier_quality_type_choices, default = "1")
    sub_supplier_rate = models.CharField(max_length=5, default = 0.5)
    sub_supplier_paymentdetails = models.TextField(null=True)
    sub_supplier_status = models.CharField(max_length=1, choices=status_choices, default='1')
    sub_supplier_internal_terminate_redirect_url = models.URLField(max_length=500, null=True, blank=True, default="")
    sub_supplier_terminate_no_project_available = models.URLField(max_length=500, null=True, blank=True, default="")
    sub_supplier_url_code = models.CharField(max_length=50, blank=True, null=True, default="")
    max_authorized_cpi = models.FloatField(default=0)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='subsupp_org_created_by')
    modified_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='subsupp_org_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-modified_at',)

    def __str__(self):
        return '{}'.format(self.sub_supplier_name.capitalize())

class SubSupplierContact(models.Model):

    # Fields
    subsupplier_firstname = models.CharField(max_length=30)
    subsupplier_lastname = models.CharField(max_length=30)
    subsupplier_contactnumber = models.CharField(max_length=14, null=True, validators=[
        RegexValidator(
            regex=r'^\+?1?\d{9,13}$',
            message="Contact number must be in the format of '+123456789'. Up to 13 digits allowed.")]
    )
    subsupplier_contact_status = models.BooleanField(default=True)
    subsend_supplier_updates = models.BooleanField(default=True)
    subsupplier_dashboard_registration = models.BooleanField(default=False)
    subsend_final_ids = models.BooleanField(default=True)
    subsupplier_email_notify = models.BooleanField(default=False)
    subsupplier_email = models.EmailField(max_length=80)
    subsupplier_mail_sent = models.BooleanField(default=False)
    subsupplier_id = models.ForeignKey(SubSupplierOrganisation, on_delete=models.CASCADE)
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='subsupp_cont_created_by')
    modified_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='subsupp_cont_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-modified_at',)

    def __str__(self):
        return '{}--{}'.format(self.subsupplier_firstname.capitalize(), self.subsupplier_lastname.capitalize())