from django.urls import path
from Surveyentry.views import *

app_name = "Surveyentry"

urlpatterns = [

    path('',healtcheck.as_view()), ## Warning!..Don't Delete This API ##

    path('survey-api', SurveyEntryAPIView.as_view()),

    path('survey-status-check-api/<str:urlsafe_str>', SurveySecurityCheckAPIView.as_view()),

    path('survey-api-answer-file/<str:url_string>', SurveyEntryAnswerFileUpload.as_view()),

    path('survey-api2/pre/<str:url_string>', SurveyPrescreenerAPIView2.as_view()),

    path('survey-api3/pre/<str:url_string>', SurveyPrescreenerAPIView3.as_view()), # for Language Agreement static Question

    path('survey-api/pre/supplierredirect/<str:url_string>', SupplierTerminateRedirectAPIView.as_view()),

    path('survey-api/pre/clientredirect/<str:url_string>', ClientRedirectAPIView.as_view()),

    path('survey-api/quota/check-available-quota/<str:url_string>', validateQuotaEligibilityAPI.as_view()),

    path('survey-api/member-management/fetch-url/<str:url_string>', fetchURLAPI.as_view()),

    path('survey-api/pre/suppliersideredirect/<str:url_string>', SupplierSideTerminateRedirectAPIView.as_view()),

    path('routingtrafficapi/<str:url_safe_string>', TrafficRoutingAPIView.as_view()),

    path('survey-api/clientsupplier-redirect-check/<str:url_string>', SurveyFinalizedAPI.as_view()),
    
    path('survey-api/research-defender-search', ResearchDefenderSearchView.as_view()),  # Research Defender Search by Survey Number 

    path('survey-api/survey-decision', SurveyEntryDecision.as_view()),

    path('survey-api/get-questions-answers', SurveyEntryGetQuestionAnswers.as_view()),
]
