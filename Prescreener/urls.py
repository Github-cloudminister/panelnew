from django.urls import path

from rest_framework.urlpatterns import format_suffix_patterns

from Prescreener import views


urlpatterns = [

    # get and post prescreener with project_group_number urls
    path('survey-prescreener/<int:project_group_number>', views.SurveyPreScreenerView.as_view()),
    
    path('survey-prescreener/v2/<int:project_group_number>', views.SurveyPreScreenerV2View.as_view()),

    path('survey-dique-prescreener-get-update/<int:project_group_number>', views.SurveyDiquePreScreenerView.as_view()),

    path('survey-lucid-prescreener-get-list/<int:project_group_number>', views.SurveyLucidPreScreenerView.as_view()),

    # update and delete prescreener 
    path('survey-prescreener/edit/<int:prescreener_question_id>', views.SurveyPreScreenerUpdatesView.as_view()),

    # delete prescreener urls
    path('survey-prescreener/delete/<int:prescreener_question_id>', views.SurveyPreScreenerDeleteView.as_view()),

    # get prescreener with project_group_number urls
    path('prescreener-questions-list/<int:project_group_number>', views.PrescreenerQuestionListView.as_view()),

    path('prescreener-answer-list/<int:transalted_question_id>', views.PrescreeneranswerView.as_view()),

    # get prescreener with project_group_number and answer_id urls
    path('survey-prescreener/api/v2/<int:project_group_number>', views.SurveyPreScreenerApiView.as_view()),

    path('prescreener-supplier/enabled/<int:proj_grp_supplier>', views.SupplierPrescreenerEnabledAPI.as_view()),

    # get project group prescreener question copy urls
    path('projectgroupprescreenercopyview/<int:old_project_group_id>/<int:new_project_group_id>', views.ProjectGroupPrescreenerCopyView.as_view()),

    path('prescreener-sequence-update/<int:project_group_number>', views.PrescreenerSequenceUpdateApi.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns)