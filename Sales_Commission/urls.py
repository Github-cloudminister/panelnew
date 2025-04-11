from django.urls import path, include

from Sales_Commission.views import *

app_name = "Sales_Commission"

urlpatterns = [

    path('sales-list', SalesCommissionListView.as_view(), name="sales_list_view"),

    path('sales/invoicerow', InvoiceRowViewSet.as_view({'get': 'list'}), name="InvoiceRowViewSet"),

    path('sales/sales_commission', Sales_CommissionViewSet.as_view({'get': 'list', 'post':'create'}), name="Sales_CommissionViewSet"),

    path('sales-commission-fetch-data/<int:id>', SalesCommissionUpdateView.as_view()),

    path('sales-commission-delete-data/<int:id>', SalesCommissionRowsDeleteApi.as_view({'delete':'destroy'})),


]