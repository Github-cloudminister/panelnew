from django.urls import path
from AdminDashboard.views import *

app_name = "admindashboard"


urlpatterns = [

    #Project Group list with Completes, Revenue, Conversion, Country and Language (Only Live project groups)
    path('projectgrpwise-stats', LiveProjectGroupWiseStatsAPI.as_view(), name="projectgrpwisestats"),

    #last 7 day counts (Day wise) for Collected complete, New projects created, Revenue, expense
    path('daywisecount-project', Last7DayWiseOnlyStatsAPI.as_view(), name="daywisecountproject"),

    #Project Statistics - Filter on day and month (Will get from frontend) --> Response {Completes, Incompletes, Terminates, OQs} [In case filter is 1D then response should include one day stats, for 3D then response should include 3 days stats day wise. Filter options: 1D, 3D, 7D, 1M, 3M, 6M, 1Y]
    path('daywisecompletecount', DayWiseCompleteCountsAPI.as_view(), name="daywisecompletecount"),

    #Current Project Status - Count of Live projects, Paused projects, Closed projects, reconciled Projects
    path('projectstatuscount', ProjectStatusCountsAPI.as_view(), name="projectstatus-count"),

    #Already Computed OnHold Projects List with Respondent Details in a New Table from Celery, Created this API just for fetching Purposes to optimize Performance
    path('computed-projectgrp-hits-count', ComputedOnHoldProjectsRespStatsAPI.as_view(), name="computedprojectgrphitscount"),

    #Customer wise Stats --> (month filter will get from frontend) ---> Customer Name, Conversion rate (Completes/ starts), rejection rate(resp_status = [8]/resp_status = [4,8,9], project status = [Reconciled, Invoiced]), Revenue, Expense, Margin((Revenue-expense)*100/revenue)
    path('customerwise-stats', MonthWiseCustomerStatsCountAPI.as_view(), name="customerwisestats"),

    #Supplier wise stats --> (month filter will get from frontend) ---> Supplier Name, Conversion rate, rejection rate, Revenue, Expense, Margin
    path('supplierwise-stats', MonthWiseSupplierStatsCountAPI.as_view(), name="supplierwisestats"),

    #PM Performance --> (month filter will get from frontend) ---> PM name, Live projects, Paused projects, Closed, Reconciled, Invoiced, Revenue, expense, margin
    path('projectmanager-stats', ProjectManagerWiseStatsAPI.as_view(), name="projectmanagerstats"),

    # Add Project to Sticky Board View
    path('sticky-board-addproject', AddProjectToStickyBoardView.as_view(), name="stickyboardaddproject"),

    # Remove Project from Sticky Board View
    path('sticky-board-removeproject', RemoveProjectStickyBoardView.as_view(), name="stickyboardremoveproject"),

    # List Project Sticky Board View
    path('sticky-board-listproject', StickyBoardProjectListView.as_view(), name="stickyboardlistproject"),

    path('overall-health', OverallHealthView.as_view({'get': 'list'}), name="overallhealth"),

    path('research-defender-failure-data/<int:survey_no>', ReserachDefenderFailureDataView.as_view(), name="research_defender_failure_data_view"),
  
    path('project-wise-manager-revenue-report', ProjectWiseManagerRevenueReport.as_view(), name="projectwisemanagerrevenuereport"),
    
    path('all-source-wise-router-report', RouterReport.as_view()),

    path('source-wise-router-report/<str:source>', SourceRouterReport.as_view()),

    #List API for Project/Audit Report and get resp Details By passing Project Number
    path('project-revenue-expense', ProjectClientRevenueAndSupplierExpenseApi.as_view()),
    
    #Survey Entry Wise Project Report
    path('project-revenue-expense-survey-entry-wise', ProjectRevenueExpenseSurveyEntryWise.as_view()),

    # By Project Invoice Data
    path('project-invoice-data',ProjectInvoiceReportDataView.as_view()),

    #Supplier invoice Row data in Project/Audit Report
    path('project-supplier-invoice-row-data', ProjectWiseSupplierInvoiceReport.as_view()),

    path('project-invoiced-approved',ProjectReportInvoiceApprovedAPI.as_view()),

    #secondary audit status update only for Narendra sir 
    path('project-secondary-invoiced-approved',ProjectsecondaryInvoiceApprovedAPI.as_view()),

    path('supplier-invoiced-row-update-dashboard/<int:id>',SupplierInvoiceRowUpdateDashboard.as_view()),

    path('send-email-to-projectmanager-cpi-update/<str:project_number>',EmailSendProjectManagerCPIUpdate.as_view()),

    path('client-supplier-pm-wise-report',ClientSupplierPMWiseReport.as_view()),

    path('project-manager-wise-INR-report',ProjectManagerINRReport.as_view()),

    path('project-multiple-invoiced-approved',ProjectReportAuditMultipleInvoicedApprovedAPI.as_view()),


    ################################# API's For New Admin Dashboard #####################################


    path('sales-overview-graph',SalesOverviewGraph.as_view()),

    path('sales-overview-apis',SalesOverviewApis.as_view()),

    path('client-stats',ClientStats.as_view()),

    path('supplier-stats',SupplierStats.as_view()),

    path('project-manager-stats',ProjectManagerStats.as_view()),

    path('user-daily-visits',UserDailyVisits.as_view()), #last 7 days user stats

    path('project-manager-work-load',ProjectManagersWorkLoad.as_view()),

    path('api-client-stats',APIClientStats.as_view()), #this year top 5 revenue projects

    path('country-wise-total-surveys-live',CountryWiseTotalSurveysLive.as_view()), #country wise total number of project live 
]