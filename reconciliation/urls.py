from django.urls import path
from reconciliation.views import *


urlpatterns = [

    path("project-reconcile/<str:project_number>", ReconciliationView.as_view()),

    path("verify-reconcile-rids/<str:project_number>", VerifyReconciliationRIDDataView.as_view()),
    
    path('revert-reconciliation/', RevertReconciliationView.as_view()),

]