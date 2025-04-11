from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns

from Recontact_Section import views

urlpatterns = [

    path('recontact/<str:project_group_number>', views.RecontactFileAPIView.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns)