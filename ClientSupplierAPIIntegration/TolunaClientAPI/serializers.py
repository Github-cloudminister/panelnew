from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.db.models import Sum

from Prescreener.models import ProjectGroupPrescreener
from Project.serializers import median_value
from Questions.models import TranslatedAnswer
from Surveyentry.models import RespondentDetail

from .models import *



class SurveyPrescreenerAnswersNestedSerializer(serializers.ModelSerializer):
    answer_id = serializers.IntegerField(source='id')

    class Meta:
        model = TranslatedAnswer
        fields = [
            'translated_answer','answer_id'
            ]


class CustomerDefaultSupplySourcesSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplierOrg.supplier_name', read_only=True)
    supplier_status = serializers.CharField(source='supplierOrg.supplier_status', read_only=True)

    class Meta:
        model = CustomerDefaultSupplySources
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                queryset=CustomerDefaultSupplySources.objects.all(),
                fields=['customerOrg', 'supplierOrg']
            )
        ]


class CustomerDefaultSubSupplySourcesSerializer(serializers.ModelSerializer):
    sub_supplier_name = serializers.CharField(source='sub_supplierOrg.sub_supplier_name', read_only=True)
    sub_supplier_status = serializers.CharField(source='sub_supplierOrg.sub_supplier_status', read_only=True)

    class Meta:
        model = CustomerDefaultSubSupplierSources
        fields = '__all__'

        validators = [
            UniqueTogetherValidator(
                queryset=CustomerDefaultSubSupplierSources.objects.all(),
                fields=['customerOrg', 'sub_supplierOrg']
            )
        ]


class ProjectGroupResponseSerializerNew(serializers.ModelSerializer):

    total_visits = serializers.SerializerMethodField()
    starts = serializers.SerializerMethodField()
    incidence = serializers.SerializerMethodField()
    median_LOI = serializers.SerializerMethodField()
    revenue = serializers.SerializerMethodField()
    expense = serializers.SerializerMethodField()
    margin = serializers.SerializerMethodField()
    completes = serializers.SerializerMethodField()
    incompletes = serializers.SerializerMethodField()
    terminates = serializers.SerializerMethodField()
    security_terminate = serializers.SerializerMethodField()
    quota_full = serializers.SerializerMethodField()

    class Meta:
        model = RespondentDetail
        fields = ['total_visits', 'starts', 'completes', 'incompletes', 'quota_full',  'terminates', 
                'security_terminate','incidence', 'median_LOI', 'revenue', 'expense', 'margin'
            ]

    def get_project_group_completes(self, obj):

        try:
            compel = ProjectGroup.objects.get(project_group_number=obj[0].project_group_number)
            return compel.project_group_completes
        except:
            return 0

    def get_total_visits(self, request, *args, **kwargs):
        total_visits = request.count()
        return total_visits

    def get_starts(self, request):
        starts = request.filter(respondent__resp_status__in=[3,4,5,6,7,8,9]).count()
        return starts
        
    def get_incidence(self, request):
        numerator = request.filter(respondent__resp_status__in=[4]).count()
        denomerator = request.filter(respondent__resp_status__in=[4,5]).count()
        try:
            incidence = (numerator/denomerator)*100
        except ZeroDivisionError:
            incidence = 0
        return incidence

    def get_median_LOI(self, request):
        survey_details = request.filter(respondent__resp_status__in=[4,9], respondent__url_type='Live')
        get_median = float(median_value(survey_details, 'respondent__duration'))
        median_LOI = round(get_median, 0)
        return median_LOI

    def get_revenue(self, request):
        revenue = request.filter(respondent__resp_status__in=[4,9], respondent__url_type='Live').aggregate(Sum("respondent__project_group_cpi"))
        return revenue['respondent__project_group_cpi__sum']

    def get_expense(self, request):
        expense = request.filter(respondent__resp_status=4, respondent__url_type='Live').aggregate(Sum("respondent__supplier_cpi"))
        return expense['respondent__supplier_cpi__sum']
        
    def get_margin(self, request):
        revenue = request.filter(respondent__resp_status__in=[4,9], respondent__url_type='Live').aggregate(Sum("respondent__project_group_cpi"))
        expense = request.filter(respondent__resp_status=4, respondent__url_type='Live').aggregate(Sum("respondent__supplier_cpi"))
        if revenue['respondent__project_group_cpi__sum'] == None or expense['respondent__supplier_cpi__sum'] == None:
            margin = 0
        else:
            margin = (revenue['respondent__project_group_cpi__sum'] - expense['respondent__supplier_cpi__sum']) / revenue['respondent__project_group_cpi__sum']
        return margin*100

    def get_completes(self, request):
        return request.filter(respondent__resp_status__in=[4,9]).count()

    def get_incompletes(self, request):
        return request.filter(respondent__resp_status=3).count()

    def get_terminates(self, request):
        return request.filter(respondent__resp_status=5).count()

    def get_security_terminate(self, request):
        return request.filter(respondent__resp_status=7).count()

    def get_quota_full(self, request):
        return request.filter(respondent__resp_status=6).count()


class ClientSurveysListSerializer(serializers.ModelSerializer):
    respondent_data = ProjectGroupResponseSerializerNew(source='respondentdetailsrelationalfield_set')
    project_group_country = serializers.CharField(source='project_group_country.country_code')
    project_group_language = serializers.CharField(source='project_group_language.language_code')
    client_name = serializers.CharField(source='project.project_customer.customer_url_code')
    project_id = serializers.ReadOnlyField(source='project.id')

    class Meta:
        model = ProjectGroup
        fields = ['id','project_id','project_group_number','project_group_name','project_group_status','project_group_country','project_group_language','project_group_incidence','project_group_loi','project_group_completes', 'project_group_revenue','project_group_cpi','respondent_data','client_name']


class ListClientDBCountryLanguageSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClientDBCountryLanguageMapping
        fields = '__all__'


class ClientPrescreenerQuestionDataSerializer(serializers.ModelSerializer):
    client_answer_mappings = SurveyPrescreenerAnswersNestedSerializer(many=True)
    client_question_mapping = serializers.ReadOnlyField(source="client_question_mapping.parent_question.parent_question_text")
    class Meta:
        model = ClientSurveyPrescreenerQuestions
        fields = ['id','client_name','client_question_mapping','client_answer_mappings','open_end_ans_options','allowedRangeMin','allowedRangeMax','date_answer_option','is_routable']


class ClientSubQuotaDataSerializer(serializers.ModelSerializer):
    clientsurveyprescreenerquestions_set = ClientPrescreenerQuestionDataSerializer(many=True)

    class Meta:
        model = ClientSubQuota
        fields = '__all__'


class ClientLayerDataSerializer(serializers.ModelSerializer):
    clientsubquota_set = ClientSubQuotaDataSerializer(many=True)
    class Meta:
        model = ClientLayer
        fields = "__all__"


class ClientQuotaDataSerializer(serializers.ModelSerializer):
    clientlayer_set = ClientLayerDataSerializer(many=True)
    class Meta:
        model = ClientQuota
        fields = "__all__"


class SurveyQualifyParametersSetupSerializer(serializers.ModelSerializer):

    class Meta:
        model = SurveyQualifyParametersCheck
        fields = '__all__'


class PrescreenerSerializerForClientSupply(serializers.ModelSerializer):

    question_text = serializers.ReadOnlyField(source="translated_question_id.internal_question_text")
    question_type = serializers.ReadOnlyField(source="translated_question_id.parent_question_type")
    allowed_answer_options = serializers.SerializerMethodField()

    def get_allowed_answer_options(self, obj):
        if obj.translated_question_id.parent_question_type in 'NU':
            agerange = []
            allowedRangeMin = obj.allowedRangeMin.split(',')
            allowedRangeMax = obj.allowedRangeMax.split(',')

            for min, max in zip(allowedRangeMin, allowedRangeMax):
                agerange.append(f'{min}-{max}')
            return agerange
        elif obj.translated_question_id.parent_question_type == 'ZIP':
            return obj.allowed_zipcode_list
        else:
            return list(obj.allowedoptions.values_list('answer_internal_name', flat=True))

    class Meta:
        model = ProjectGroupPrescreener
        fields = ['question_text','question_type','allowed_answer_options']