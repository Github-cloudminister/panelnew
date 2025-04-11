from django.contrib import admin

from ClientSupplierInvoicePayment.models import ClientPaymentReceipt, ClientPaymentReceiptInvoiceLinking

# Register your models here.

admin.site.register(ClientPaymentReceipt)
admin.site.register(ClientPaymentReceiptInvoiceLinking)
