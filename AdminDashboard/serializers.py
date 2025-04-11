from django.db import models
from django.db.models import *
from rest_framework import serializers

from Project.models import *
from Customer.models import *
from Supplier.models import *
from Surveyentry.models import *

def stats(project_obj):
    stats_dict = {}
    resp_detail_obj = RespondentDetail.objects.filter(resp_status__in=[4,9], url_type='Live', project_number=project_obj.project_number)
    revenue = resp_detail_obj.aggregate(revenue = Sum("project_group_cpi"))
    expense = resp_detail_obj.aggregate(expense=Sum("supplier_cpi"))
    stats_dict.update(revenue)
    return stats_dict

class OverallHealthSerializer(serializers.ModelSerializer):
    stats = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['project_number', 'stats']

    def get_stats(self, obj):
        return stats(obj)



class ComputedOnHoldProjectsRespStatSerializer(serializers.ModelSerializer):

    class Meta:
        model = ComputedOnHoldProjectsRespStats
        fields = ('__all__')