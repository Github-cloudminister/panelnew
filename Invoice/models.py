from django.db import models
from django.db.models.fields.related import ForeignKey
from Project.models import *
from Customer.models import *
from employee.models import *


class Invoice(models.Model):

    status = (
        ('1', 'Draft'),
        ('2', 'Sent'),
        ('3', 'Paid'),
        ('4', 'Cancel'),
    )
    tax_choices = (
        ('1', 'None'),
        ('2', 'IGST'),
        ('3', 'SGST/CGST'),
    )

    invoice_number = models.CharField(max_length=50, default="")
    prefix = models.CharField(max_length=50, default="")
    suffix = models.IntegerField(null=True, blank=True)
    invoice_project = models.ManyToManyField(Project)
    invoice_description = models.TextField(null=True, blank=True)
    invoice_po_number = models.TextField(null=True, blank=True) # Keeping it just like that, Not using this Field at all
    invoice_customer = models.ForeignKey(CustomerOrganization, on_delete=models.CASCADE)
    invoice_contact = models.ForeignKey(ClientContact, on_delete=models.CASCADE)
    invoice_status = models.CharField(max_length=1, choices=status, default='1')
    invoice_show_conversion_rate = models.BooleanField(default=False)
    invoice_conversion_rate = models.FloatField(default=0)
    invoice_total_amount_in_USD = models.FloatField(default=0)
    invoice_total_amount = models.FloatField(default=0)
    invoice_subtotal_amount = models.FloatField(default=0)


    # Additional Fields
    invoice_date = models.DateField()
    invoice_due_date = models.DateField()
    invoice_ship_to_address_enable = models.BooleanField(default=True)
    invoice_tax = models.CharField(max_length=1, choices=tax_choices, default='1')
    invoice_IGST_value = models.FloatField(default=0)
    invoice_SGST_value = models.FloatField(default=0)
    invoice_CGST_value = models.FloatField(default=0)
    invoice_TDS_amount = models.FloatField(default=0)
    discount = models.FloatField(default=0)
    subtotal_after_discount = models.FloatField(default=0)
    invoice_TDS_percentage = models.FloatField(default=0)
    invoice_show_stamp = models.BooleanField(default=False)
    invoice_currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True)

    # Company Invoice Bank Detail
    company_invoice_bank_detail = models.ForeignKey('CompanyBankDetails.CompanyInvoiceBankDetail', null=True, blank=True, default="", on_delete=models.SET_NULL)

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='invoice_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='invoice_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)
    
    def get_invoice_contact_full_name(self):
        return f'{self.invoice_contact.client_firstname} {self.invoice_contact.client_lastname}'

    class Meta:
        ordering = ('-id',)
    
    def __str__(self):
        return '{}'.format(self.invoice_number)


class InvoiceRow(models.Model):

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    project_group_number = models.ForeignKey(ProjectGroup, on_delete=models.SET_NULL, null=True) # Keeping it just like that, Not using this Field at all
    row_project_number = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    row_po_number = models.TextField(default='',blank=True)
    row_hsn_code = models.CharField(max_length=200, null=True)
    row_name = models.CharField(max_length=255, null=False)
    row_completes = models.IntegerField(default=0)
    row_cpi = models.FloatField(default=0)
    row_total_amount = models.FloatField(default=0)
    row_description = models.TextField(null=True, default="")

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='invoice_row_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='invoice_row_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('id',)


class DraftInvoice(models.Model):

    cpi_calculation = (
        ('1', 'Including GST'),
        ('2', 'Excluding GST'),
    )

    project = models.OneToOneField(Project, null=True, on_delete=models.CASCADE)
    invoice_to_customer = models.ForeignKey(CustomerOrganization, null=True, on_delete=models.CASCADE)
    invoice_currency = models.ForeignKey(Currency, null=True, on_delete=models.CASCADE)
    bid_currency = models.ForeignKey(Currency, null=True, on_delete=models.CASCADE, related_name='draft_invoice_bid_currency')
    confirm_email_file = models.FileField(upload_to='invoice_confirmation_attachment/', max_length=5000, null=True, blank=True)
    invoice_total = models.FloatField(null=True, blank=True)
    bid_total = models.FloatField(null=True, blank=True)
    conversion_rate = models.FloatField(null=True, blank=True)
    cpi_calculation_method = models.CharField(null=True, blank=True, choices=cpi_calculation, max_length=1)
    draft_approved = models.BooleanField(default=False)
    approval_note = models.TextField(null=True, blank=True)
    notes_from_pm = models.TextField(null=True, blank=True)
    project_invoiced_date = models.DateField(null=True)

    BA_approved = models.BooleanField(default=False)
    Accountant_approved = models.BooleanField(default=False)

    BA_approved_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='draft_invoice_ba_approved_by')

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='draft_invoice_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='draft_invoice_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('id',)



class DraftInvoiceRow(models.Model):
    draft_invoice = models.ForeignKey(DraftInvoice, null=True, on_delete=models.CASCADE)
    po_number = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    bid_cpi = models.FloatField(default=0)
    cpi = models.FloatField(default=0)
    completes = models.IntegerField(default=0)
    total = models.FloatField(default=0)
    bid_total = models.FloatField(default=0)

    class Meta:
        ordering = ('id',)


class InvoicePaymentReminderEmail(models.Model):
    invoices = models.ManyToManyField(Invoice)
    customer = models.ForeignKey(CustomerOrganization,on_delete=models.SET_NULL, null=True, blank=True)
    reminder_date = models.DateField(auto_now_add=True)
    added_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='invoice_payment_reminder_email')



class DraftInvoiceChangesStore(models.Model):
    draft_invoice = models.ForeignKey(DraftInvoice, null=True, on_delete=models.CASCADE)
    approved_date = models.DateTimeField(null=True)
    approved_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='draft_invoice_create_update_approved_approved_by')
    payload_data = models.JSONField(max_length=10000, null = True)

    # Common relation Fields
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='draft_invoice_create_update_approved_created_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)



class DraftInvoiceNotes(models.Model):
    draft_invoice = models.ForeignKey(DraftInvoice, null=True, on_delete=models.CASCADE)
    notes = models.TextField(null=True, blank=True)

    # Common relation Fields
    created_by = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='draft_invoice_notes_created_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

