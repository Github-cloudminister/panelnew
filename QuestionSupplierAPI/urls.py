from django.urls import path
from QuestionSupplierAPI import views

app_name = "QuestionSupplierAPI"


urlpatterns = [
	path('api_supplier/questionfetch_answers/', views.QuestionsMappingDetailView.as_view(), name='questionfetch_answers'),
	path('api_supplier/supplierorg_quesmapping/', views.SupplierOrgMappedQuestionsView.as_view(), name='supplierorg_quesmapping'),
]