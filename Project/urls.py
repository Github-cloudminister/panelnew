from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from Project import views

urlpatterns = [

     #Country list GET API
     path('country', views.CountryView.as_view()),

     #Language list GET API
     path('language', views.LanguageView.as_view()),

     #Project LIST/CREATE API
     path('project', views.ProjectView.as_view()),

     #Project GET/UPDATE API
     path('project/<int:project_id>', views.ProjectUpdateView.as_view()),
     
     # Project list with stats API Home page
     path('project-stats-list-2', views.ProjectListStatistics2View.as_view()),

     # Project 24 hr stats API Project List page
     path('project-24-hr-stats-view/<str:project_number>', views.Project24HrStats.as_view()),

     # Project Status Change API
     path('project/<int:project_id>/status',views.ProjectStatusUpdateView.as_view()),

     # ProjectGroup LIST/CREATE API
     path('project-group', views.ProjectGroupView.as_view()),

     # ProjectGroup GET/UPDATE API
     path('project-group/<int:project_group_id>',views.ProjectGroupUpdateView.as_view()),

     # ProjectGroup status change API
     path('project-group/<int:project_group_id>/status',views.ProjectGroupStatusUpdateView.as_view()),

     # project-group-supplier API
     path('projectgroup-supplier', views.ProjectGroupSupplierView.as_view()),
     
     # project-group-supplier API
     path('projectgroup-supplier/<int:proj_grp_supp_id>',views.ProjectGroupSupplierUpdateView.as_view()),
     
     # project-group-supplier status change API
     path('projectgroup-supplier/<int:supplier_id>/status',views.ProjectGroupSupplierStatusUpdateView.as_view()),

     # project-group multiple API
     path('multiple-url/<int:project_group_number>', views.MultipleURLView.as_view()),

     # project wise project-group API
     path('project/group/<int:project_id>', views.ProjectDetailGroup.as_view()),

     # project statistics of respondent API
     path('statistics/project/<str:project_number>',views.ProjectRespondentDetailView.as_view()),

     # project-group statistics of respondent API
     path('statistics/project-group/<int:project_group_num>',views.ProjectGroupRespondentDetailView.as_view()),

     # project-group wise supplier statistics of respondent API
     path('statistics/supplier/<int:supplier_id>/<int:project_group_num>',views.SupplierRespondentDetailView.as_view()),
     
     # project wise detailed API, clicked on project survey
     path('project-detail/<int:project_id>',views.ProjectDetailedView.as_view()),

     # project level supplier add at survey list page
     path('project-group/supplierWiseprojectgroupsupplier/<str:project_no>/<int:supplier_id>', views.SupplierWiseProjectGroupView.as_view()),
     
     # list supplier statistics in survey
     path('project-group/supplierWithstat-2/<int:project_group_num>', views.SupplierWithStatisticsView.as_view()),

     # list sub supplier statistics in survey
     path('project-group/sub-supplierWithstat-2/<int:project_group_num>', views.SubSupplierWithStatisticsView.as_view()),

     # sidebar dashboard header calculation 
     path('dash-board', views.DashboardView.as_view()),

     # Copy individual survey with Prescreener
     path('project-group-copy/<int:project_group_id>', views.ProjectGroupCopyView.as_view()),

     # upload zipcode file for old Prescreener(Now added in "allowed_zipcode_list" JSONField)
     path('zip_code/<int:project_group_number>', views.ZipCodeView.as_view()),

     # Project list statistics download
     path('project-stats-list/xlsx-download', views.ProjectListStatisticsExcelDownloadView.as_view()),

     # Prescreener Zipcode download
     path('zipcode-download/<int:project_group_number>', views.ZipCodeDownloadAPIView.as_view()),

     # Multipleurl download
     path('multipleurl-download/<int:project_group_number>', views.MultipleURLDownloadAPIView.as_view()),

     #Add notes in project
     path('add-project-notes/<str:project_number>', views.projectAddNotes.as_view()),

     # Use in Exclude Project Group
     path('project-group/excluded', views.ExcludedProjectGroupGetApi.as_view()),

     # Lanch survey time call
     path('pre-launching-survey-checklist/<int:project_group_number>', views.PreLanchingSurveyCheckListApi.as_view()),

     # Respondent CPI update for single Supplier in ProjectGroup Supplier Level
     path('respondent-update-cpi/<str:project_group_number>/<int:supplier_id>', views.RespondentDetailCPIUpdateSupplierLevelAPI.as_view()),

     # Respondent CPI update for multi Supplier in Project Level
     path('respondent-update-project-level-cpi/<str:project_number>/<int:supplier_id>', views.RespondentDetailCPIUpdateProjectLevelAPI.as_view()),
     
     # statistics Create in new table
     path('project-group-statistics-create/<str:project_number>', views.ProjectGroupStatisticsCreate.as_view()),
     
     # statistics Update in new table
     path('project-group-statistics-update/<str:project_number>', views.ProjectGroupStatisticsUpdate.as_view()),

     # Live Project Group List for Survey Priority
     path('project-group-survey-priority-list', views.ProjectGroupSurveyPriority.as_view()),

     # Project Level Supplier CPI and System CPI Approved Popup API and redy for invoice
     path('project-level-cpi-confirm-by-manager/<int:project>', views.ProjectCPIApprovedByManager.as_view()),

     # Project Type Dummy and create Dummy Completes
     path('dummy-data-create-in-respondent-for-outer-project/<int:projectgroupsupplier>', views.RespondentDummyDataCreate.as_view()),

     # this API called from Celery for Calculation of internal conversion in Project Group Level
     path('celery-conversion-calculation', views.CeleryConversionCalculation.as_view()),
     
     # this API called from Celery for Calculation of internal conversion in Project Group Level
     path('set-survey-priority-celery', views.SurveyPriorityCelery.as_view()),

     # Project Create from Bid Email Link
     path('project-get-bid-email-link/<int:bidid>', views.ProjectCreateBidEmailLink.as_view()),

     # Add Project backup list API
     path('project-add-for-backup', views.ProjectAddForBackup.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)