from rest_framework import serializers
from Prescreener.models import ProjectGroupPrescreener
from Supplier.models import SupplierOrganisation
from Project.models import  ProjectGroup, ProjectGroupSupplier, ZipCode
from SupplierInvoice.models import SupplierInvoice
from Surveyentry.models import RespondentDetail
from django.db.models import Sum
from Surveyentry.models import *


class supplierDashboardSupplierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierOrganisation
        fields = ['id','supplier_name']

class supplierAddSerializer(serializers.ModelSerializer):
    project_number = serializers.SerializerMethodField()
    survey_name = serializers.SerializerMethodField()
    incidence = serializers.SerializerMethodField()
    loi = serializers.SerializerMethodField()
    targeting_description = serializers.SerializerMethodField()

    def get_project_number(self, instance):
        return instance.project_group.project.project_number

    def get_survey_name(self, instance):
        return instance.project_group.project_group_name

    def get_incidence(self, instance):
        return instance.project_group.project_group_incidence

    def get_loi(self, instance):
        return instance.project_group.project_group_loi
    
    def get_targeting_description(self, instance):
        return instance.project_group.project.project_notes    

    class Meta:
        model = ProjectGroupSupplier
        fields = ['project_number','survey_name','cpi','completes', 'supplier_status','loi','incidence', 'targeting_description', 'supplier_survey_url','supplier_completeurl', 'supplier_terminateurl', 'supplier_quotafullurl', 'supplier_securityterminateurl', 'supplier_internal_terminate_redirect_url', 'supplier_terminate_no_project_available','supplier_postbackurl']
        extra_kwargs = {
            'project_number':{
                'read_only': True,
            },
            'survey_name':{
                'read_only': True,
            },
            'cpi':{
                'read_only': True,
            },
            'completes':{
                'read_only': True,
            },
            'loi':{
                'read_only': True,
            },
            'incidence':{
                'read_only': True,
            },
            'targeting_description':{
                'read_only': True,
            },
            'supplier_survey_url':{
                'read_only': True,
            },
            'supplier_completeurl':{
                'required': True,
            },
            'supplier_terminateurl':{
                'required': True,
            },
            'supplier_quotafullurl':{
                'required': True,
            },
            'supplier_securityterminateurl':{
                'required': True,
            },
        }
        
    
class LiveProjectListSerializer(serializers.ModelSerializer):
    project_number = serializers.SerializerMethodField()
    survey_number = serializers.SerializerMethodField()
    survey_name = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()

    def get_project_number(self, instance):
        return instance.project_group.project.project_number

    def get_survey_number(self, instance):
        return instance.project_group.project_group_number

    def get_survey_name(self, instance):
        return instance.project_group.project_group_name

    def get_statistics(self, instance):
        stats = RespondentDetail.objects.filter(project_group_number = instance.project_group.project_group_number, source = self.context['source'], url_type = 'Live')
        visits=stats.count()
        completes = stats.filter(resp_status = '4')
        all_status = stats.filter(resp_status__in = ['4','5','6','7']).count()
        incidence = 0
        if all_status>0:
            incidence = round(completes.count()/all_status,2)*100
        earning = completes.aggregate(Sum('supplier_cpi'))
        
        return [{'visits':visits, 'completes':completes.count(),'incidence':incidence,'earning':earning['supplier_cpi__sum']}]
    
    class Meta:
        model = ProjectGroupSupplier
        fields = ['project_number', 'survey_number', 'survey_name', 'cpi', 'statistics']


class AwardedProjectGroupSerializer(serializers.ModelSerializer):
    
    project_number = serializers.SerializerMethodField()
    cpi = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    targeting_description = serializers.SerializerMethodField()
    prjgrp_status_setLive_time = serializers.SerializerMethodField()

    def get_prjgrp_status_setLive_time(self, instance):
        timestamp = str(instance.prjgrp_status_setLive_timestamp.date()) + ' ' + str(instance.prjgrp_status_setLive_timestamp.time().hour) + ':' + str(instance.prjgrp_status_setLive_timestamp.time().minute)
        return timestamp

    def get_project_number(self, instance):
        return instance.project.project_number

    def get_cpi(self, instance):
        cpi = round(instance.project_group_cpi * 0.60, 2)
        try:
            max_cpi = SupplierOrganisation.objects.get(id=self.context['source']).max_authorized_cpi
        except:
            max_cpi = 0.0
        return cpi if float(cpi) < max_cpi else max_cpi

    def get_country(self, instance):
        return instance.project_group_country.country_name

    def get_language(self, instance):
        return instance.project_group_language.language_name

    def get_targeting_description(self, instance):
        return instance.project.project_notes
    
    class Meta:
        model = ProjectGroup
        fields = ['project_number', 'survey_number', 'survey_name', 'cpi', 'incidence', 'loi', 'completes', 'country', 'language', 'targeting_description', 'prjgrp_status_setLive_time']
        extra_kwargs = {
            'survey_number':{
                'source': 'project_group_number',
            },
            'survey_name':{
                'source': 'project_group_name'
            },
            'incidence':{
                'source': 'project_group_incidence',
            },
            'loi':{
                'source': 'project_group_loi'
            },
            'completes':{
                'source': 'project_group_completes',
            },
            'prjgrp_status_setLive_time':{
                'source': 'prjgrp_status_setLive_timestamp',
            },
            
        }

class ClosedProjectGroupSerializer(serializers.ModelSerializer):
    project_number = serializers.SerializerMethodField()
    survey_number = serializers.SerializerMethodField()
    survey_name = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()

    def get_project_number(self, instance):
        return instance.project_group.project.project_number

    def get_survey_number(self, instance):
        return instance.project_group.project_group_number

    def get_survey_name(self, instance):
        return instance.project_group.project_group_name

    def get_statistics(self, instance):
        stats = RespondentDetail.objects.filter(project_group_number = instance.project_group.project_group_number, source = self.context['source'], url_type = 'Live')
        completes = stats.filter(resp_status__in = ['4','8','9'])
        total_amount = completes.aggregate(Sum('supplier_cpi'))
        
        return [{'total_amount':total_amount['supplier_cpi__sum'], 'total_completes':completes.count(),}]
    
    class Meta:
        model = ProjectGroupSupplier
        fields = ['project_number', 'survey_number', 'survey_name', 'cpi', 'statistics']

class FinalizedProjectGroupSerializer(serializers.ModelSerializer):
    project_number = serializers.SerializerMethodField()
    survey_number = serializers.SerializerMethodField()
    survey_name = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()

    def get_project_number(self, instance):
        return instance.project_group.project.project_number

    def get_survey_number(self, instance):
        return instance.project_group.project_group_number

    def get_survey_name(self, instance):
        return instance.project_group.project_group_name

    def get_statistics(self, instance):
        stats = RespondentDetail.objects.filter(project_group_number = instance.project_group.project_group_number, source = self.context['source'], url_type = 'Live')
        completes = stats.filter(resp_status = '4')        
        total_amount = completes.aggregate(Sum('supplier_cpi'))
        
        return [{'total_amount':total_amount['supplier_cpi__sum'], 'total_completes':completes.count(),}]
    
    class Meta:
        model = ProjectGroupSupplier
        fields = ['project_number', 'survey_number', 'survey_name', 'cpi', 'statistics']

class AcceptSupplierSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProjectGroupSupplier
        fields = [
            'id', 'project_group', 'supplier_org', 'completes', 'clicks', 'cpi', 'supplier_complete_url', 'supplier_terminate_url',
            'supplier_quotafull_url', 'supplier_securityterminate_url', 'supplier_survey_url', 
            'supplier_status',
        ]
        read_only_fields = ['id', 'project_group', 'supplier_org', 'completes', 'clicks', 'cpi', 'supplier_complete_url', 'supplier_terminate_url',
            'supplier_quotafull_url', 'supplier_securityterminate_url', 'supplier_survey_url', 
            'supplier_status',]
        extra_kwargs = {
            'supplier_complete_url':{
                'source': 'supplier_completeurl',
            },
            'supplier_terminate_url':{
                'source': 'supplier_terminateurl',
            },
            'supplier_quotafull_url':{
                'source': 'supplier_quotafullurl',
            },
            'supplier_securityterminate_url':{
                'source': 'supplier_securityterminateurl',
            },
        }


class SearchProjectListSerializer(serializers.ModelSerializer):
    project_number = serializers.SerializerMethodField()
    survey_number = serializers.SerializerMethodField()
    survey_name = serializers.SerializerMethodField()
    statistics = serializers.SerializerMethodField()
    language = serializers.CharField(source="project_group.project_group_language")
    country = serializers.CharField(source="project_group.project_group_country")
    status = serializers.CharField(source="project_group.project.project_status")

    def get_project_number(self, instance):
        return instance.project_group.project.project_number

    def get_survey_number(self, instance):
        return instance.project_group.project_group_number

    def get_survey_name(self, instance):
        return instance.project_group.project_group_name

    def get_statistics(self, instance):
        stats = RespondentDetail.objects.filter(project_group_number = instance.project_group.project_group_number, source = self.context['source'], url_type = 'Live')
        visits=stats.count()
        completes = stats.filter(resp_status = '4')
        all_status = stats.filter(resp_status__in = ['4','5','6','7']).count()
        incidence = 0
        if all_status>0:
            incidence = round(completes.count()/all_status,2)*100
        earning = completes.aggregate(Sum('supplier_cpi'))
        
        return [{'visits':visits, 'completes':completes.count(),'incidence':incidence,'earning':earning['supplier_cpi__sum']}]
    
    class Meta:
        model = ProjectGroupSupplier
        fields = ['project_number', 'status','survey_number', 'survey_name', 'cpi', 'statistics','language','country']


class SurveyPrescreenerViewSerializer(serializers.ModelSerializer):
    parent_question_number = serializers.SerializerMethodField()
    parent_question_text = serializers.SerializerMethodField()
    parent_question_type = serializers.SerializerMethodField()
    answer_options = serializers.SerializerMethodField()
    zipcode_counts = serializers.SerializerMethodField()

    def get_zipcode_counts(self,obj):
        return ZipCode.objects.filter(project_group_id = obj.project_group_id).count() + len(obj.allowed_zipcode_list) if obj.allowed_zipcode_list != [] else 0

    def get_parent_question_number(self, obj):
        return obj.translated_question_id.parent_question.parent_question_number
    
    def get_parent_question_text(self, obj):
        return obj.translated_question_id.parent_question.parent_question_text

    def get_parent_question_type(self, obj):
        return obj.translated_question_id.parent_question.parent_question_type

    def get_answer_options(self, obj):
        return obj.allowedoptions.values('parent_answer_id', 'parent_answer__parent_answer_text', 'id', 'translated_answer')

    class Meta:
        model = ProjectGroupPrescreener
        fields = ['parent_question_number', 'parent_question_text', 'parent_question_type', 
                 'answer_options', 'allowedRangeMin','allowedRangeMax', 'zipcode_counts']

class SupplierInvoiceFileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierInvoice
        fields = ['id', 'supplier_invoice_file']
