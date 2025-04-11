from django.db import models
from CompanyBankDetails.models import CompanyInvoiceBankDetail
from Customer.models import CustomerOrganization
from Invoice.models import Invoice
from Customer.models import Currency




class ClientPaymentReceipt(models.Model):

    customer_org = models.ForeignKey(CustomerOrganization, on_delete=models.CASCADE)
    payment_receipt_amount = models.FloatField()
    bank_charges = models.FloatField()
    payment_receipt_date = models.DateField()
    payment_reference = models.CharField(max_length=255, null=True, blank=True)
    payment_description = models.TextField(null=True)
    bank_account = models.ForeignKey(CompanyInvoiceBankDetail, on_delete=models.CASCADE, null=True)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, null=True)


class ClientPaymentReceiptInvoiceLinking(models.Model):

    client_payment_receipt = models.ForeignKey(ClientPaymentReceipt, on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    payment_received_amount = models.FloatField()
    tds_amount = models.FloatField()
