from Project.models import ProjectGroup
from rest_framework import serializers
from django.db.models import F
from django.contrib.postgres.aggregates import ArrayAgg

class ProjectGroupSerializer(serializers.ModelSerializer):
    survey_category = serializers.ReadOnlyField(source='project.project_category')
    country = serializers.ReadOnlyField(source='project_group_country.country_code')
    language = serializers.ReadOnlyField(source='project_group_language.language_code')
    survey_question_answer_list = serializers.SerializerMethodField()

    def get_survey_question_answer_list(self, obj):
        survey_question_answer_list = list(
            obj.projectgroupprescreener_set.filter(is_enable = True).annotate(
                    allowedanswersoptions=ArrayAgg('allowedoptions__internal_answer_id')).values(
                        'allowedRangeMin',
                        'allowedRangeMax',
                        'sequence',
                        'allowed_zipcode_list',
                        'allowedanswersoptions',
                        'is_enable',
                        'translated_question_id__parent_question_type',
                        internal_question_id=F('translated_question_id__Internal_question_id')))
        
        return survey_question_answer_list
     

    class Meta:
        model = ProjectGroup
        fields = ['project_group_number','project_group_name','project_group_surveyurl','survey_category','project_group_loi','project_group_incidence','panel_reward_points','project_group_cpi','project_group_status','country','language','project_device_type','survey_question_answer_list']