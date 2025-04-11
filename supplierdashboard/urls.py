from django.urls import path
from supplierdashboard.views import *

app_name = "supplierdashboard"

urlpatterns = [
    path('supplierdashboard/login', SupplierDashboardLoginApiView.as_view(), name="supplier_dashboard_login"),

    path('supplierdashboard/supplierlist', supplierList.as_view({'get':'list'})),

    path('supplierdashboard/projectlist/Live', projectList.as_view({'get':'list'})),

    path('supplierdashboard/projectlist/Awarded', awardedprojectList.as_view({'get':'list'})),

    path('supplierdashboard/projectlist/Closed', closedprojectList.as_view({'get':'list'})),

    path('supplierdashboard/projectlist/Finalized', finalizedprojectList.as_view({'get':'list'})),

    path('supplierdashboard/projectdetails/<str:project_group_number>', supplierAdd.as_view({'get':'retrieve'})),

    path('supplierdashboard/projectlist/accept/<str:project_group_number>', acceptSupplierProject.as_view({'get':'list','post':'create'})),
    
    path('supplierdashboard/projectfinalids', downloadFinalIds.as_view({'get':'list'})),

    path('supplierdashboard/project-list', SearchProjectListView.as_view({'get':'list'})),

    path('supplierdashboard/project-status-data', ProjectStatusWiseDataView.as_view({'get':'list'})),

    path('supplierdashboard/project-status-live', SupplierProjectLiveView.as_view({'get':'list'})),

    path('supplierdashboard/project-status-closed', SupplierProjectClosedView.as_view({'get':'list'})),

    path('supplierdashboard/project-status-finalized', SupplierProjectFinalizedView.as_view({'get':'list'})),

    path('supplierdashboard/stats-aggregate-counts', SupplierStatsAggregateCountsAPI.as_view()),

    path('supplierdashboard/country', SupplierDashboardCountryView.as_view()),

    path('supplierdashboard/language', SupplierDashboardLanguageView.as_view()),

    path('supplierdashboard/zip_code-list-view/<int:project_group_number>', ZipCodeListView.as_view()),

    path('supplierdashboard/survey-prescreener-list-view/<int:survey_number>', SurveyPreScreenerListView.as_view()),

    path('supplierdashboard/finalidsprojectlist/<str:supcode>/<str:project_list_code>', finalidsProjectListView.as_view()),

    path('supplierdashboard/project-final-ids/<str:project_id>/<str:supplier_id>',ProjectFinalidsDataView.as_view()),
    
    path('supplierdashboard/supplier-data-view', SupplierDashboardSupplierDataView.as_view(), name="supplier_data_view"),
    
    path('supplierdashboard/supplier-update-view/<int:supplierOrg_id>', SupplierDashboardSupplierUpdateView.as_view(), name="supplier_data_update_view"), 
    
    path('supplierdashboard/supplier-contact-view/<int:supplierOrg_id>', SupplierContactDataView.as_view(), name="supplier_contact_fetch_view"), 
    
    path('supplierdashboard/supplier-contact-update-view/<int:supplier_contact_id>', SupplierContactUpdateDataView.as_view(), name="supplier_contact_update_view"), 

    # SupplierSide Invoice List GET API
    path('supplierdashboard/supplier-invoice-get/<int:invoiceid>', SupplierInvoiceGet.as_view()),
    
    # SupplierSide Invoice List API
    path('supplierdashboard/supplier-invoice-list', SupplierInvoiceDataView.as_view(), name="supplier_invoice_list_view"), #Done
    
    # SupplierSide Invoice Row List API
    path('supplierdashboard/supplier-invoice', SupplierWiseSupplierInvoiceRowDataView.as_view(), name="supplier_invoice_create_view"),

    # SuppliserSide Company List
    path('supplierdashboard/company-detail-data', SupplierCompanyDetailsDataView.as_view({'get':'list'})),
    
    # SuppliserSide Invoice Create/Update
    path('supplierdashboard/invoice-create-update', SupplierInvoiceCreateUpdateDataView.as_view()),

    # SuppliserSide Currency list
    path('supplierdashboard/invoice-currency', SupplierInvoiceCurrencyDataView.as_view()),

    # get Supplier Currency
    path('supplierdashboard/supplier-invoice-data', SupplierInvoiceCurrencyGET.as_view()),

    path('supplierdashboard/stats-day-wise-count', StatsLastSevenDayCountCompleteClicksView.as_view()),

    path('supplierdashboard/forgot-password', SupplierUserForgotPasswordAPI.as_view()),

    path('supplierdashboard/set-password/<str:token>', SupplierUserSetPasswordAPI.as_view()),

    path('supplierdashboard/change-password/<int:user_id>', SupplierUserChangePasswordAPI.as_view()),

    path('supplierdashboard/user-register-api', EngninxSupplierUserRegisterScriptAPI.as_view()),

    path('supplierdashboard/employee-list', SupplierDashboardEmployeeListAPI.as_view()),

    path('supplierdashboard/employee-source-update', EmployeeSourceIDUpdateAPI.as_view()),

]