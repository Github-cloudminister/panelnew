from django.urls import path
from feasibility.views import *

app_name = "feasibility"

urlpatterns = [
    path('feasibility/listquestionanswer', feasibilityWeightageView.as_view({'get':'list', 'post':'create'})),

    path('feasibility/listquestionanswer/<int:id>', feasibilityWeightageView.as_view({'get':'retrieve','put':'update'})),

    path('feasibility/cpi/rate', feasibilityCPIRateView.as_view({'get':'list', 'post':'create'}), name="crate_or_update_feasibility_cpi_rate"),

    path('feasibility/baseWeightage', feasibilityBaseWeightageView.as_view({'get':'list', 'post':'create'}), name="crate_or_update_feasibility_weightage"),
    
    path('feasibility/questionanswer/value', feasibilityQustionAnswerValueView.as_view({ 'post':'create'})),

    path('feasibility/feasibilequestionanswer', feasibilityQuestionAnswerView.as_view({'get':'list'})),
]