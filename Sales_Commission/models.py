from django.db import models
from Customer.models import Currency
from Invoice.models import InvoiceRow
from employee.models import EmployeeProfile
from Project.models import *


class Sales_Commission(models.Model):
    Sales_choices = (
        ('Draft', 'Draft'),
        ('Paid', 'Paid'),
        ('Cancelled', 'Cancelled'),
    )   
    
    sales_person = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE)
    commission_amount = models.FloatField(default=0)
    total_commision_amount = models.FloatField(default=0)
    currency = models.ForeignKey(Currency,on_delete=models.CASCADE)
    payment_date = models.DateField()
    status = models.CharField(max_length=225,choices=Sales_choices)


class Sales_Commission_Rows(models.Model):
    sales_commision = models.ForeignKey(Sales_Commission,on_delete=models.CASCADE)
    project = models.OneToOneField(Project, on_delete=models.CASCADE, null=True)
    commission_row_amount = models.FloatField(default=0)
    invoice_amount = models.FloatField(default=0)
    invoice_row = models.ForeignKey(InvoiceRow,on_delete=models.SET_NULL,null=True)
