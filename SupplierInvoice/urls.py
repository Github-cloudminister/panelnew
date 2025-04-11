from django.urls import path
from SupplierInvoice.views import *
from rest_framework.urlpatterns import format_suffix_patterns

app_name = "supplierinvoice"

urlpatterns = [

    # SupplierInvoice url
    path('supplier-invoice', SupplierInvoiceListView.as_view({'get':'list'}), name="supplier_invoice_list"),

    path('supplier-invoice/amount-by-date-list', SupplierInvoiceAmountByDateListView.as_view(), name="supplier_invoices_amountby_date"),

    path('supplier-invoice/bulk-update/<int:supplierOrg_id>', SupplierInvoiceBulkUpdateView.as_view(), name="supplier_invoice_bulk_update"),

    path('supplier-invoice/invoice-verify/<int:supplierOrg_id>', SupplierInvoiceVerificationView.as_view(), name="supplier_invoice_invoice_verify"),

    path('supplier-invoice/suppinv-retrieve-update/<int:invoiceid>', SupplierInvoiceRetrieveUpdateView.as_view(), name="supplier_invoice_retrieve_update"),
    
    path('supplier-invoice/suppinv-row-list', ListSupplierInvoiceRowAPI.as_view()),
    
    path('supplier-invoice/suppinv-row-update-create', SupplierInvoiceRowCreateUpdateAPI.as_view(), name="supplier_invoice_update_create_view"),

    # Download SupplierInvoice Row XLSX
    path('supplier-invoice/suppinv-row-xlsx-download', SupplierInvoiceRowsXLSXDownload.as_view()),

    path('supplier-invoice/client-receivable-amount/<str:supplier_id>', ClientWiseReceivablesView.as_view()),
    
    path('supplier-invoice/supplier-payable-amount/<str:supplier_id>', SupplierWisePayablesView.as_view()),
    
    path('supplier-invoice/supplier-projectwiseinvoicerow', SupplierInvoiceRowDataProjectSupplierWise.as_view()),

    path('supplier-invoice/supplierinvoice-null-row-update', SupplierInvoiceNullRowUpdateApi.as_view()),

    path('supplier-invoice/payment-reminder', PaymentReminderHTMlView.as_view()),

    # PVP side Supplier Invoice status update
    path('supplier-invoice/status-change', InvoicefieldStatusChange.as_view()),
    
    # Suplier Invoice Payment Details Update
    path('supplier-invoice/payment-details-update/<int:invoiceid>', SupplierInvoiceUpdateStatusView.as_view()),
    
    # Suplier Invoice Paid Mark
    path('supplier-invoice/stats-mark-paid', SupplierInvoicePaidMarkView.as_view()),

    # Suplier Invoice Payment Details GET 
    path('supplier-invoice/payment-details/<int:invoiceid>', InvoicePyamentDetailsView.as_view()),

    path('supplier-invoice/delete', SupplierInvoiceDeleteAPI.as_view())

]

urlpatterns = format_suffix_patterns(urlpatterns)