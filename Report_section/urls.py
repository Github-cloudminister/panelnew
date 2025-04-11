from django.urls import path
from Report_section import views

urlpatterns = [

    path('report/project-manager-work-load', views.ProjectManagerProjectList.as_view()),

    path('report/sales-executive', views.ProjectManagerSalesProjectList.as_view()),

    path('report/customer/<int:customer_id>', views.CustomerReportingView.as_view()),

    path('report/project-manager/revenue-expense/supplier', views.ProjectstWithRevenueExpenseSupplier.as_view()),

    path('report/customer', views.CustomerReportwithDate.as_view()),

    path('report/supplier', views.SupplierReportwithDate.as_view()),

    path('report/supplier-revenue-per-month', views.SupplierRevenuePerMonth.as_view()),

    path('report/clientwise-invoicing-revenue-per-month', views.ClientwiseInvoicingRevenuePerMonth.as_view()),
    
    path('report/clientwise-locked-pending-revenue-per-month', views.ClientwiseLockedPendingRevenuePerMonth.as_view()),
    
    path('report/supplierfinalids', views.SupplierFinalidsbyDate.as_view()),    # supplier final ids
]