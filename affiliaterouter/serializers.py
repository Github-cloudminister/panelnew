from rest_framework import serializers
from Project.models import *
from Prescreener.models import *
from affiliaterouter.models import AffiliateRouterQuestions, RountingPriority

class RountingPrioritySerializer(serializers.ModelSerializer):
    project_group_number = serializers.CharField(source='project_group.project_group_number')

    class Meta:
        model = RountingPriority
        fields = ['id', 'project_group_number', 'created_by', 'modified_by']
        extra_kwargs = {
            'project_group_number': {
                'required': True,
            },
            'created_by':{
                'read_only': True,
            },
            'modified_by':{
                'read_only': True,
            },
        }

    def get_modified_by(self, instance):
        return f'{instance.created_by.first_name} {instance.created_by.last_name}' if instance.created_by != None else None

    def get_modified_by(self, instance):
        return f'{instance.modified_by.first_name} {instance.modified_by.last_name}' if instance.modified_by != None else None


class TranslatedAnswersNestedSerializer(serializers.ModelSerializer):
    numeric_min_range = serializers.CharField(source='parent_answer.numeric_min_range')
    numeric_max_range = serializers.CharField(source='parent_answer.numeric_max_range')
    class Meta:
        model = TranslatedAnswer
        fields = ['translated_answer', 'internal_question_id', 'numeric_min_range', 'numeric_max_range','parent_answer_id','internal_answer_id']

        extra_kwargs = {
            'parent_answer_code':{
                'source':'parent_answer_id',
            },
            'parent_answer_id':{
                'source':'id',
            }
        }


class AffiliateRouterQuestionsAnswersSerializer(serializers.ModelSerializer):
    translated_question_text = serializers.CharField(source='translated_question.translated_question_text')
    translated_question_code = serializers.CharField(source='translated_question.Internal_question_id')
    translated_question_type = serializers.CharField(source='translated_question.parent_question_type')
    translated_answers = TranslatedAnswersNestedSerializer(source='translated_question.translatedanswer_set.all', many=True)

    class Meta:
        model = AffiliateRouterQuestions
        fields = ['affiliate_router_id', 'translated_question', 'translated_question_text', 'translated_question_code','translated_question_type', 'translated_answers']

        extra_kwargs = {
            'affiliate_router_id':{
                'source':'id',
            }
        }

