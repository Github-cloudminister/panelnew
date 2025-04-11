from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path
from CompanyBankDetails import views

urlpatterns = [
    path('company-invoice-bank-detail', views.CompanyInvoiceDataView.as_view({'get':'list', 'post':'create'})),

    path('company-invoice-bank-detail/<int:id>', views.CompanyInvoiceDataView.as_view({'get':'retrieve', 'put':'update'})),

    path('company-detail-data', views.CompanyDetailsDataView.as_view({'get':'list', 'post':'create'})),
    
    path('company-detail-data/<int:id>', views.CompanyDetailsDataView.as_view({'get':'retrieve', 'put':'update'})),

]

urlpatterns = format_suffix_patterns(urlpatterns)