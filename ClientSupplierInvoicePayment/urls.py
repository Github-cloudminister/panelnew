from django.urls import path
from ClientSupplierInvoicePayment.views import ClientPaymentReceiptCreateListAPI, ClientPaymentReceiptRetrieveAPI

app_name = "clientsupplierinvoicepayment"


urlpatterns = [

    path('clientpaymentreceipt/retrieve/<int:id>', ClientPaymentReceiptRetrieveAPI.as_view()),

    path('clientpaymentreceipt/create-list/', ClientPaymentReceiptCreateListAPI.as_view()),

]