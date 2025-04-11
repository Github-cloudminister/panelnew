# rest_framework imports
from rest_framework.validators import UniqueTogetherValidator
from rest_framework import serializers
from feasibility.models import *
from Questions.models import *

class FeasibilityQuestionAnswerMappingSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = FeasibilityQuestionAnswerMapping
        fields = '__all__'
        extra_kwargs = {
            'feasibilitycpiweightage':{
                'required':False,
            },
            'feasibilityweightage':{
                'required':False,
            },

        }
        validators = [
            UniqueTogetherValidator(
                queryset=FeasibilityQuestionAnswerMapping.objects.all(),
                fields=['question', 'answer']
            )
        ]


class feasibilityCPIRateSerializer(serializers.ModelSerializer):

    class Meta:
        model = BaseCPI
        fields = ['id','study_type', 'min_loi', 'max_loi', 'min_incidence', 'max_incidence', 'cpi']
        validators = [
            UniqueTogetherValidator(
                queryset = BaseCPI.objects.all(),
                fields = ['study_type', 'min_loi', 'max_loi', 'min_incidence', 'max_incidence', 'cpi']
            )
        ]

class feasibilityWeightageSerializer(serializers.ModelSerializer):

    class Meta:
        model = BaseFeasibilityWeightage
        fields = ['id','min_loi', 'max_loi', 'min_incidence', 'max_incidence', 'feasibilityWeightage']
        validators = [
            UniqueTogetherValidator(
                queryset = BaseFeasibilityWeightage.objects.all(),
                fields = ['min_loi', 'max_loi', 'min_incidence', 'max_incidence', 'feasibilityWeightage']
            )
        ]


class feasibilityQuestionAnswerSerializer(serializers.ModelSerializer):

    parent_question_category = serializers.SerializerMethodField()
    answer_options = serializers.SerializerMethodField()
    parent_question_text = serializers.SerializerMethodField()

    def get_parent_question_text(self, obj):
        return obj.parent_question_text

    def get_parent_question_category(self, obj):
        quest_cat = obj.parent_question_category
        return quest_cat.category

    def get_answer_options(self, obj):
        try:
            answers = ParentAnswer.objects.filter(parent_question__id=obj.id, parent_answer_status=True).order_by('sequence')
            return [{"id":answer.id, "sequence":answer.sequence, "answer_text":answer.parent_answer_text, "exclusive":answer.exclusive} for answer in answers]
        except:
            return None

    parent_question_prescreener_type = serializers.CharField(
        read_only=True,
    )

    class Meta:
        model = ParentQuestion
        fields = ['id', 'parent_question_number', 'parent_question_category', 
                'parent_question_type', 'parent_question_text', 'parent_question_prescreener_type', 'answer_options',
            ]