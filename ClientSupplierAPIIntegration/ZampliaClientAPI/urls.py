from django.urls import path
from ClientSupplierAPIIntegration.views import *
from .views import *



app_name = "ZampliaClientAPI"


urlpatterns = [
    
    path('survey-supplier/client-db-zamplia-quota-update', ClientDBZampliaQuotaUpdate.as_view()),

]