from Prescreener.models import ProjectGroupPrescreener
from django.urls import path
from .views import *

app_name = "SupplierBuyerAPI"

urlpatterns = [
    
        #SupplierBuyer Enable/Disable
        path('supplierbuyer/enable-disable/<int:id>/<int:supplier_type>',SupplierBuyerEnableDisable.as_view()),

        # ClientDBCountryLanguageMapping API
        path('CountryLanguage/ReferenceData/Cultures',GetSupplierBuyerCountryLangAPI.as_view()),

        #TranslatedQuestion API
        path('QuestionsAndAnswersData/ReferenceData/Qualifications',GetQualificationsAPI.as_view()),

        #All ProjectGroupSupplier Survey GET
        path('ExternalSurveys/ReferenceData/SamplingService',SupplierBuyerSurveyGetAPI.as_view()),
        
        #Survey Qualifications by project_group_number
        path('GetSurveyQuotas/ReferenceData/Qualifications/<str:project_group_number>',GetSurveyQuotasAPI.as_view()),

        #SurveyStatistics by project_group_number
        path('GetSurveyStatistics/ReferenceData/<str:project_group_number>',GetSurveyStatistics.as_view()),

        #GET Survey URL and Validate User Response
        # path('GetFetchSurveyURL/ReferenceData/<str:project_group_number>',GetFetchSurveyURLAPI.as_view()),

        # This is Autocreate Surveys objects in SurveyBuyerProjectGroup
        path('supplierbuyer-projectgroup-create',SupplierBuyerProjectGroupCreateView.as_view()),
]