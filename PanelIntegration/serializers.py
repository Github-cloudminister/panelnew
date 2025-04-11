from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from .models import *
from Project.models import *
from Customer.models import *
from Surveyentry.models import RespondentDetail, RespondentReconcilation
from Prescreener.models import ProjectGroupPrescreener
from Project.models import ZipCode
from datetime import datetime

class ProjectGroupAddPanelSerializer(serializers.ModelSerializer):

    project_category = serializers.SerializerMethodField()

    def get_project_category(self, obj):
        return obj.project.project_category
    
    class Meta:
        model = ProjectGroup
        fields = [
            'id', 'project_group_number', 'project_group_name', 'project_group_survey_url', 'project_group_encodedS_value', 
            'project_group_encodedR_value', 'project_group_redirectID', 'project_group_revenue', 'project_group_cpi', 'project_group_country', 
            'project_group_language', 'project_category', 'project_group_status', 'enable_panel', 'panel_reward_points',
        ]
        read_only_fields = ['project_group_number', 'project_group_name', 'project_group_survey_url', 'project_group_encodedS_value', 
            'project_group_encodedR_value', 'project_group_redirectID', 'project_group_revenue', 'project_group_cpi', 'project_group_country', 
            'project_group_language', 'project_category', 'project_group_status', ]
        extra_kwargs = {
            'project_group_survey_url': {
                'source': 'project_group_surveyurl',
            },
            'enable_panel': {
                'required': True,
            },
            'panel_reward_points':{
                'required': True,
            },
        }

class EmailSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailSubject
        fields = ['id', 'email_subject_line']

class EmailInviteSerializer(serializers.ModelSerializer):
    survey_number = serializers.IntegerField(source='survey_number.project_group_number')
    class Meta:
        model = EmailInvite
        fields = ['id', 'survey_number', 'no_of_invites', 'schedule', 'email_subjectline']

class StoreEmailInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailInvite
        fields = ['id', 'survey_number', 'no_of_invites', 'schedule', 'email_subjectline']


class SelectedQuestionAnswerListSerializer(serializers.ModelSerializer):

    parent_question_number = serializers.SerializerMethodField()
    question_category = serializers.SerializerMethodField()
    parent_question_prescreener_type = serializers.SerializerMethodField()
    answer_options = serializers.SerializerMethodField()
    zipcode_counts = serializers.SerializerMethodField()

    def get_parent_question_number(self, obj):
        return obj.translated_question_id.parent_question.parent_question_number
    
    def get_question_category(self, obj):
        return obj.translated_question_id.parent_question.parent_question_category.category
    
    def get_parent_question_prescreener_type(self, obj):
        return obj.translated_question_id.parent_question.parent_question_prescreener_type
    
    def get_answer_options(self, obj):
        return obj.allowedoptions.values_list('parent_answer__parent_answer_id', flat=True)

    
    def get_zipcode_counts(self,obj):
        return ZipCode.objects.filter(project_group_id = obj.project_group_id).count() + len(obj.allowed_zipcode_list) if obj.allowed_zipcode_list != [] else 0

    class Meta:
        model = ProjectGroupPrescreener
        fields = ['parent_question_number', 'question_category', 'parent_question_prescreener_type',
                 'answer_options', 'allowedRangeMin','allowedRangeMax',  'zipcode_counts'
            ]

class PanelistSurveyHistorySerializer(serializers.ModelSerializer):
    resp_status = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    verified = serializers.SerializerMethodField()
    previous_status = serializers.SerializerMethodField()

    class Meta:
        model = RespondentDetail
        fields = ['resp_status', 'rewards', 'date', 'project_number', 'survey_number', 'final_detailed_reason' ,'verified', 'previous_status']
        extra_kwargs = {
            'rewards':{
                'source':'supplier_cpi'
            },
            'survey_number':{
                'source': 'project_group_number',
            },
        }

    def get_resp_status(self, instance):
        return instance.get_resp_status_display()

    def get_date(self, instance):
        return datetime.strftime(instance.start_time, '%d-%m-%Y')
    
    def get_respondent_reconcilation_object(self, instance):
        try:
            resp_reconcilation = RespondentReconcilation.objects.get(respondent=instance)
        except ObjectDoesNotExist:
            resp_reconcilation = None
        return resp_reconcilation

    def get_verified(self, instance):
        resp_reconcilation_obj = self.get_respondent_reconcilation_object(instance)
        if resp_reconcilation_obj != None:
            resp_reconcilation_obj = resp_reconcilation_obj.get_verified_display()
        return resp_reconcilation_obj

    def get_previous_status(self, instance):
        resp_reconcilation_obj = self.get_respondent_reconcilation_object(instance)
        if resp_reconcilation_obj != None:
            resp_reconcilation_obj = resp_reconcilation_obj.get_previous_status_display()
        return resp_reconcilation_obj



class ProjectGroupAddSlickRouterSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProjectGroup
        fields = [
            'id', 'project_group_number', 'project_group_name', 'project_group_survey_url', 'project_group_encodedS_value', 
            'project_group_encodedR_value', 'project_group_redirectID', 'project_group_revenue', 'project_group_cpi', 'project_group_country', 
            'project_group_language', 'project_group_status', 'enable_panel', 'panel_reward_points',
        ]
        read_only_fields = ['project_group_number', 'project_group_name', 'project_group_survey_url', 'project_group_encodedS_value', 
            'project_group_encodedR_value', 'project_group_redirectID', 'project_group_revenue', 'project_group_cpi', 'project_group_country', 
            'project_group_language', 'project_category', 'project_group_status', ]
        extra_kwargs = {
            'project_group_survey_url': {
                'source': 'project_group_surveyurl',
            },
            'enable_panel': {
                'required': True,
            },
            'panel_reward_points':{
                'required': True,
            },
        }