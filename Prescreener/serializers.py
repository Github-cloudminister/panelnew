from rest_framework import serializers
from Prescreener.models import *
from Questions.models import *
from django.db.models import F,ExpressionWrapper, Q
from Project.models import ZipCode


class PreScreenerQuestionSerializer(serializers.ModelSerializer):

    class Meta:

        model = ProjectGroupPrescreener
        fields = ['id', 'project_group_id', 'translated_question_id', 'allowed_options', 'allowed_min_range', 'allowed_max_range', 'sequence','is_enable']
        extra_kwargs = {
            'project_group_id':{
                'read_only':True,
            },
            'translated_question_id': {
                'allow_null': False, 
                'required': True,
            },
            'allowed_options': {
                # 'allow_null': False, 
                'required': True,
                'source': 'allowedoptions',
            },
            'allowed_min_range': {
                'source': 'allowedRangeMin',
                'label': 'Allowed Min Range'
            },
            'allowed_max_range': {
                'source': 'allowedRangeMax',
                'label': 'Allowed Max Range',
            },
        }


class PreScreenerQuestionUpdateSerializer(serializers.ModelSerializer):
    
    project_group_id = serializers.SerializerMethodField()
    translated_question_id = serializers.SerializerMethodField()
    parent_question_prescreener_type = serializers.SerializerMethodField()

    def get_project_group_id(self, obj):
        return obj.project_group_id.project_group_name

    def get_translated_question_id(self, obj):
        return obj.translated_question_id.translated_question_text

    def get_parent_question_prescreener_type(self, obj):
        return obj.translated_question_id.parent_question.parent_question_prescreener_type

    class Meta:

        model = ProjectGroupPrescreener
        fields = ['id', 'project_group_id', 'translated_question_id', 'parent_question_prescreener_type', 'allowed_options', 'allowed_min_range', 'allowed_max_range', 'sequence']
        extra_kwargs = {

            'allowed_options': {
                # 'allow_null': False, 
                'required': True,
                'source': 'allowedoptions',
            },
            'allowed_min_range': {
                'source': 'allowedRangeMin',
                'label': 'Allowed Min Range'
            },
            'allowed_max_range': {
                'source': 'allowedRangeMax',
                'label': 'Allowed Max Range',
            }
        }    


class PreScreenerQuestionListSerializer(serializers.ModelSerializer):

    question_type = serializers.SerializerMethodField()
    lucid = serializers.SerializerMethodField()
    disq = serializers.SerializerMethodField()
    internal_question_text = serializers.SerializerMethodField()
    
    def get_lucid(self, obj):
        return True if obj.lucid_question_id else False
    
    def get_disq(self, obj):
        return True if obj.disqo_question_id else False

    def get_question_type(self, obj):
        return obj.parent_question.parent_question_type
    
    def get_internal_question_text(self, obj):
        return obj.translated_question_text if obj.internal_question_text == '' else obj.internal_question_text

    class Meta:
        model = TranslatedQuestion
        fields = ['question_type','internal_question_text','id','lucid','disq']


class PreScreenerAnswerListSerializer(serializers.ModelSerializer):

    answer_internal_name = serializers.SerializerMethodField()

    def get_answer_internal_name(self, obj):
        return obj.translated_answer if obj.answer_internal_name == '' else obj.answer_internal_name

    class Meta:
        model = TranslatedAnswer
        fields = ['answer_internal_name','id']


class SurveyPrescreenerViewSerializer(serializers.ModelSerializer):

    prescreener_id = serializers.SerializerMethodField()
    parent_question_id = serializers.SerializerMethodField()
    parent_question_text = serializers.SerializerMethodField()
    parent_question_prescreener_type = serializers.SerializerMethodField()
    translated_question_id = serializers.SerializerMethodField()
    translated_question_text = serializers.SerializerMethodField()
    question_type = serializers.SerializerMethodField()
    question_category = serializers.SerializerMethodField()
    answer_options = serializers.SerializerMethodField()
    sequence = serializers.SerializerMethodField()
    parent_question_number = serializers.SerializerMethodField()
    zipcode_counts = serializers.SerializerMethodField()

    def get_zipcode_counts(self,obj):
        return ZipCode.objects.filter(project_group_id = obj.project_group_id).count() + len(obj.allowed_zipcode_list) if obj.allowed_zipcode_list != [] else 0

    def get_prescreener_id(self, obj):
        return obj.id

    def get_parent_question_id(self, obj):
        return obj.translated_question_id.parent_question.id

    def get_parent_question_text(self, obj):
        return obj.translated_question_id.parent_question.parent_question_text

    def get_translated_question_id(self, obj):
        return obj.translated_question_id.id

    def get_translated_question_text(self, obj):
        return obj.translated_question_id.translated_question_text

    def get_question_type(self, obj):
        return obj.translated_question_id.parent_question.parent_question_type

    def get_question_category(self, obj):
        return obj.translated_question_id.parent_question.parent_question_category.category

    def get_answer_options(self, obj):
        return obj.allowedoptions.values('parent_answer_id', 'parent_answer__parent_answer_text', 'id', 'translated_answer')

    def get_sequence(self, obj):
        return obj.sequence

    def get_parent_question_prescreener_type(self, obj):
        return obj.translated_question_id.parent_question.parent_question_prescreener_type

    def get_parent_question_number(self, obj):
        return obj.translated_question_id.parent_question.parent_question_number

    class Meta:
        model = ProjectGroupPrescreener
        fields = ['prescreener_id', 'parent_question_id', 'parent_question_text', 'question_type','question_category', 'parent_question_prescreener_type',
                'translated_question_id', 'translated_question_text',
                 'answer_options', 'sequence','allowedRangeMin','allowedRangeMax', 'parent_question_number', 'zipcode_counts'
            ]


class SurveyPrescreenerV2Serializer(serializers.ModelSerializer):

    prescreener_id = serializers.SerializerMethodField()
    parent_question_id = serializers.SerializerMethodField()
    parent_question_text = serializers.SerializerMethodField()
    parent_question_prescreener_type = serializers.SerializerMethodField()
    translated_question_id = serializers.SerializerMethodField()
    translated_question_text = serializers.SerializerMethodField()
    question_type = serializers.SerializerMethodField()
    question_type_name = serializers.ReadOnlyField(source = 'translated_question_id.parent_question.get_parent_question_type_display')
    question_category = serializers.SerializerMethodField()
    answer_options = serializers.SerializerMethodField()
    sequence = serializers.SerializerMethodField()
    parent_question_number = serializers.SerializerMethodField()
    zipcode_counts = serializers.SerializerMethodField()
    status = serializers.ReadOnlyField(source = 'translated_question_id.parent_question.is_active')

    def get_zipcode_counts(self,obj):
        return len(obj.allowed_zipcode_list) if obj.allowed_zipcode_list != [] else 0

    def get_prescreener_id(self, obj):
        return obj.id

    def get_parent_question_id(self, obj):
        return obj.translated_question_id.parent_question.id

    def get_parent_question_text(self, obj):
        return obj.translated_question_id.parent_question.parent_question_text

    def get_translated_question_id(self, obj):
        return obj.translated_question_id.id

    def get_translated_question_text(self, obj):
        return obj.translated_question_id.translated_question_text

    def get_question_type(self, obj):
        return obj.translated_question_id.parent_question.parent_question_type

    def get_question_category(self, obj):
        return obj.translated_question_id.parent_question.parent_question_category.category

    def get_answer_options(self, obj):
        allowed_answers_list = obj.allowedoptions.values_list('parent_answer_id', flat=True)
        trans_ans_list = TranslatedAnswer.objects.filter(translated_parent_question__parent_question=obj.translated_question_id.parent_question,translated_parent_question__lang_code__language_code="en").values('parent_answer_id', parent_answer_text=F('parent_answer__parent_answer_text'), translated_answer_text=F('translated_answer'), translated_answer_id=F('id')).annotate(is_allowed_option = ExpressionWrapper(Q(parent_answer_id__in = allowed_answers_list), output_field=models.BooleanField()))
        return trans_ans_list
        

    def get_sequence(self, obj):
        return obj.sequence

    def get_parent_question_prescreener_type(self, obj):
        return obj.translated_question_id.parent_question.parent_question_prescreener_type

    def get_parent_question_number(self, obj):
        return obj.translated_question_id.parent_question.parent_question_number

    class Meta:
        model = ProjectGroupPrescreener
        fields = ['prescreener_id', 'parent_question_id', 'parent_question_text', 'question_type','question_type_name','question_category', 'parent_question_prescreener_type',
                'translated_question_id', 'translated_question_text',
                'answer_options', 'sequence','allowedRangeMin','allowedRangeMax', 'parent_question_number', 'zipcode_counts','status'
            ]


class SurveyPrescreenerApiViewSerializer(serializers.ModelSerializer):

    prescreener_id = serializers.SerializerMethodField()
    parent_question_text = serializers.SerializerMethodField()
    parent_question_prescreener_type = serializers.SerializerMethodField() 
    question_type = serializers.SerializerMethodField()
    question_category = serializers.SerializerMethodField()
    answer_options = serializers.SerializerMethodField()
    sequence = serializers.SerializerMethodField()
    parent_question_number = serializers.SerializerMethodField()
    zipcode_counts = serializers.SerializerMethodField()

    def get_zipcode_counts(self,obj):
        return ZipCode.objects.filter(project_group_id = obj.project_group_id).count() + len(obj.allowed_zipcode_list) if obj.allowed_zipcode_list != [] else 0

    def get_prescreener_id(self, obj):
        return obj.id

    def get_parent_question_text(self, obj):
        return obj.translated_question_id.parent_question.parent_question_text

    def get_question_type(self, obj):
        return obj.translated_question_id.parent_question.parent_question_type

    def get_question_category(self, obj):
        return obj.translated_question_id.parent_question.parent_question_category.category

    def get_answer_options(self, obj):
        return obj.allowedoptions.values('parent_answer_id', 'parent_answer__parent_answer_id', 'parent_answer__parent_answer_text',)

    def get_sequence(self, obj):
        return obj.sequence

    def get_parent_question_prescreener_type(self, obj):
        return obj.translated_question_id.parent_question.parent_question_prescreener_type

    def get_parent_question_number(self, obj):
        return obj.translated_question_id.parent_question.parent_question_number

    class Meta:
        model = ProjectGroupPrescreener
        fields = ['prescreener_id', 'parent_question_number', 'parent_question_text', 'question_type','question_category', 'parent_question_prescreener_type',
                 'answer_options', 'sequence','allowedRangeMin','allowedRangeMax', 'zipcode_counts'
            ]
