from django.urls import path
from scrubsupplierids.views import *

app_name = 'scrubsupplierids'

urlpatterns = [

     path('project-list-for-scrub', projectListForScrubView.as_view()), #List of projects which needs to be scrubbed. 

     path('complete-counts-by-supplier', SupplierCompleteCountsView.as_view()), # List of Supplier data based on that scrub operation should be performed. 
     
     path('scrub-supplier-id', SupplierIdRejectedView.as_view()), # Scrub final ids from payload data
     
     path('project-supplier-row-create', ProjectSupplierRowCreateApi.as_view()), # exists data project supplier invoice row create api

     #============= Sub Supplier Scrub =====================#

     path('sub-supplier-project-list-for-scrub', SubSupplierProjectListForScrubView.as_view()), #List of projects which needs to be scrubbed for Sub Supplier. 

     path('complete-counts-by-sub-supplier', SubSupplierCompleteCountsView.as_view()), # List of Sub Supplier data based on that scrub operation should be performed. 

     path('scrub-sub-supplier-id', SubSupplierIdRejectedView.as_view()), # Scrub Sub Supplier final ids from payload data

     # path('revert-scrub', revertScrubIdsView.as_view()),
     
     # path('complete-counts-by-project', projectCompleteCountsView.as_view()),

]