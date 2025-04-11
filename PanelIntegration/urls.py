from django.urls import path
from PanelIntegration import views

urlpatterns = [
    # add projectgroup in panel
     path('project-group/<int:project_group_number>/enable-panel', views.ProjectGroupAddPanelView.as_view()),

    # Add ProjectGroup in Slick Router 
     path('project-group/<int:project_group_number>/enable-slick-router', views.ProjectGroupAddSlickRouterView.as_view()),

    # Create Email Subject Line
    path('email-subjectlines', views.EmailSubjectView.as_view({'get': 'list', 'post': 'create'}), name="email_subjectlines"),

    path('email-subjectline/<int:id>', views.UpdateEmailSubjectView.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name="update_email_subjectline"),

    # Email Invite Fetch
    path('email-invite-fetch/<int:project_group_number>', views.EmailInviteCountsView.as_view({'get': 'retrieve'}), name="email_invite_fetch"),

    path('send-invites', views.SendInvitesView.as_view({'get':'list', 'post':'create'}), name="send_invites"),

    # Panelist Completion Count
    path('panelist-completion-count/<str:source>', views.PanelistCompletionCountView.as_view({'get':'retrieve'}), name="panelist_completion_count"),

    # Panelist Survey History
    path('panelist-survey-history/<str:id>', views.PanelistSurveyHistory.as_view({'get': 'retrieve'}), name="panelist_completion_count"),

    path('survey-enabled-fetch', views.SurveyFetchForOpinionsdeal.as_view(), name="survey_enabled_fetch"),

    path('clinet-country-lang-list', views.CountryLanguageMappingListForOpinionsDealAPI.as_view(), name="client_country_lang_list"),
    
    path('panel-survey-priority', views.PanelOpinionsDealSurveyPriorityAPI.as_view(), name="panel_opinionsdeal_priority_survey"),
]