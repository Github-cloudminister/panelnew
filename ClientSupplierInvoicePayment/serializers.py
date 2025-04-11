from rest_framework import serializers
from ClientSupplierInvoicePayment.models import ClientPaymentReceipt, ClientPaymentReceiptInvoiceLinking


class ClientPaymentReceiptInvoiceLinkingSerializer(serializers.ModelSerializer):
    invoice_number = serializers.ReadOnlyField(source="invoice.invoice_number")
    invoice_date = serializers.ReadOnlyField(source="invoice.invoice_date")
    invoice_total_amount = serializers.ReadOnlyField(source="invoice.invoice_total_amount")
    class Meta:
        model = ClientPaymentReceiptInvoiceLinking
        fields = ['id', 'invoice','invoice_number','invoice_date','invoice_total_amount','payment_received_amount','tds_amount']


    
class ClientPaymentReceiptSerializer(serializers.ModelSerializer):
    receiptinvoicelinking = ClientPaymentReceiptInvoiceLinkingSerializer(many=True, source='clientpaymentreceiptinvoicelinking_set', read_only=True)
    cust_org_name = serializers.CharField(source='customer_org.cust_org_name', read_only=True)
    bank_account_name = serializers.ReadOnlyField(source="bank_account.bank_name")
    currency_name = serializers.ReadOnlyField(source="currency.currency_iso")

    class Meta:
        model = ClientPaymentReceipt
        fields = ['id', 'customer_org', 'cust_org_name', 'payment_receipt_amount','bank_charges','payment_receipt_date','payment_reference','payment_description','bank_account','bank_account_name','currency','currency_name', 'receiptinvoicelinking']