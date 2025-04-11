from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path
from Invoice import views

urlpatterns = [

    path('invoice', views.InvoiceList.as_view()),

    path('invoice/create', views.CreateInvoice.as_view()),

    path('invoice/number/get', views.GetInvoiceNumber.as_view()),

    path('invoice/customer/<int:cust_org_id>', views.CustomerOrganizationReconciledProjectView.as_view()),

    path('invoice/project-group-list', views.ProjectGroupInvoiceList.as_view()),

    path('invoice/<str:invoice_number>/status', views.InvoiceUpdateStatusView.as_view()),

    path('invoice/<str:invoice_number>/edit', views.InvoiceUpdateView.as_view()),

    path('invoice-row/create', views.InvoiceRowView.as_view()),
    
    path('invoice-row/<int:invoice_row_id>/edit', views.InvoiceRowUpdateView.as_view()),

    path('invoice/<str:invoice_number>/pdf', views.InvoicePdfView.as_view()),
    path('invoicehtml', views.invoiceHTML.as_view()),

    # Multiple Invoice Data Download In Single PDF 
    path('multiple-invoice-data/pdf', views.MulitpleInvoiceInSinglePdfDownload.as_view()),

    # Send Email Invoice PDF
    path('invoice/send-email', views.SendInvoicePdfEmailView.as_view()),

    # Download All Invoice CSV
    path('invoice/invoice-xls-download', views.InvoiceListXLSDownload.as_view()),

    # Download Invoice Row XLSX
    path('invoice/invoicerow-xlsx-download', views.InvoiceRowsXLSXDownload.as_view()),

    # Download Invoice Data By Project
    path('invoice/invoice-byproject-xlsx', views.InvoiceByProjectXLSX.as_view()),


    # DRAFTINVOICE AND DRAFTINVOICEROW APIS
    path('draftinvoice-rows/multiple/create', views.DraftInvoiceAndRowsCreate.as_view()),

    path('draft-invoice-list', views.DraftInvoiceListView.as_view()),

    path('draft-invoice-status-update', views.DraftInvoiceStatusUpdateView.as_view()),

    path('draft-invoice-row-list', views.DraftInvoiceRowsListView.as_view()),

    path('draft-invoice-update/file-upload/<int:pk>', views.DraftInvoiceUpdateFileUploadView.as_view()),

    path('draft-invoice/get-counts', views.DraftInvoiceGetCounts.as_view()),

    path('draft-invoice-list-stats/approved-status', views.ListDraftInvoiceStatsApprovedStatus.as_view()),

    path('draft-invoice-row-list-by-project', views.DraftInvoiceRowsListByProjectView.as_view()),

    path('draft-invoice-row-delete', views.DraftInvoiceRowsDeleteAPI.as_view()),

    #INVOICE PAYEMNT REMINDER EMAIL SENDING & CREATING TABLE DATA IN THIS API
    path('invoice/payment-reminder/email', views.InvoicePaymentReminderEmailView.as_view()),

    path('invoice-po-wise/payment-reminder/email', views.InvoiceListPaymentReminderEmailView.as_view()),

    path('invoice/<int:invoice_id>/delete', views.InvoiceDeleteView.as_view()),

    path('invoice/receivable-amount/<str:customer_id>', views.TotalOverDueReceivablesView.as_view()),

    path('invoice/payable-amount/<str:customer_id>', views.TotalOverDuePayablesView.as_view()),

    path('invoice-revert/<str:invoice_number>', views.InvoiceRevertApi.as_view()),

    path('invoice/due-date-reminder', views.CustomerInvoiceDueDateReminderList.as_view()),
    
    path('customer-reminder-invoice-list/<str:customer_id>/<str:invoice_currency_id>', views.CustomerWiseInvoiceDueDateList.as_view()),
    
    path('invoice/companyupdate', views.InvoiceCompanyUpdate.as_view()),

    path('draft-invoice-revert/<int:project_id>/<int:draftinvoice_id>', views.DraftInvoiceRevert.as_view()),
    
    path('invoice/month-wise-email-sent', views.InvoiceListSendEmailMonthWiseAPI.as_view()),

    path('invoice/draft-invoice-notes/<int:draft_invoice_id>', views.DraftInvoiceNotesAPI.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns)