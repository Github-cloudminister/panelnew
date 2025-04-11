from django.db.models import fields, Sum, Count, Q
from rest_framework import serializers
from rest_framework.fields import ReadOnlyField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework.views import set_rollback
from rest_framework.viewsets import ModelViewSet

# *********** in-project imports ************
from SupplierAPI.models import *
from Project.models import *
from Supplier.models import *
from Surveyentry.models import *
from SupplierAPI.serializers import *



class ProjectGroupRouterSupplierSerializer(ModelSerializer):
    # completes = serializers
    total_N = serializers.CharField(source='completes')
    class Meta:
        model = ProjectGroupSupplier
        fields = [
            'id', 'project_group', 'supplier_org', 'total_N', 'clicks', 'cpi'
        ]
        
        # read_only_fields = ['cpi']
        validators = [
            UniqueTogetherValidator(
                queryset=ProjectGroupSupplier.objects.all(),
                fields=['project_group', 'supplier_org'],
            )
        ]



class SupplierAPIAdditionalfieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierAPIAdditionalfield
        fields = ['enable_routing', 'enable_hash', 'hash_variable_name', 'hash_security_key']

class RouterSupplierOrganisationSerailizer(ModelSerializer):
    additional_field = SupplierAPIAdditionalfieldSerializer(source='supplierapiadditionalfield', required=False)

    class Meta:
        model = SupplierOrganisation
        fields = [
            'id', 'supplier_code', 'supplier_name',
            'supplier_payment_details', 'supplier_address1', 'supplier_address2', 'supplier_city', 'supplier_state', 'supplier_country',
            'supplier_zip', 'supplier_status', 'supplier_postbackurl', 'supplier_internal_terminate_redirect_url', 'supplier_terminate_no_project_available', 'supplier_type','supplier_routerurl', 'supplier_rate_model', 'supplier_rate', 'additional_field','max_authorized_cpi'
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
            'supplier_rate_model':{
                'required':True,
            },
            'supplier_rate':{
                'required':True,
            },
        }

    def create(self, validated_data):
        additional_field_data = validated_data.pop('supplierapiadditionalfield', {})
        apisupplier_org_obj = SupplierOrganisation.objects.create(**validated_data)
        SupplierAPIAdditionalfield.objects.create(supplier=apisupplier_org_obj, **additional_field_data)
        return apisupplier_org_obj


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


class RouterSupplierRespondentDetailSerializer(serializers.ModelSerializer):

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

class RouterSupplierOrganisationwithCPISerailizer(serializers.ModelSerializer):
    additional_field = SupplierAPIAdditionalfieldSerializer(source='supplierapiadditionalfield', required=False)
    supplier_rate = serializers.SerializerMethodField()

    class Meta:
        model = SupplierOrganisation
        fields = [
            'id', 'supplier_code', 'supplier_name',
            'supplier_payment_details', 'supplier_address1', 'supplier_address2', 'supplier_city', 'supplier_state', 'supplier_country',
            'supplier_zip', 'supplier_status', 'supplier_complete_url', 'supplier_terminate_url', 'supplier_quotafull_url', 'supplier_securityterminate_url', 'supplier_postback_url', 'supplier_internal_terminate_redirect_url', 'supplier_terminate_no_project_available', 'supplier_type','supplier_routerurl', 'supplier_rate_model', 'supplier_rate', 'additional_field','max_authorized_cpi'
            ]
        read_only_fields = ['supplier_code','supplier_routerurl']
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
            'supplier_payment_details': {
                'source': 'supplier_paymentdetails',
                'required':False,
            }
        }

    def get_supplier_rate(self, instance):
        project_group_id = self.context.get('project_group_id', '')
        country_code_list = ProjectGroupSupplier.objects.filter(project_group__id=project_group_id,supplier_org=instance, supplier_org__supplier_type = '3').values_list('project_group__project_group_country__country_code', flat=True)
        try:
            supplier_rate = SupplierCPIMapping.objects.get(supplier_org = instance, country__country_code__in = country_code_list).cpi
        except:
            supplier_rate = "0"
        return supplier_rate
