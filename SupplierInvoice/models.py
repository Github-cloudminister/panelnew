from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from CompanyBankDetails.models import CompanyDetails

from Supplier.models import *
from Project.models import *

# Create your models here.
class SupplierInvoice(models.Model):

    status_choices = (
        ('1', 'Received'),
        ('2', 'Paid'),
        ('3', 'Cancelled'),
        ('4', 'Approved'),
        ('5', 'Need to Clarify by PVP'),
        ('6', 'Clarification Submitted By Supplier'),
    )

    invoice_create_choices = (
        ('1', 'PanelViewPoint'),
        ('2', 'SupplierDashboard'),
    )

    supplier_org = models.ForeignKey(SupplierOrganisation, on_delete=models.CASCADE, null=True)
    company = models.ForeignKey(CompanyDetails, on_delete=models.CASCADE, null=True, blank=True)
    invoice_number = models.CharField(max_length=50, default="", null=True, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    conversion_rate = models.FloatField(default=0)
    taxable_value = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    total_from_invoice_amount = models.FloatField(default=0)
    total_invoice_amount = models.FloatField(default=0)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, null=True)
    invoice_status = models.CharField(max_length=1, choices=status_choices, default='1')
    clarification = models.TextField(default="", null=True, blank=True)
    supplier_invoice_file = models.URLField(max_length=10000,null=True,blank=True)
    created_from = models.CharField(max_length=1, choices=invoice_create_choices, default='1')


class SupplierInvoiceRow(models.Model):
    supplier_invoice = models.ForeignKey(SupplierInvoice, on_delete=models.SET_NULL,null=True, blank=True)
    supplier_org = models.ForeignKey(SupplierOrganisation, on_delete=models.CASCADE,null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE,null=True)
    invoice_received = models.BooleanField(default=False)
    cpi = models.FloatField(default=0)
    completes = models.IntegerField(null=True, blank=True)
    invoiced_completes = models.IntegerField(null=True, blank=True)
    invoiced_cpi = models.FloatField(null=True, blank=True)
    total_amount = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.project.project_number+"-"+self.supplier_org.supplier_name 
    

class SupplierInvoicePayment(models.Model):
    supplier_invoice = models.OneToOneField(SupplierInvoice, on_delete=models.CASCADE)
    gst_deductible = models.FloatField(null=True, blank=True)
    tds_receivable = models.FloatField(null=True, blank=True)
    total_payable_amount = models.FloatField(null=True, blank=True)
    date_invoice_paid = models.DateField(null=True, blank=True)
    expected_invoice_payment = models.DateField(null=True, blank=True)

class ProjectInvoicedApproved(models.Model):

    invoice_status = (
        ('1','Pending'),
        ('2','System Data CPI Mismatch'),
        ('3','System Data Approved'),
        ('4','Supplier Invoice Mismatch'),
        ('5','Approved')
    )
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    revenue = models.FloatField(null=True, blank=True)
    operationcost = models.FloatField(null=True, blank=True)
    expense = models.FloatField(null=True, blank=True)
    margin = models.FloatField(null=True, blank=True)
    invoice_approved_date = models.DateField(auto_now_add=True)
    project_invoice_status = models.CharField(max_length=2, choices=invoice_status, null=True)
    
    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='project_invoice_approved_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='project_invoice_approved_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

class ProjectSecondaryAuditApproved(models.Model):

    audit_status = (
        ('1','Pending'),
        ('2','System Data CPI Mismatch'),
        ('3','System Data Approved'),
        ('4','Supplier Invoice Mismatch'),
        ('5','Approved')
    )
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    project_audit_status = models.CharField(max_length=2, choices=audit_status, null=True)


class InvoiceFileData(models.Model):

    file = models.FileField(upload_to='supplier_invoice_pdf', max_length=500, null=True, blank=True)