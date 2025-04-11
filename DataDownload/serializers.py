from rest_framework import serializers

from Surveyentry.models import *
from .models import *


class RespondentDetailSerializer(serializers.ModelSerializer):

    pid = serializers.SerializerMethodField()
    ip_address = serializers.SerializerMethodField()
    RID = serializers.SerializerMethodField()

    def get_pid(self, obj):

        try:
            pid_value = RespondentURLDetail.objects.get(respondent__id=obj.id)
            return pid_value.pid
        except:
            return None

    def get_ip_address(self, obj):

        try:
            ip_add = RespondentURLDetail.objects.get(respondent__id=obj.id)
            return ip_add.ip_address
        except:
            return None

    def get_RID(self, obj):

        try:
            rid_value = RespondentURLDetail.objects.get(respondent__id=obj.id)
            return rid_value.RID
        except:
            return None

    class Meta:
        
        model = RespondentDetail
        fields = [
            'id', 'pid', 'ip_address', 'source', 'resp_status', 'RID', 
            'start_time', 'end_time', 'duration', 'final_detailed_reason', 
        ]



class SuppliersMonthlyDetailListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='respondentdetailsrelationalfield.source.supplier_name')
    survey_number = serializers.CharField(source='project_group_number')
    project_status = serializers.CharField(source='respondentdetailsrelationalfield.project.project_status')
    respondent_pid = serializers.CharField(source='respondenturldetail.pid')
    resp_start_time = serializers.DateTimeField(source='start_time', format="%d-%m-%Y %H:%M:%S")
    resp_end_time = serializers.DateTimeField(source='end_time', format="%d-%m-%Y %H:%M:%S")
    resp_status = serializers.SerializerMethodField()


    def get_resp_status(self, obj):
        return obj.get_resp_status_display()

    class Meta:
        
        model = RespondentDetail
        fields = ('supplier_name','project_number','survey_number','project_status','respondent_pid','resp_start_time','resp_end_time', 'resp_status')



class RespondentDetailNestedSerializer(serializers.ModelSerializer):

    class Meta:
        
        model = RespondentDetail
        fields = '__all__'



class ResearchDefenderResponseNestedSerializer(serializers.ModelSerializer):

    class Meta:
        
        model = ResearchDefenderResponseDetail
        fields = '__all__'


class ResearchDefenderDetailListSerializer(serializers.ModelSerializer):
    respondent_detail = RespondentDetailNestedSerializer(source='respondent')
    research_defender_response = ResearchDefenderResponseNestedSerializer(source='researchdefenderresponsedetail')
    created_at = serializers.DateTimeField(format="%d-%m-%Y")
    updated_at = serializers.DateTimeField(format="%d-%m-%Y")

    class Meta:
        
        model = RespondentResearchDefenderDetail
        fields = '__all__'