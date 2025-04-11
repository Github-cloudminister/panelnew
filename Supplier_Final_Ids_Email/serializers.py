from rest_framework import serializers
from Supplier_Final_Ids_Email.models import *


class ReconciliationSerializer(serializers.ModelSerializer):

    class Meta:
        model = SupplierIdsMarks
        fields = ['verified', 'previous_status', 'previous_final_detailed_reason']


class ListReconciledProjectsSerializer(serializers.ModelSerializer):
    project_number = serializers.ReadOnlyField(source='project.project_number')

    class Meta:
        model = SupplierIdsMarks
        fields = ['project_number', 'reconcile_approved']
