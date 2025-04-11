from rest_framework import serializers
from Questions.models import *


class QuestionCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = QuestionCategory
        fields = ['id', 'category',]


class ParentQuestionSerializer(serializers.ModelSerializer):

    parent_question_number = serializers.CharField(
        read_only=True,
    )

    parent_question_prescreener_type = serializers.CharField(
        read_only=True,
    )

    class Meta:
        model = ParentQuestion
        fields = ['id', 'parent_question_number', 'parent_question_text', 'parent_question_type', 'parent_question_category', 'parent_question_prescreener_type','apidbcountrylangmapping']
        extra_kwargs={
            'parent_question_type':{
                'required':True,
            },
            'parent_question_category':{
                'required':True,
            }
        }


class ParentQuestionUpdateSerializer(serializers.ModelSerializer):

    parent_question_number = serializers.CharField(
        read_only=True,
    )
    parent_question_type = serializers.CharField(
        read_only=True,
    )
    parent_question_prescreener_type = serializers.CharField(
        read_only=True,
    )

    class Meta:
        model = ParentQuestion
        fields = ['id', 'parent_question_number', 'parent_question_text', 'parent_question_type', 'parent_question_category', 'parent_question_prescreener_type']


class ParentAnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = ParentAnswer
        fields = ['id', 'parent_question', 'parent_answer_text', 'sequence', 
                'numeric_min_range', 'numeric_max_range', 'isExclusive', 'parent_answer_status',
            ]
        extra_kwargs={
          'isExclusive':{
                'source':"exclusive",
            },
            'parent_question':{
                'required':True,
            },
            'sequence':{
                'required':True,
            },
        }

class StandardParentAnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = ParentAnswer
        fields = ['id', 'parent_answer_id', 'parent_question', 'parent_answer_text', 'sequence', 
                'numeric_min_range', 'numeric_max_range', 'isExclusive', 'parent_answer_status',
            ]
        extra_kwargs={
          'isExclusive':{
                'source':"exclusive",
            },
            'parent_question':{
                'required':True,
            },
            'sequence':{
                'required':True,
            },
        }


class ParentAnswerUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ParentAnswer
        fields = ['id', 'parent_question', 'parent_answer_text', 'sequence', 
                'numeric_min_range', 'numeric_max_range', 'isExclusive', 'parent_answer_status',
            ]
        extra_kwargs={
            'isExclusive':{
                'source':"exclusive",
            },
            'parent_question':{
                'read_only':True,
            },
            'numeric_min_range':{
                'read_only':True,
            },
            'numeric_max_range':{
                'read_only':True,
            }
        }


class TranslatedQuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = TranslatedQuestion
        fields = ['id', 'parent_question', 'lang_code', 'translated_question_text','apidbcountrylangmapping']


class TranslatedQuestionNameSerializer(serializers.ModelSerializer):

    language = serializers.SerializerMethodField()
    parent_question = serializers.SerializerMethodField()
    parent_question_prescreener_type = serializers.SerializerMethodField()

    def get_parent_question(self, obj):
        return obj.parent_question.parent_question_text.capitalize()

    def get_language(self, obj):
        return obj.lang_code.language_name.capitalize()

    def get_parent_question_prescreener_type(self, obj):
        return obj.parent_question.parent_question_prescreener_type

    class Meta:
        model = TranslatedQuestion
        fields = ['id', 'parent_question', 'parent_question_prescreener_type', 'language', 'translated_question_text',]


class TranslatedQuestionUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TranslatedQuestion
        fields = ['id', 
                'parent_question', 'lang_code', 
                'translated_question_text',
            ]
        extra_kwargs={
            'lang_code':{
                'read_only':True,
            },
            'parent_question':{
                'read_only':True,
            }
        }


class TranslatedAnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = TranslatedAnswer
        fields = ['id', 'translated_parent_question', 'parent_answer', 'translated_answer', 'translated_answer_status',]


class TranslatedAnswerNameSerializer(serializers.ModelSerializer):

    translated_question = serializers.SerializerMethodField()
    parent_answer = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()


    def get_parent_answer(self, obj):
        return obj.parent_answer.parent_answer_text.capitalize()
        
    def get_translated_question(self, obj):
        return obj.translated_parent_question.translated_question_text.capitalize()

    def get_language(self, obj):
        return obj.translated_parent_question.lang_code.language_name.capitalize()

    class Meta:
        model = TranslatedAnswer
        fields = [
            'id', 'parent_answer', 'language',
            'translated_question', 'translated_answer', 'translated_answer_status',
        ]


class TranslatedAnswerUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TranslatedAnswer
        fields = ['id', 'translated_parent_question', 
                'parent_answer', 'translated_answer', 'translated_answer_status',
            ]
        extra_kwargs={
            'translated_parent_question':{
                'read_only':True,
            },
            'parent_answer':{
                'read_only':True,
            }
        }
            

class QuestionAnswerSerializer(serializers.ModelSerializer):

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
            answers = ParentAnswer.objects.filter(parent_question__id=obj.id, parent_answer_status=True).order_by('id')
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

class QuestionAnswerListSerializer(serializers.ModelSerializer):

    parent_question_id = serializers.SerializerMethodField()
    parent_question_prescreener_type = serializers.SerializerMethodField()
    
    def get_parent_question_id(self, obj):
        return obj.parent_question.id

    def get_parent_question_prescreener_type(self, obj):
        return obj.parent_question.parent_question_prescreener_type

    class Meta:
        model = ParentAnswer
        fields = [
            'id', 'parent_question_id', 'parent_question_prescreener_type', 'parent_answer_text', 'sequence', 'numeric_min_range', 'numeric_max_range',
        ]


class TranslatedQuestionAnswerListSerializer(serializers.ModelSerializer):

    parent_answer_id = serializers.SerializerMethodField()
    translated_question_id = serializers.SerializerMethodField()
    parent_question_prescreener_type = serializers.SerializerMethodField()

    def get_translated_question_id(self, obj):
        return obj.translated_parent_question.id

    def get_parent_answer_id(self, obj):
        return obj.parent_answer.id
    
    def get_parent_question_prescreener_type(self, obj):
        return obj.translated_parent_question.parent_question.parent_question_prescreener_type

    class Meta:
        model = TranslatedAnswer
        fields = ['id', 'translated_question_id', 'parent_answer_id', 'parent_question_prescreener_type', 'translated_answer',]


class TranslatedQuestionAnswerSerializer(serializers.ModelSerializer):

    parent_question_id = serializers.SerializerMethodField()
    translated_question = serializers.SerializerMethodField()
    traslated_language = serializers.SerializerMethodField()
    traslated_answer_options = serializers.SerializerMethodField()
    translated_answer_count = serializers.SerializerMethodField()
    parent_question_prescreener_type = serializers.SerializerMethodField()

    def get_parent_question_id(self, obj):
        num_obj = obj.parent_question.id
        return num_obj

    def get_translated_question(self, obj):
        # return obj.translated_question_text
        return [{"id":obj.id,
                "question_text":obj.translated_question_text.capitalize()}]

    def get_traslated_language(self, obj):
        return [{"id":obj.lang_code.id,
                "language_name":obj.lang_code.language_name.capitalize()}]

    def get_traslated_answer_options(self, obj):
        try:
            answers = TranslatedAnswer.objects.filter(translated_parent_question__id=obj.id, translated_answer_status=True).order_by('id')
            return [{"id":answer.id, "parent_answer_id":answer.parent_answer.id, "translated_answer_text": answer.translated_answer}\
                            for answer in answers]
        except:
            return None

    def get_translated_answer_count(self, obj):
        try:
            answer_count = TranslatedAnswer.objects.filter(translated_parent_question__id=obj.id, translated_answer_status=True)
            return answer_count.count()
        except:
            return 0

    def get_parent_question_prescreener_type(self, obj):
        return obj.parent_question.parent_question_prescreener_type

    class Meta:
        model = TranslatedQuestion
        fields = ['id', 'parent_question_id', 'parent_question_prescreener_type', 'translated_question', 
                'traslated_language', 'translated_answer_count', 'traslated_answer_options',
        ]


class TranslatedListByParentQuestionSerializer(serializers.ModelSerializer):

    language = serializers.SerializerMethodField()
    translated_question = serializers.SerializerMethodField()
    translated_answer_count = serializers.SerializerMethodField()
    translated_answer_options = serializers.SerializerMethodField()
    parent_question_id = serializers.SerializerMethodField()
    parent_question_prescreener_type = serializers.SerializerMethodField()

    def get_parent_question_id(self, obj):
        return obj.parent_question.id

    def get_language(self, obj):
        return [{"id":obj.lang_code.id,
                "language_name":obj.lang_code.language_name.capitalize()}]

    def get_translated_question(self, obj):
        return [{"id":obj.id,
                "question_text":obj.translated_question_text.capitalize()}]

    def get_translated_answer_count(self, obj):
        try:
            answer_count = TranslatedAnswer.objects.filter(translated_parent_question__id=obj.id, translated_answer_status=True)
            return answer_count.count()
        except:
            return 0
    
    def get_translated_answer_options(self, obj):
        try:
            answers = TranslatedAnswer.objects.filter(translated_parent_question__id=obj.id, translated_answer_status=True).order_by('id')
            return [{"id":answer.id, "parent_answer_id":answer.parent_answer.id, "translated_answer_text": answer.translated_answer}\
                            for answer in answers]
        except:
            return None

    def get_parent_question_prescreener_type(self, obj):
        return obj.parent_question.parent_question_prescreener_type

    class Meta:
        model = TranslatedQuestion
        fields = ['parent_question_id', 'parent_question_prescreener_type', 'language', 'translated_question', 'translated_answer_count','translated_answer_options',]

class StandardParentAnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = ParentAnswer
        fields = ['id', 'parent_answer_id', 'parent_question', 'parent_answer_text', 'sequence', 
                'numeric_min_range', 'numeric_max_range', 'isExclusive', 'parent_answer_status',
            ]
        extra_kwargs={
          'isExclusive':{
                'source':"exclusive",
            },
            'parent_question':{
                'required':True,
            },
            'sequence':{
                'required':True,
            },
        }