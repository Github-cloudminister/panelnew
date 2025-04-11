from django.urls import path
from Ad_Panel_Dashboard.views import *


app_name = "Ad_Panel_Dashboard"

urlpatterns = [
    path('adpaneldashboard/supplier-contact/<int:supp_contact_id>', SubSupplierContactDashboardRegistrationView.as_view()),

    path('adpaneldashboard/supplier-contact/re-send-email/<int:supp_contact_id>', sub_supplierUserRegistrationReSendEmailPasswordLink.as_view()),

    path('adpaneldashboard/project-list', ProjectGroupADEnabledList.as_view()),

    path('adpaneldashboard/projectlist/Live/<str:sub_sup_code>', projectList.as_view({'get':'list'})),

    path('adpaneldashboard/projectlist/Closed/<str:sub_sup_code>', closedprojectList.as_view({'get':'list'})),

    path('adpaneldashboard/projectlist/new-available/<str:sub_sup_code>', NewProjectSurveyAvailableList.as_view({'get':'list'})),

    path('adpaneldashboard/projectlist/Finalized/<str:sup_code>', finalizedprojectList.as_view({'get':'list'})),

    path('adpaneldashboard/stats-aggregate-counts/<str:sub_sup_code>', SubSupplierStatsAggregateCountsAPI.as_view()),

    path('adpaneldashboard/days-wise-counts/<str:sub_sup_code>', StatsCountCompleteClicksView.as_view()),

    path('adpaneldashboard/survey-prescreener-list-view/<int:survey_number>', SurveyPreScreenerListView.as_view()),

    path('adpaneldashboard/finalidsprojectlist/<str:supcode>/<str:project_list_code>', finalidsProjectListView.as_view()),

    path('adpaneldashboard/project-final-ids/<str:project_id>/<str:supplier_id>', ProjectFinalidsDataView.as_view()),

    path('adpaneldashboard/projectdetails/<str:sub_sup_code>/<str:project_group_number>', subsupplierupdate.as_view({'get':'retrieve'})),

    path('adpaneldashboard/subsupplier-list', SubSupplierList.as_view()),

    path('adpaneldashboard/add-adpanel-supplier/<int:project_group_id>', ADPanelSupplierADD.as_view()),

    path('adpaneldashboard/project-group/sub-supplierWithstat-2/<int:project_group_num>', ADPanelSubSupplierWithStat2View.as_view()),

    path('adpaneldashboard/sub-supplier-redirecturl/<int:project_group_sub_supplier_id>', SubSupplierRedirectUrlView.as_view()),

    path('adpaneldashboard/report/sub-supplier', SubSupplierReportwithDate.as_view()),  ## Sub Supplier Report

    path('adpaneldashboard/sub-supplier-data-download/<str:project_number>', ADPanelProjectGroupSubJsonDataApiView.as_view()),  ## Sub Supplier Data Download

    path('adpaneldashboard/country', SupplierDashboardCountryView.as_view()),
    
    path('adpaneldashboard/language', SupplierDashboardLanguageView.as_view()),
]