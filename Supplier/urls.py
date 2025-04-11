from django.urls import path
from Supplier import views

urlpatterns = [

    # Supplier Organization urls
    path('supplier', views.SupplierView.as_view()),

    path('supplier/<int:supplier_id>', views.SupplierUpdateView.as_view()),

    # Supplier Organization urls
    path('subsupplier', views.SubSupplierView.as_view()),

    path('subsupplier/<int:subsupplier_id>', views.SubSupplierUpdateView.as_view()),

    # Supplier Contact urls
    path('supplier-contact', views.SupplierContactView.as_view()),

    path('supplier-contact/<int:supplier_contact_id>',views.SupplierContactUpdateView.as_view()),

    path('subsupplier-contact', views.SubSupplierContactView.as_view()),

    path('subsupplier-contact/<int:subsupplier_contact_id>',views.SubSupplierContactUpdateView.as_view()),

    # Supplier wise Contact urls
    path('supplier/contact/<int:supplier_id>',views.SupplierDetailContactView.as_view()),
         
    # Sub Supplier wise Contact urls
    path('sub-supplier/contact/<int:sub_supplier_id>',views.SubSupplierDetailContactView.as_view()),

     # SupplierOrgAuthKeyDetails urls
    path('api-supplier/authkey-details', views.SupplierOrgAuthKeyDetailsView.as_view()),

    path('api-supplier/authkey-details/<int:pk>', views.SupplierOrgAuthKeyDetailsUpdateView.as_view()),

    # SupplierInvoicingDetailsView urls
    path('supplier/invoicing-details', views.SupplierInvoicingDetailsView.as_view()),

    path('supplier/invoicing-details/<int:pk>', views.SupplierInvoicingUpdateView.as_view()),

    #LucidAPI Country Language Table Synchronization
    path('api-supplier/country-language-sync', views.LucidAPICountryLanguageSync.as_view()),

    path('supplier/supplier-contact/<int:supp_contact_id>', views.SupplierContactDashboardRegistrationView.as_view()),

    path('supplier/supplier-contact/reset-password/<int:supp_contact_id>', views.SupplierContactDashboardResetPasswordView.as_view()),

    path('supplier/supplier-contact/re-send-email/<int:supp_contact_id>', views.UserRegistrationReSendEmailPasswordLink.as_view()),

    # Supplier's PrjGrpSupplier-Wise RespondentStats
    path('supplier/prjgrp-supp/resp-stats',views.SupplierPrjGrpSuppRespStats.as_view()),

     # Supplier Invoice Approval Email
    path('supplier/invoice-approval/email',views.SupplierInvoiceApprovalEmailView.as_view()),

    # Supplier enable/disable 
    path('supplier/block',views.SupplierStatusUpdateView.as_view()),
    
    # SubSupplier enable/disable 
    path('subsupplier/block',views.SubSupplierStatusUpdateView.as_view()),
    
    #projectgroup sub supplier live/paused  
    path('subsupplier/status/list',views.SubSupplierStatusListView.as_view()),

    #projectgroup sub supplier live/paused  
    path('subsupplier/redirects/get/update/<int:projectgroupid>/<int:subsupplierid>',views.SubSupplierRedirectGetUpdateView.as_view()),

]