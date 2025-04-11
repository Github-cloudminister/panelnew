from django.urls import path
from SupplierAPI.views import *

app_name = "apisupplier"

urlpatterns = [

    # APISupplier Organization urls
    path('api-supplier', APISupplierOrganisationView.as_view({'get':'list'}), name="api_supplier_create"),

    path('api-supplier/<int:id>/', APISupplierOrganisationUpdateView.as_view({'get':'retrieve', 'put':'update'}), name="api_supplier_update"),
    
    # project-group-api-supplier urls
    path('projectgroup-api-supplier', ProjectGroupAPISupplierView.as_view({'get':'list','post':'create'}), name="projectgroup_api_supplier"),
    
    path('projectgroup-api-supplier/<int:id>', ProjectGroupAPISupplierUpdateView.as_view({'get':'retrieve', 'put':'update'}), name="projectgroup_api_supplier_update"),

    # project-group-api-supplier update stats urls
    path('projectgroup-api-supplier/<int:id>/status', ProjectGroupAPISupplierStatusUpdateView.as_view({'get':'retrieve', 'put':'update'}), name="projectgroup_api_supplier_update"),

    # project-group wise supplier statistics of respondent urls
    path('statistics/api-supplier/<int:supplier_id>/<int:project_group_num>', APISupplierRespondentDetailView.as_view(), name="statisics_supplier"),

    path('project-group/api-supplierWithstat/<int:project_group_num>', APISupplierWithStatView.as_view(), name="project_group_apisupplierwithstat"),
    
    path('project-group/api-supplierTermReport/<int:project_group_num>', APISupplierWithTermReportView.as_view(), name="project_group_apisuppliertermreport"),
     
]