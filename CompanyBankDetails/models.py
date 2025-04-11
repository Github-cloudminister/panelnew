from email.policy import default
from pyexpat import model
from statistics import mode
from django.db import models
from django.db.models.fields.related import ForeignKey
from Project.models import *
from Customer.models import *
from employee.models import *



class CompanyDetails(models.Model):
    company_name = models.CharField(max_length=150, null=True, blank=True, default='')
    company_contact_number = models.CharField(max_length=14, null=True, validators=[
        RegexValidator(
            regex=r'^\+?1?\d{9,13}$',
            message="Contact number must be in the format of '+123456789'. Up to 13 digits allowed.")]
    )
    company_address1 = models.CharField(max_length=250, null=True, blank=True, default='')
    company_address2 = models.CharField(max_length=250, null=True, blank=True, default='')
    company_city = models.CharField(max_length=250, null=True, blank=True, default='')
    company_state = models.CharField(max_length=250, null=True, blank=True, default='')
    company_country= models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    company_zipcode = models.CharField(max_length=10, null=True, blank=True, default='')
    company_email = models.EmailField(null=True, blank=True, default='')
    company_website = models.URLField(max_length=300, null=True, blank=True, default='')
    company_tax_number = models.CharField(max_length=20, null=True, blank=True, default='')
    company_cin_number = models.CharField(max_length=255, null=True, blank=True, default='')
    company_pan_number = models.CharField(max_length=20, null=True, blank=True, default='')
    company_invoice_prefix_local_currency = models.CharField(max_length=20, null=True, blank=True, default='')
    company_invoice_prefix_international_currency = models.CharField(max_length=20, null=True, blank=True, default='')
    company_invoice_suffix_local_currency = models.CharField(max_length=20, null=True, blank=True, default='')
    company_invoice_suffix_international_currency = models.CharField(max_length=20, null=True, blank=True, default='')

    # Relational Fields
    company_local_currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True)


    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, blank=True, null=True, related_name='company_details_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, blank=True, null=True, related_name='company_details_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

class CompanyInvoiceBankDetail(models.Model):

    account_type_choices = [
        ('1', 'Current'),
        ('2', 'Saving'),
        ('3', 'Checking Account'),
    ]

    account_number = models.CharField(max_length=255, null=True, blank=True, default="")
    ifsc_code = models.CharField(max_length=255, null=True, blank=True, default="")
    bank_name = models.CharField(max_length=255, null=True, blank=True, default="")
    bank_address = models.TextField(null=True, blank=True, default="")
    swift_code = models.CharField(max_length=255, null=True, blank=True, default="")
    account_type = models.CharField(max_length=10, null=True, blank=True, choices=account_type_choices, default="1")
    company_iban_number = models.CharField(max_length=30, null=True, blank=True, default='')
    company_routing_number = models.CharField(max_length=30, null=True, blank=True, default='')

    # Relational Fields
    company_details = models.ForeignKey(CompanyDetails, on_delete=models.SET_NULL,blank=True, null=True)

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, blank=True, null=True, related_name='company_invoice_data_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, blank=True, null=True, related_name='company_invoice_data_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-id',)

