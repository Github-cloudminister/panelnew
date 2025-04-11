from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from Surveyentry.views import healtcheck

urlpatterns = [

    path('',healtcheck.as_view()), ## Warning!..Don't Delete This API ##

    # Django admin urls
    path('admin/', admin.site.urls),

    # initial-setup app urls
    path(settings.APP_PATH, include('InitialSetup.urls')),

    # employee app urls
    path(settings.APP_PATH, include('employee.urls')),

    # bid app urls
    path(settings.APP_PATH, include('Bid.urls')),

    # Customer app urls
    path(settings.APP_PATH, include('Customer.urls')),

    # Supplier app urls
    path(settings.APP_PATH, include('Supplier.urls')),

    # Project app urls
    path(settings.APP_PATH, include('Project.urls')),

    # Data Download app urls
    path(settings.APP_PATH, include('DataDownload.urls')),

    # Questions app urls
    path(settings.APP_PATH, include('Questions.urls')),

    # Prescreener app urls
    path(settings.APP_PATH, include('Prescreener.urls')),

    # Reconciliation app urls
    path(settings.APP_PATH, include('reconciliation.urls')),

    # TolunaClientAPI app urls
    path(settings.APP_PATH, include('ClientSupplierAPIIntegration.TolunaClientAPI.urls')),

    # ZampliaClientAPI app urls
    path(settings.APP_PATH, include('ClientSupplierAPIIntegration.ZampliaClientAPI.urls')),

    # Surveyentry app urls
    path('v2/', include('Surveyentry.urls')),

    # Landing Page app urls
    path('', include('Landingpage.urls')),

    # Invoice app urls
    path(settings.APP_PATH, include('Invoice.urls')),
    
    # Supplier Dashboard urls
    path(settings.APP_PATH, include('supplierdashboard.urls')),

    # AffiliateRouter app urls
    path(f'{settings.APP_PATH}affiliaterouter/', include('affiliaterouter.urls')),
    
    # SupllierAPI app urls
    path(settings.APP_PATH, include('SupplierAPI.urls')),
    
    # SupplierRouter app urls
    path(settings.APP_PATH, include('SupplierRouter.urls')),
    
    # SupplierRouter app urls
    path(settings.APP_PATH, include('Report_section.urls')),

    # Recontact_Section app urls
    path(settings.APP_PATH, include('Recontact_Section.urls')),

    # Supplier Final IDS Email urls
    path(settings.APP_PATH, include('Supplier_Final_Ids_Email.urls')),

    # Question Mapping SupplierAPI urls
    path(settings.APP_PATH, include('QuestionSupplierAPI.urls')),
    
    # Question Mapping scrubsupplierids urls
    path(settings.APP_PATH, include('scrubsupplierids.urls')),
    
    # Admin Dashboard urls
    path(settings.APP_PATH, include('AdminDashboard.urls')),

    # Supplier Invoice urls
    path(settings.APP_PATH, include('SupplierInvoice.urls')),

    # SupplierBuyerAPI urls
    path('', include('SupplierBuyerAPI.urls')),
    
    # Supplier Invite On Project urls
    path(settings.APP_PATH, include('SupplierInviteOnProject.urls')),
    
    # Company Bank Details urls
    path(settings.APP_PATH, include('CompanyBankDetails.urls')),

    # Client Supplier Invoice Payment urls
    path(settings.APP_PATH, include('ClientSupplierInvoicePayment.urls')),

    # Panel Integration urls
    path(settings.APP_PATH, include('PanelIntegration.urls')),

    # Sales_CommissionViewSet
    path(settings.APP_PATH, include('Sales_Commission.urls')),

    # AD Panel Dashboard urls
    path(settings.APP_PATH, include('Ad_Panel_Dashboard.urls')),

    # Email Template App Urls
    path(settings.APP_PATH, include('email_template_app.urls')),

    # Notifications App Urls
    path(settings.APP_PATH, include('Notifications.urls')),
    
    # Backup App Urls
    path(settings.APP_PATH, include('backup.urls')),
    
    path('', include('AutomationAPI.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATICFILES_DIRS)
