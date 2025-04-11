from django.urls import path
from SupplierInviteOnProject import views

urlpatterns = [

    # Supplier Organization urls
    path('supplier-invite/<str:project_number>', views.SupplierInvoiceView.as_view()),

    path('supplier-reminder/<str:project_number>', views.SuppliersReminderView.as_view()),
    
    path('supplier-midfield-update/<str:project_group_number>', views.SuppliersMidfieldUpdateView.as_view()),
]