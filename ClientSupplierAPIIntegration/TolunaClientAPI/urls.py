from django.urls import path
from ClientSupplierAPIIntegration.TolunaClientAPI.tests import FecthSurveysFromTolunaSideAPI, FecthSurveysFromZampliaSideAPI
from ClientSupplierAPIIntegration.views import *
from .views import *



app_name = "TolunaClientAPI"


urlpatterns = [

    path('add-default-supply-source', CustomerDefaultSupplySourcesAPI.as_view()),

    path('get-default-supply-source', getCustDefaultSupplySourceAPI.as_view({'get':'list','put':'update'})),

    path('update-multiple-default-supply-sources', UpdateMultipleCustomerDefaultSupplySourcesAPI.as_view()),
    ## ************** Default Sub Supplier API ************** 
    path('add-default-sub-supply-source', CustomerDefaultSubSupplySourcesAPI.as_view()),

    path('get-default-sub-supply-source', getCustDefaultSubSupplySourceAPI.as_view({'get':'list','put':'update'})),

    path('update-multiple-default-sub-supply-sources', UpdateMultipleCustomerDefaultSubSupplySourcesAPI.as_view()),
    
    path('survey-supplier/client-survey-toluna-quota-update', ClientSurveyQuotaUpdateView.as_view()), # Individual Client Quotas Update From Toluna Side
    
    # path('survey-supplier/all-client-survey-quota-update', AllClientSurveyQuotaUpdateView.as_view()), # All Client Quotas Update From Toluna/Zamplia Side

    path('list-surveys', ClientSurveysListAPI.as_view()),
    
    path('list-client-db-country-lang', ListClientDBCountryLanguageAPI.as_view()),

    path('total-customer-revenue', TotalCustomerRevenueMonthWiseCountApi.as_view()),

    path('total-supplier-revenue', TotalSupplierRevenueMonthWiseCountApi.as_view()),

    path('client-survey-quotas', ClientSurveyWiseQuotasDataView.as_view()),

    path('client-supply-Prescreener', ClientSurveyWisePrescreenerQuestionDataView.as_view()),

    # Project Group Status Update
    path('client-survey-status-update', ClientSupplyProjectGroupStatusUpdateView.as_view()),

    path('client-survey-wise-supplier', ClientProjectGroupSupplierDataView.as_view()),

    #toluna side API given for Survey and Quota Update notifications
    path('toluna/quota/notifications/<str:projectcode>', TolunaPostQuotaUpdateNotifications.as_view()),

    path('toluna/Survey/notifications/<str:projectcode>', TolunaPostSurveyNotifications.as_view()),

    #get API for Customer Survey Params Get in Customer default params set
    path('get-survey-qualify-params/<int:customerOrg>', RetrieveSurveyQualifyParametersAPI.as_view()),

    #create/Update Customer Survey Params
    path('survey-qualify-params-setup', SurveyQualifyParametersSetupAPI.as_view()),

    #get CountryLang for celery, based on survey fetch
    # path('country-lang-send-to-celery-for-survey-fetch', CountryLangSendToCeleryForSurveyFetch.as_view()),

    #get customer survey params for get or accept surveys in celery
    # path('survey-qualify-parameters-check', SurveyQualifyParametersCheckAPI.as_view()),

    # get survey from celery to pvp with proper mapping and need to create/update by this API
    # path('client-survey-lists-celery-pvp', ClientSurveyListCeleryAPI.as_view()),

    # pause surveys from celery to PVP 
    # path('client-survey-pause', ClientSurveysPause.as_view()),

    # Live client Suppliers when survey is Live Again from celery to PVP
    # path('client-survey-supplier-live', ClientSurveySupplierlive.as_view()),

    # create/update quotas from celery to PVP
    # path('client-survey-of-quotas-lists-celery-pvp', ClientSurveyOfQuotasListCeleryAPI.as_view()),
    
    # add Default Supplier in client surveys from celery to PVP
    # path('add-update-default-supplier', AddUpdateDefaultSupplier.as_view()),



    #this 2 API Is Only for Testing  
    # path('survey-supplier/fetch-surveys-from-toluna-side', FecthSurveysFromTolunaSideAPI.as_view()),
    # path('survey-supplier/fetch-surveys-from-zamplia-side', FecthSurveysFromZampliaSideAPI.as_view())
]