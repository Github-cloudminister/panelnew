from django.urls import path
from SupplierRouter.views import *

app_name = "SupplierRouter"

urlpatterns = [
        path('projectgroup-router-supplier/<int:project_group_id>', ProjectGroupRouterSupplierView.as_view({'get':'list', 'post':'create'})),

        path('project-group/router-supplierstatistics/<int:project_group_num>/<int:supplier_id>', RouterSupplierRespondentDetailView.as_view()),

        path('projectgroup-ad-supplier/<int:project_group_id>', ProjectGroupADPanelSupplier.as_view()),

        path('projectgroup-sub-supplier-multiple-add', SubSupplierAddMultipleSurveyAPI.as_view()),
        
]