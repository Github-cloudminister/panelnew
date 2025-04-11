from django.urls import path
from InitialSetup.views import InitialSetupView, SupplierOrgAuthKeyDetailsSetupAPI, StandardQuestionView

urlpatterns = [

    path('initial-setup', InitialSetupView.as_view(), name="initial_setup"),

    path('standard-question', StandardQuestionView.as_view()),
    
    path('api-customer-supplier-authkeys-setup', SupplierOrgAuthKeyDetailsSetupAPI.as_view()),
    
]