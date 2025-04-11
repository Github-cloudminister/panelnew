from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.db.models import Sum
from Recontact_Section.models import Recontact
from .models import *
from Customer.models import *
from employee.models import Country
from Surveyentry.models import RespondentDetail
import math


class CountrySerializer(serializers.ModelSerializer):

    country_code = serializers.CharField(
        validators=[UniqueValidator(queryset=Country.objects.all())])
    country_name = serializers.CharField(
        validators=[UniqueValidator(queryset=Country.objects.all())])

    class Meta:
        model = Country
        fields = ['id', 'country_code', 'country_name']


class LanguageSerializer(serializers.ModelSerializer):

    language_code = serializers.CharField(
        validators=[UniqueValidator(queryset=Language.objects.all())])
    language_name = serializers.CharField(
        validators=[UniqueValidator(queryset=Language.objects.all())])

    class Meta:
        model = Language
        fields = ['id', 'language_code', 'language_name']


class ProjectSerializer(serializers.ModelSerializer):
    bid_currency = serializers.ReadOnlyField(source='project_customer.currency.id')
    project_customer_name = serializers.ReadOnlyField(source='project_customer.cust_org_name')
    project_sales_person_name = serializers.SerializerMethodField()
    project_pm_name = serializers.SerializerMethodField()

    def get_project_sales_person_name(self,obj):
        return f'{obj.project_sales_person.first_name} {obj.project_sales_person.last_name}'
    
    def get_project_pm_name(self,obj):
        return f'{obj.project_manager.first_name} {obj.project_manager.last_name}'

    class Meta:
        model = Project
        fields = ['id','project_name','project_number','project_po_number','project_category','project_device_type','project_type','project_status','project_redirectID','project_revenue_month','project_revenue_year','project_total_revenue','project_notes','project_client_invoicing_contact_person','project_client_contact_person','project_manager','secondary_project_manager','project_customer','project_currency','bid_currency','project_country','project_language','project_sales_person','project_redirect_type','project_criticality_level','project_list_notes','created_by','modified_by','scrubproject','prj_sticky_board','ad_scrubproject','bid','project_sales_person_name','project_pm_name','project_customer_name']


class ProjectGroupStatusUpdateSerializer(serializers.ModelSerializer):

    project_group_name = serializers.CharField(
        read_only=True
    )
    project_group_number = serializers.CharField(
        read_only=True
    )
    project_name = serializers.SerializerMethodField(
        source='project'
    )

    def get_project_name(self, grp_obj):
        return grp_obj.project.project_name.capitalize()

    class Meta:
        model = ProjectGroup
        fields = [
            'id', 'project_name', 'project_group_number', 'project_group_name', 'project_group_status',
        ]


class ProjectGroupSupplierStatusUpdateSerializer(serializers.ModelSerializer):

    project_group_name = serializers.SerializerMethodField(
        source='project_group'
    )
    supplier_name = serializers.SerializerMethodField(
        source='supplier_org'
    )

    def get_project_group_name(self, supp_obj):
        return supp_obj.project_group.project_group_name.capitalize()

    def get_supplier_name(self, supp_obj):
        return supp_obj.supplier_org.supplier_name.capitalize()

    class Meta:
        model = ProjectGroupSupplier
        fields = [
            'id', 'supplier_name', 'project_group_name', 'supplier_status',
        ]


class ProjectGroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectGroup
        fields = '__all__'


class ProjectGroupGetSerializer(serializers.ModelSerializer):

    total_client_multipleURL_counts = serializers.SerializerMethodField()
    total_client_multipleURL_used_counts = serializers.SerializerMethodField()
    total_client_multipleURL_un_used_counts = serializers.SerializerMethodField()
    total_client_recontactURL_used_counts = serializers.SerializerMethodField()
    total_client_recontactURL_counts = serializers.SerializerMethodField()
    total_client_recontactURL_un_used_counts = serializers.SerializerMethodField()

    def get_total_client_multipleURL_counts(self, obj):
        client_url_counts = MultipleURL.objects.filter(project_group__id=obj.id)
        return client_url_counts.count()

    def get_total_client_multipleURL_used_counts(self, obj):
        client_url_counts = MultipleURL.objects.filter(project_group__id=obj.id, is_used=True)
        return client_url_counts.count()

    def get_total_client_multipleURL_un_used_counts(self, obj):
        client_url_counts = MultipleURL.objects.filter(project_group__id=obj.id, is_used=False)
        return client_url_counts.count()
    
    def get_total_client_recontactURL_counts(self, obj):
        client_url_counts = Recontact.objects.filter(project_group__id=obj.id)
        return client_url_counts.count()
    
    def get_total_client_recontactURL_used_counts(self, obj):
        client_url_counts = Recontact.objects.filter(project_group__id=obj.id, is_used=True)
        return client_url_counts.count()
    
    def get_total_client_recontactURL_un_used_counts(self, obj):
        client_url_counts = Recontact.objects.filter(project_group__id=obj.id, is_used=False)
        return client_url_counts.count()

    project_group_encodedS_value = serializers.CharField(
        read_only=True
    )
    project_group_encodedR_value = serializers.CharField(
        read_only=True
    )
    project_group_redirectID = serializers.CharField(
        read_only=True
    )
    project_group_revenue = serializers.IntegerField(
        read_only=True
    )
    project_group_live_url = serializers.URLField(
        source='project_group_liveurl',
        required=False
    )
    project_group_test_url = serializers.URLField(
        source='project_group_testurl',
        required=False
    )
    project_group_survey_url = serializers.URLField(
        source='project_group_surveyurl',
        read_only=True
    )
    project_group_status = serializers.CharField(
        read_only=True,
    )
    project_group_number = serializers.CharField(
        read_only=True,
    )

    class Meta:
        model = ProjectGroup
        fields = [
            'id', 'project_group_number', 'project_group_name', 'project_group_live_url', 'project_group_test_url', 'project_group_survey_url',
            'project_group_encodedS_value', 'project_group_encodedR_value', 'project_group_redirectID', 'project_audience_type',
            'project_group_incidence', 'project_group_loi', 'project_group_clicks', 'project_group_completes', 'project_group_cpi', 
            'project_group_revenue',  'project_group_startdate', 'project_group_enddate', 'project_group_country', 
            'project_group_language', 'project', 'project_group_status', 'project_group_security_check', 
            'project_group_ip_check', 'project_group_pid_check', 'project_group_allowed_svscore', 
            'project_group_allowed_dupescore', 'project_group_allowed_fraudscore', 'project_group_client_url_type',
            'total_client_multipleURL_counts', 'total_client_multipleURL_used_counts', 'total_client_multipleURL_un_used_counts',
            'show_on_DIY','research_defender_oe_check','threat_potential_score','total_client_recontactURL_used_counts','total_client_recontactURL_counts','total_client_recontactURL_un_used_counts','excluded_project_group','ad_enable_panel', 'project_device_type','respondent_risk_check','failure_check','duplicate_check','duplicate_score','failure_reason','threat_potential_check','enable_panel'
        ]


class ProjectGroupSupplierSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectGroupSupplier
        fields = [
            'id', 'project_group', 'supplier_org', 'completes', 'clicks', 'cpi', 'supplier_complete_url', 'supplier_terminate_url',
            'supplier_quotafull_url', 'supplier_securityterminate_url', 'supplier_postback_url', 'supplier_internal_terminate_redirect_url', 'supplier_terminate_no_project_available', 'supplier_survey_url', 
            'supplier_status',
        ]
        extra_kwargs = {
            'completes':{
                'required': True,
            },
            'cpi':{
                'required': True,
            },
            'supplier_complete_url':{
                'source': 'supplier_completeurl'
            },
            'supplier_terminate_url':{
                'source': 'supplier_terminateurl'
            },
            'supplier_quotafull_url':{
                'source': 'supplier_quotafullurl'
            },
            'supplier_securityterminate_url':{
                'source': 'supplier_securityterminateurl'
            },
            'supplier_postback_url':{
                'source': 'supplier_postbackurl'
            },
            'supplier_survey_url':{
                'read_only': True,
            },
            'supplier_status':{
                'read_only': True,
            },

        }


def median_value(queryset, term):
    count = queryset.count()
    if count > 0:
        values = queryset.values_list(term, flat=True).order_by(term)
        if count == 1:
            return values[0]
        elif count % 2 == 1:
            return values[math.floor(count/2)]
        else:
            first_value = values[round((count/2)-1)]
            second_value = values[round(count/2)]
            val = float(first_value) + float(second_value)
            return val/float(2.0)
    else:
        return 0


class ProjectGroupResponseSerializer(serializers.ModelSerializer):

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
    project_group_completes = serializers.SerializerMethodField()

    class Meta:
        model = RespondentDetail
        fields = ['total_visits', 'starts', 'completes', 'incompletes', 'quota_full',  'terminates', 
                'security_terminate','incidence', 'median_LOI', 'revenue', 'expense', 'margin', 
                'project_group_completes',
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
        starts = request.filter(resp_status__in=[3,4,5,6,7,8,9]).count()
        return starts
        
    def get_incidence(self, request):
        numerator = request.filter(resp_status__in=[4]).count()
        denomerator = request.filter(resp_status__in=[4,5]).count()
        try:
            incidence = (numerator/denomerator)*100
        except ZeroDivisionError:
            incidence = 0
        return incidence

    def get_median_LOI(self, request):
        survey_details = request.filter(resp_status__in=[4,9], url_type='Live')
        get_median = float(median_value(survey_details, 'duration'))
        median_LOI = round(get_median, 0)
        return median_LOI

    def get_revenue(self, request):
        revenue = request.filter(resp_status__in=[4,9], url_type='Live').aggregate(Sum("project_group_cpi"))
        return revenue['project_group_cpi__sum']

    def get_expense(self, request):
        expense = request.filter(resp_status=4, url_type='Live').aggregate(Sum("supplier_cpi"))
        return expense['supplier_cpi__sum']
        
    def get_margin(self, request):
        revenue = request.filter(resp_status__in=[4,9], url_type='Live').aggregate(Sum("project_group_cpi"))
        expense = request.filter(resp_status=4, url_type='Live').aggregate(Sum("supplier_cpi"))
        if revenue['project_group_cpi__sum'] == None or expense['supplier_cpi__sum'] == None:
            margin = 0
        else:
            margin = (revenue['project_group_cpi__sum'] - expense['supplier_cpi__sum']) / revenue['project_group_cpi__sum']
        return margin*100

    def get_completes(self, request):
        return request.filter(resp_status__in=[4,9]).count()

    def get_incompletes(self, request):
        return request.filter(resp_status=3).count()

    def get_terminates(self, request):
        return request.filter(resp_status=5).count()

    def get_security_terminate(self, request):
        return request.filter(resp_status=7).count()

    def get_quota_full(self, request):
        return request.filter(resp_status=6).count()

class ProjectGroupSupplierResponseSerializer(serializers.ModelSerializer):

    project_id = serializers.SerializerMethodField()
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
        fields = ['project_id', 'total_visits', 'starts', 'completes', 'incompletes', 'quota_full', 'terminates', 'security_terminate',
                  'incidence', 'median_LOI', 'revenue', 'expense', 'margin',
                  ]

    def get_project_id(self, obj):
        try:
            pro_id = Project.objects.get(project_number=obj[0].project_number)
            return pro_id.id
        except:
            return 0

    def get_total_visits(self, request, *args, **kwargs):
        total_visits = request.count()
        return total_visits

    def get_starts(self, request):        
        starts = request.filter(resp_status__in=[3,4,5,6,7,8,9]).count()
        return starts

    def get_incidence(self, request):
        numerator = request.filter(resp_status__in=[4]).count()
        denomerator = request.filter(resp_status__in=[4,5]).count()
        try:
            incidence = (numerator/denomerator)*100
        except ZeroDivisionError:
            incidence = 0
        return incidence

    def get_median_LOI(self, request):
        survey_details = request.filter(resp_status__in=[4], url_type='Live')
        get_median = float(median_value(survey_details, 'duration'))
        median_LOI = round(get_median, 0)
        return median_LOI

    def get_revenue(self, request):
        revenue = request.filter(resp_status__in=[4], url_type='Live').aggregate(Sum("project_group_cpi"))
        return revenue['project_group_cpi__sum']

    def get_expense(self, request):
        expense = request.filter(resp_status=4, url_type='Live').aggregate(Sum("supplier_cpi"))
        return expense['supplier_cpi__sum']

    def get_margin(self, request):
        revenue = request.filter(resp_status__in=[4], url_type='Live').aggregate(Sum("project_group_cpi"))
        expense = request.filter(resp_status=4, url_type='Live').aggregate(Sum("supplier_cpi"))
        if revenue['project_group_cpi__sum'] == None or expense['supplier_cpi__sum'] == None:
            margin = 0
        else:
            margin = (revenue['project_group_cpi__sum'] - expense['supplier_cpi__sum']) / revenue['project_group_cpi__sum']
        return margin*100

    def get_completes(self, request):
        return request.filter(resp_status__in=[4]).count()

    def get_incompletes(self, request):
        return request.filter(resp_status__in=[3,9]).count()

    def get_terminates(self, request):
        return request.filter(resp_status=5).count()

    def get_security_terminate(self, request):
        return request.filter(resp_status=7).count()

    def get_quota_full(self, request):
        return request.filter(resp_status=6).count()


class ProjectDetailSerializer(serializers.ModelSerializer):

    project_sales_person = serializers.SerializerMethodField()
    project_customer = serializers.SerializerMethodField()
    project_client_invoicing_contact_person = serializers.SerializerMethodField()
    project_client_contact_person = serializers.SerializerMethodField()
    project_manager = serializers.SerializerMethodField()

    def get_project_sales_person(self, pro_obj):
        return pro_obj.project_sales_person.first_name.capitalize() + ' ' + pro_obj.project_sales_person.last_name

    def get_project_customer(self, pro_obj):
        return pro_obj.project_customer.cust_org_name.capitalize()

    def get_project_client_invoicing_contact_person(self, pro_obj):
        return pro_obj.project_client_invoicing_contact_person.client_firstname.capitalize() + ' ' + pro_obj.project_client_invoicing_contact_person.client_lastname

    def get_project_client_contact_person(self, pro_obj):
        return pro_obj.project_client_contact_person.client_firstname.capitalize() + ' ' + pro_obj.project_client_contact_person.client_lastname

    def get_project_manager(self, pro_obj):
        return pro_obj.project_manager.first_name.capitalize() + ' ' + pro_obj.project_manager.last_name

    class Meta:
        model = Project
        fields = [
            'id', 'project_name', 'project_customer', 'project_manager', 'project_sales_person',
            'project_client_contact_person', 'project_client_invoicing_contact_person',
        ]


class ZipCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ZipCode
        fields = '__all__'
