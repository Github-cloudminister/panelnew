from django.urls import path
from affiliaterouter.views import *

app_name = "affiliaterouter"

urlpatterns = [

    path('crud-questionsdata', QuestionsDataTableCrud.as_view(), name='crud-questionsdata'),

    path('identify-country', identifyCountry.as_view()),

    path('questions-answers', AffiliateRouterQuestionsAnswers.as_view()),

    path('surveyside-redirect', SurveySideRedirectAPI.as_view()),       # SurveyNumber Available

    path('surveyside-decision/<str:visitorid>', SurveySideDecisionAPI.as_view()),

    path('affiliate-redirect-survey-data', AffialiateRouterProjectGroupData.as_view(), name='survey_data_view'),

    path('routing-priority', RountingPriorityView.as_view()),

    path('re-routing-user-register', ReRountingUserRegister.as_view()),

    path('re-routing-user-counts', ReRountingUserCounts.as_view()),

]