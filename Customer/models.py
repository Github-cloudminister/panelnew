from django.db import models
from django.core.validators import RegexValidator

from employee.models import EmployeeProfile, Country



class Currency(models.Model):

    # Fields
    currency_name = models.CharField(max_length=60, unique=True, null=True)
    currency_iso = models.CharField(max_length=3,null=True)
    client_currency_id = models.IntegerField(null=True)
    client_currency_name = models.CharField(max_length=80, null=True)
    customer_name = models.CharField(max_length=50, null=True) # JUST FOR KNOWING WHETHER CLIENT IS INTEGRATED OR NOT AND WHO IS THE CLIENT

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='currency_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='currency_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-modified_at',)

    constraints = [
        models.UniqueConstraint(fields=['customer_name', 'client_currency_id'], name="unique_customer_name_currency_id")
        ]

    def __str__(self):
        return '{}'.format(self.currency_iso)




class CustomerOrganization(models.Model):

    # choices
    org_choices = (
        ('1', 'Wholesaler'),
        ('2', 'Retailer'),
    )

    cpi_calculation = (
        ('1', 'Including GST'),
        ('2', 'Excluding GST'),
    )

    # Fields
    cust_org_name = models.CharField(max_length=150, unique=True)
    customer_organization_type = models.CharField(
        max_length=1, choices=org_choices, default='1')
    cust_org_address_1 = models.CharField(max_length=120, null=True, blank=True)
    cust_org_address_2 = models.CharField(max_length=120, null=True, blank=True)
    cust_org_city = models.CharField(max_length=30, null=True, blank=True)
    cust_org_state = models.CharField(max_length=30, null=True, blank=True)
    cpi_calculation_method = models.CharField(null=True, blank=True, choices=cpi_calculation, max_length=1)
    payment_terms = models.IntegerField(null=False, blank=True)
    cust_org_country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL)
    cust_org_zip = models.CharField(max_length=10, null=True, blank=True)
    cust_org_TAXVATNumber = models.CharField(max_length=25, null=True, blank=True)
    cust_org_website = models.CharField(max_length=100, null=True, blank=True)
    cust_org_other = models.CharField(max_length=100, null=True, blank=True)
    threat_potential_score = models.IntegerField(default=60)

    # Additional Fields
    cust_org_ship_to_address_1 = models.CharField(max_length=120, null=True, blank=True)
    cust_org_ship_to_address_2 = models.CharField(max_length=120, null=True, blank=True)
    cust_org_ship_to_city = models.CharField(max_length=30, null=True, blank=True)
    cust_org_ship_to_state = models.CharField(max_length=30, null=True, blank=True)
    cust_org_ship_to_country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.SET_NULL, related_name='ship_to_country')
    cust_org_ship_to_zip = models.CharField(max_length=10, null=True, blank=True)
    customer_url_code = models.CharField(max_length=50, blank=True, null=True)

    # Company Invoice Bank Detail
    company_invoice_bank_detail = models.ForeignKey('CompanyBankDetails.CompanyInvoiceBankDetail', null=True, blank=True, default='', on_delete=models.SET_NULL)

    # Relationship Fields
    sales_person_id = models.ForeignKey(
        EmployeeProfile, on_delete=models.PROTECT)
    currency = models.ForeignKey('Currency', on_delete=models.CASCADE)
    customer_invoice_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='customer_inv_currencies', null=True)

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='cust_org_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='cust_org_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('cust_org_name',)

    def __str__(self):
        return '{}'.format(self.cust_org_name.capitalize())



class ClientContact(models.Model):

    # Fields
    client_firstname = models.CharField(max_length=30)
    client_lastname = models.CharField(max_length=30)
    client_email = models.EmailField(max_length=80)
    client_contactnumber = models.CharField(max_length=14, null=True, validators=[
        RegexValidator(
            regex=r'^\+?1?\d{9,13}$',
            message="Contact number must be in the format of '+123456789'. Up to 13 digits allowed.")]
    )
    client_status = models.BooleanField(default=True)
    # Relationship Fields
    customer_id = models.ForeignKey(
        CustomerOrganization, on_delete=models.CASCADE)

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='client_cont_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='client_cont_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-modified_at',)

    def __str__(self):
        return '{} from {}'.format(self.client_firstname.capitalize(), self.customer_id.cust_org_name.capitalize())



class CustomerOrgAuthKeyDetails(models.Model):
    customerOrg = models.OneToOneField(CustomerOrganization, on_delete=models.CASCADE, related_name='authkey_detail')
    authkey = models.CharField(max_length=200, null=True, blank=True)
    staging_authkey = models.CharField(max_length=200, null=True, blank=True)
    api_key = models.CharField(max_length=200, null=True, blank=True)
    staging_api_key = models.CharField(max_length=200, null=True, blank=True)
    secret_key = models.CharField(max_length=200, null=True, blank=True)
    staging_secret_key = models.CharField(max_length=200, null=True, blank=True)
    staging_base_url = models.URLField(null=True, blank=True)
    production_base_url = models.URLField(null=True, blank=True)
    client_id = models.CharField(max_length=100, null=True, blank=True)
    supplier_id = models.CharField(max_length=30, null=True, blank=True)