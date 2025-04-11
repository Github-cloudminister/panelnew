from django.db.models import Sum, Count
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework.validators import UniqueTogetherValidator
# *********** in-project imports ************
from SupplierAPI.models import *
from Project.models import *
from Supplier.models import *
from Surveyentry.models import *


class SupplierAPIAdditionalfieldSerializer(ModelSerializer):
    class Meta:
        model = SupplierAPIAdditionalfield
        fields = ['enable_routing', 'enable_hash', 'hash_variable_name', 'hash_security_key']

class APISupplierOrganisationSerailizer(ModelSerializer):
    additional_field = SupplierAPIAdditionalfieldSerializer(source='supplierapiadditionalfield', required=False)

    class Meta:
        model = SupplierOrganisation
        fields = [
            'id', 'supplier_code', 'supplier_name',
            'supplier_payment_details', 'supplier_address1', 'supplier_address2', 'supplier_city', 'supplier_state', 'supplier_country',
            'supplier_zip', 'supplier_status', 'supplier_postbackurl', 'supplier_internal_terminate_redirect_url', 'supplier_terminate_no_project_available', 'supplier_url_code','supplier_type','supplier_routerurl','supplier_rate_type', 'supplier_rate_value', 'additional_field','max_authorized_cpi', 'max_completes_on_diy'
            ]
        read_only_fields = ['supplier_code','supplier_routerurl']
        extra_kwargs = {
            'supplier_payment_details': {
                'source': 'supplier_paymentdetails',
                'required':False,
            },
            'supplier_address1': {
                'required':False,
            },
            'supplier_address2': {
                'required':False,
            },
            'supplier_city': {
                'required':False,
            },
            'max_completes_on_diy': {
                'required':False,
            },
            'supplier_state': {
                'required':False,
            },
            'supplier_country': {
                'required':True,
            },
            'supplier_zip': {
                'required':False,
            },
            'supplier_routerurl': {
                'required':False,
            },
            'supplier_rate_type': {
                'source':'supplier_rate_model',
                'required':False,
            },
            'supplier_rate_value': {
                'source':'supplier_rate',
                'required':False,
            },
        }

    def create(self, validated_data):
        additional_field_data = validated_data.pop('supplierapiadditionalfield', {})
        apisupplier_org_obj = SupplierOrganisation.objects.create(**validated_data)
        SupplierAPIAdditionalfield.objects.create(supplier=apisupplier_org_obj, **additional_field_data)
        return apisupplier_org_obj

class UpdateAPISupplierOrganisationSerailizer(ModelSerializer):
    additional_field = SupplierAPIAdditionalfieldSerializer(source='supplierapiadditionalfield', required=False)
    buyer_api_enable = serializers.StringRelatedField(source='supplier_buyer_apid.buyer_api_enable')

    class Meta:
        model = SupplierOrganisation
        fields = [
            'id', 'supplier_code', 'supplier_name',
            'supplier_payment_details', 'supplier_address1', 'supplier_address2', 'supplier_city', 'supplier_state', 'supplier_country',
            'supplier_zip', 'supplier_status', 'supplier_postbackurl', 'supplier_internal_terminate_redirect_url', 'supplier_terminate_no_project_available', 'supplier_url_code', 'supplier_routerurl', 'supplier_type','supplier_rate_type', 'supplier_rate_value', 'additional_field','max_authorized_cpi','buyer_api_enable', 'max_completes_on_diy'
            ]
        read_only_fields = ['supplier_code', 'supplier_url_code','supplier_routerurl','supplier_type','buyer_api_enable']
        extra_kwargs = {
            'supplier_rate_type': {
                'source':'supplier_rate_model',
                'required':False,
            },
            'supplier_rate_value': {
                'source':'supplier_rate',
                'required':False,
            },
            'supplier_payment_details': {
                'source': 'supplier_paymentdetails',
                'required':False,
            },
            'supplier_address1': {
                'required':False,
            },
            'supplier_address2': {
                'required':False,
            },
            'supplier_city': {
                'required':False,
            },
            'max_completes_on_diy': {
                'required':False,
            },
            'supplier_state': {
                'required':False,
            },
            'supplier_country': {
                'required':True,
            },
            'supplier_zip': {
                'required':False,
            },
        }

    def update(self, instance, validated_data):
        additional_field_data = validated_data.pop('supplierapiadditionalfield', {})

        instance = super().update(instance, validated_data)

        supp_additional_field_obj,supp_additional_field_obj_created = SupplierAPIAdditionalfield.objects.get_or_create(supplier=instance)
        if additional_field_data.get('enable_routing'):
            supp_additional_field_obj.enable_routing = additional_field_data['enable_routing']
        else:
            supp_additional_field_obj.enable_routing = False
        if additional_field_data.get('enable_hash'):
            supp_additional_field_obj.enable_hash = additional_field_data['enable_hash']
        else:
            supp_additional_field_obj.enable_hash = False
        if additional_field_data.get('hash_security_key','') != '':
            supp_additional_field_obj.hash_security_key = additional_field_data['hash_security_key']
        if additional_field_data.get('hash_variable_name','') != '':
            supp_additional_field_obj.hash_variable_name = additional_field_data['hash_variable_name']
        supp_additional_field_obj.save()
        return instance

class ProjectGroupAPISupplierSerializer(ModelSerializer):
    class Meta:
        model = ProjectGroupSupplier
        fields = [
            'id', 'project_group', 'supplier_org', 'completes', 'clicks', 'cpi', 'supplier_status'
        ]
        
        # read_only_fields = ['cpi']
        validators = [
            UniqueTogetherValidator(
                queryset=ProjectGroupSupplier.objects.all(),
                fields=['project_group', 'supplier_org'],
            )
        ]


class ProjectGroupAPISupplierUpdateSerializer(ModelSerializer):
    class Meta:
        model = ProjectGroupSupplier
        fields = [
            'id', 'project_group', 'supplier_org', 'completes', 'clicks', 'cpi', 'supplier_status'
        ]
        read_only_fields = ['id', 'project_group', 'supplier_org']



# Custom function for - median_value
def median_value(queryset, term):
    count = queryset.count()
    if count > 0:
        values = queryset.values_list(term, flat=True).order_by(term)
        if count == 1:
            return values[0]
        elif count % 2 == 1:
            return values[int(round(count/2))]
        else:
            first_value = values[round((count/2)-1)]
            second_value = values[round(count/2)]
            val = float(first_value) + float(second_value)
            return val/float(2.0)
    else:
        return 0

def get_reps_supplier_stats(resp):
    
    total_visits = resp.count()
    incompletes = resp.filter(resp_status=3).count()
    completes = resp.filter(resp_status=4).count()
    terminates = resp.filter(resp_status=5).count()
    quota_full = resp.filter(resp_status=6).count()
    security_terminate = resp.filter(resp_status=7).count()
    starts = incompletes + completes + terminates + quota_full + security_terminate
    try:
        incidence = (completes/(completes + terminates + quota_full))*100
    except ZeroDivisionError:
        incidence = 0

    survey_details = resp.filter(resp_status=4, url_type='Live')
    get_median = float(median_value(survey_details, 'duration'))
    median_LOI = round(get_median, 0)

    revenue = resp.filter(resp_status=4, url_type='Live').aggregate(Sum("project_group_cpi"))
    expense = resp.filter(resp_status=4, url_type='Live').aggregate(Sum("supplier_cpi"))
    revenue = resp.filter(resp_status=4, url_type='Live').aggregate(
            Sum("project_group_cpi"))
    expense = resp.filter(resp_status=4, url_type='Live').aggregate(
            Sum("supplier_cpi"))
    if revenue['project_group_cpi__sum'] == None or expense['supplier_cpi__sum'] == None or revenue['project_group_cpi__sum'] == 0 or expense['supplier_cpi__sum'] == 0:
        margin=0
    else:
        margin = (revenue['project_group_cpi__sum'] - expense['supplier_cpi__sum']) / revenue['project_group_cpi__sum']

    resp_stats = {
        "starts": starts,
        "total_visits": total_visits,
        "incidence": incidence,
        "median_LOI": median_LOI,
        "revenue": revenue['project_group_cpi__sum'],
        "expense": expense['supplier_cpi__sum'],
        "margin": round(margin * 100, 2),
        "completes": completes,
        "incompletes": incompletes,
        "terminates": terminates,
        "security_terminate": security_terminate,
        "quota_full": quota_full
    }

    return resp_stats


class APISupplierWithStatsSerializer(serializers.ModelSerializer):
    
    total_N = serializers.IntegerField(
        source='completes'
    )

    supplier_stats = serializers.SerializerMethodField()

    class Meta:
        model = ProjectGroupSupplier
        fields = ['id', 'project_group', 'supplier_org', 'total_N', 'clicks', 'cpi', 'supplier_complete_url', 'supplier_terminate_url', 'supplier_quotafull_url', 'supplier_securityterminate_url', 'supplier_postback_url', 'supplier_internal_terminate_redirect_url', 'supplier_terminate_no_project_available', 'supplier_status', 'supplier_stats']

        extra_kwargs = {
            'supplier_complete_url': {
                'source': 'supplier_completeurl',
            },
            'supplier_terminate_url': {
                'source': 'supplier_terminateurl',
            },
            'supplier_quotafull_url': {
                'source': 'supplier_quotafullurl',
            },
            'supplier_securityterminate_url': {
                'source': 'supplier_securityterminateurl',
            },
            'supplier_postback_url':{
                'source': 'supplier_postbackurl',
            },
        }

    def get_supplier_stats(self, obj):
        resp_detail_obj = self.context.get('resp_detail_obj').filter(source=obj.supplier_org.id)
        return get_reps_supplier_stats(resp_detail_obj)


class APISupplierWithReportTermSerializer(serializers.ModelSerializer):

    total_N = serializers.IntegerField(
        source='completes'
    )

    supplier_stats = serializers.SerializerMethodField()

    class Meta:
        model = ProjectGroupSupplier
        fields = [
            'id', 'project_group', 'supplier_org', 'total_N', 'clicks', 'cpi', 'supplier_complete_url', 'supplier_terminate_url', 'supplier_quotafull_url', 'supplier_securityterminate_url', 'supplier_postback_url', 'supplier_internal_terminate_redirect_url', 'supplier_terminate_no_project_available', 'supplier_status', 'supplier_stats'
        ]

        extra_kwargs = {
            'supplier_complete_url': {
                'source': 'supplier_completeurl',
            },
            'supplier_terminate_url': {
                'source': 'supplier_terminateurl',
            },
            'supplier_quotafull_url': {
                'source': 'supplier_quotafullurl',
            },
            'supplier_securityterminate_url': {
                'source': 'supplier_securityterminateurl',
            },
            'supplier_postback_url':{
                'source': 'supplier_postbackurl',
            },
        }

    def get_supplier_stats(self, obj):
        resp_detail_obj = self.context.get('resp_detail_obj').filter(source=obj.supplier_org.id)
        return get_reps_supplier_stats(resp_detail_obj)

    def get_reports(self, obj):
        reports = []
        for resp_detail in RespondentDetail.objects.filter(project_group_number=obj.project_group.project_group_number, source=obj.supplier_org.id).values('final_detailed_reason').annotate(Count('final_detailed_reason')).order_by():
            reports.append({resp_detail['final_detailed_reason']:resp_detail['final_detailed_reason__count']})
        return reports

class APISupplierRespondentDetailSerializer(serializers.ModelSerializer):

    project_id = serializers.SerializerMethodField()
    supplier_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = RespondentDetail
        fields = ['project_id', 'supplier_stats']

    def get_project_id(self, obj):
        try:
            pro_id = Project.objects.get(project_number=obj[0].project_number)
            return pro_id.id
        except:
            return 0

    def get_supplier_stats(self, instance):
        total_visits = instance.count()
        incompletes = instance.filter(resp_status=3).count()
        completes = instance.filter(resp_status=4).count()
        terminates = instance.filter(resp_status=5).count()
        quota_full = instance.filter(resp_status=6).count()
        security_terminate = instance.filter(resp_status=7).count()
        starts = incompletes + completes + terminates + quota_full + security_terminate
        try:
            incidence = (completes/(completes + terminates + quota_full))*100
        except ZeroDivisionError:
            incidence = 0

        survey_details = instance.filter(resp_status=4, url_type='Live')
        get_median = float(median_value(survey_details, 'duration'))
        median_LOI = round(get_median, 0)
        revenue = instance.filter(resp_status=4, url_type='Live').aggregate(Sum("project_group_cpi"))
        expense = instance.filter(resp_status=4, url_type='Live').aggregate(Sum("supplier_cpi"))
        if revenue['project_group_cpi__sum'] == None or expense['supplier_cpi__sum'] == None or revenue['project_group_cpi__sum'] == 0 or expense['supplier_cpi__sum'] == 0:
            margin = 0
        else:
            margin = (revenue['project_group_cpi__sum'] - expense['supplier_cpi__sum']) / revenue['project_group_cpi__sum']

        supplier_stats = {
            "total_visits": total_visits,
            "starts": starts,
            "completes": completes,
            "incompletes": incompletes,
            "quota_full": quota_full,
            "terminates": terminates,
            "security_terminate": security_terminate,
            "incidence": incidence,
            "median_LOI": median_LOI,
            "revenue": revenue['project_group_cpi__sum'],
            "expense": expense['supplier_cpi__sum'],
            "margin": round(margin*100, 2)
        }

        return supplier_stats


class PrescreenerQuestionsAnswerLucidListSerializer(serializers.ModelSerializer):

    parent_question_type = serializers.CharField(source='translated_question_id.parent_question_type')
    lucidquestion = serializers.CharField(source='translated_question_id.lucid_question_id')
    AnswerOptions = serializers.SerializerMethodField()

    def get_AnswerOptions(self, obj):
        return obj.allowed_zipcode_list if obj.translated_question_id.lucid_question_id == '45' else obj.allowedoptions.values_list('lucid_answer_id',flat = True)
    class Meta:
        model = ProjectGroupPrescreener
        fields = ['lucidquestion','allowedRangeMin','allowedRangeMax','allowed_zipcode_list','AnswerOptions','parent_question_type']