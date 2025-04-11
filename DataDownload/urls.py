from django.urls import path
from . import views


urlpatterns = [

    path('details', views.RespondentProjectGroup.as_view()),

    path('sidebarcount', views.SideBarCountsView.as_view()),

    path('project-data/<int:project_group_num>', views.ProjectGroupDataAPIView.as_view()),
    
    path('project-data/json-data/<int:project_group_num>', views.ProjectGroupJsonDataAPIView.as_view()),

    path('data/<str:project_number>', views.ProjectDataAPIView.as_view()),

    path('data-v2/<str:project_number>', views.ProjectDataApiView_V2.as_view()),

    path('project-group-question-data/<int:project_group_number>', views.ProjectGroupQuestionDataAPIView.as_view()),

    path('research-defender-data/<int:project_group_num>', views.ResearchDefenderDataAPIView.as_view()),

    path('download/cust-supp-question-data', views.CustSuppQuestionDataDownload.as_view()),

    # API FOR LISTING MULTIPLE SUPPLIERS' COMPLETED STATUS DATA MONTH-YEAR WISE
    path('suppliers-monthly-detail-list', views.SuppliersMonthlyDetailListAPI.as_view()),

    # API FOR LISTING ALL RespondentResearchDefenderDetail DATA
    path('research-defender-detail-list', views.ResearchDefenderDetailListAPI.as_view()),

    path('sub-supplier/json-data/<int:project_group_num>', views.ProjectGroupSubJsonDataApiView.as_view()),

]