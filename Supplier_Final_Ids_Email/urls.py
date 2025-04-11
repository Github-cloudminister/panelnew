from django.urls import path
from Supplier_Final_Ids_Email import views

urlpatterns = [

    # Supplier wise Contact urls
    path('pending-suplierfinalids', views.PendingSupplierFinalIdsView.as_view()),

    path('send-supplier-final-ids', views.sendSupplierFinalIdsView.as_view()),

    path('supplierfinalids',views.SupplierFinalIdsView.as_view()),
    
    path('projectsupplierscrabbed',views.ProjectSupplierScrabbedView.as_view()),
]