from rest_framework import serializers
from Prescreener.models import ProjectGroupPrescreener
from Project.models import ProjectGroupSupplier
from Questions.models import TranslatedAnswer, TranslatedQuestion, ZipCodeMappingTable
from django.db.models import F

class TranslatedAnswersSerializer(serializers.ModelSerializer):
    AnswerID = serializers.CharField(source='internal_answer_id')
    AnswerText = serializers.CharField(source='translated_answer')
    InternalAnswerText = serializers.CharField(source='answer_internal_name')
    class Meta:
        model = TranslatedAnswer
        fields = ['AnswerID', 'AnswerText','InternalAnswerText']

class TranslatedQuestionsSerializer(serializers.ModelSerializer):

    all_responses = TranslatedAnswersSerializer(many=True, source='translatedanswer_set')
    CountryLanguageID = serializers.CharField(source='apidbcountrylangmapping.id')
    QuestionID = serializers.CharField(source='Internal_question_id')
    InternalQuestionText = serializers.CharField(source='internal_question_text')
    QuestionText = serializers.CharField(source='translated_question_text')
    QuestionType = serializers.CharField(source='parent_question_type')
    IsActive = serializers.CharField(source='is_active')
    class Meta:
        model = TranslatedQuestion
        fields = ['QuestionID','QuestionText','InternalQuestionText','QuestionType','IsActive','CountryLanguageID','all_responses']

class PrescreenerQuestionAnswerSerializers(serializers.ModelSerializer):
    AnswerOptions = serializers.SerializerMethodField()
    QuestionID = serializers.SerializerMethodField()

    def get_AnswerOptions(self, obj):
        if obj.translated_question_id.Internal_question_id in ['112521','181411']:
            agerange = []
            allowedRangeMin = obj.allowedRangeMin.split(',')
            allowedRangeMax = obj.allowedRangeMax.split(',')

            for min, max in zip(allowedRangeMin, allowedRangeMax):
                agerange.append(f'{min}-{max}')
            return agerange
        elif obj.translated_question_id.parent_question_type == 'ZIP':
            allowed_zipcode_list = []
            allowed_zipcode_list.extend(obj.allowed_zipcode_list)

            ctzip_obj = list(ProjectGroupPrescreener.objects.filter(translated_question_id__parent_question_type = 'CTZIP',project_group_id__project_group_number = obj.project_group_id.project_group_number).values_list('allowedoptions__internal_answer_id',flat=True))           
            return list(ZipCodeMappingTable.objects.filter(parent_answer_id__internal_answer_id__in = ctzip_obj).values_list('zipcode',flat=True))
        else:
            return list(obj.allowedoptions.values_list(F('internal_answer_id'),flat=True))
    
    def get_QuestionID(self, obj):
        return obj.translated_question_id.Internal_question_id
    
    class Meta:
        model = ProjectGroupPrescreener
        fields = ['QuestionID','AnswerOptions']