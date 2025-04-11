from rest_framework import serializers
from django.db.models import Sum, Avg
from Surveyentry.models import *
from Project.models import *


class LiveProjectListSubSupplierSerializer(serializers.ModelSerializer):
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
        stats = RespondentDetail.objects.filter(project_group_number = instance.project_group.project_group_number, respondenturldetail__sub_sup_id = self.context['sub_source'], url_type = 'Live')
        visits=stats.count()
        completes = stats.filter(resp_status = '4')
        all_status = stats.filter(resp_status__in = ['4','5','6','7']).count()
        incidence = 0
        if all_status>0:
            incidence = round(completes.count()/all_status,2)*100
        earning = completes.aggregate(Sum('supplier_cpi'))
        
        return [{'visits':visits, 'completes':completes.count(),'incidence':incidence,'earning':earning['supplier_cpi__sum']}]
    
    class Meta:
        model = ProjectGroupSubSupplier
        fields = ['project_number', 'survey_number', 'survey_name', 'cpi', 'statistics']



class ClosedProjectGroupSubSupplierSerializer(serializers.ModelSerializer):
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
        stats = RespondentDetail.objects.filter(project_group_number = instance.project_group.project_group_number, respondenturldetail__sub_sup_id = self.context['sub_source'], url_type = 'Live')
        completes = stats.filter(resp_status__in = ['4','8','9'])
        total_amount = completes.aggregate(Sum('supplier_cpi'))
        
        return [{'total_amount':total_amount['supplier_cpi__sum'], 'total_completes':completes.count(),}]
    
    class Meta:
        model = ProjectGroupSubSupplier
        fields = ['project_number', 'survey_number', 'survey_name', 'cpi', 'statistics']



class SupplierContactSerializer(serializers.ModelSerializer):

    contact_number = serializers.CharField(
        source='subsupplier_contactnumber',
        required=False,
        allow_null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,13}$',
                            message="Contact number must be in the format of '+123456789'. Up to 13 digits allowed.")],
    )

    subsupplier_id = serializers.CharField(source = 'subsupplier_id.sub_supplier_code')

    class Meta:
        model = SubSupplierContact
        fields = [
            "id", 'first_name', 'last_name', 'email', 'contact_number', 'subsupplier_id', 'subsupplier_contact_status','subsend_supplier_updates','subsend_final_ids', 'subsupplier_dashboard_registration'
        ]
        extra_kwargs = {
            'email': {
                'source': 'subsupplier_email',
            },
            'first_name': {
                'source': 'subsupplier_firstname',
            },
            'last_name': {
                'source': 'subsupplier_lastname',
            },
        }


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
        

class subsupplierAddSerializer(serializers.ModelSerializer):
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
        model = ProjectGroupSubSupplier
        fields = ['project_number','survey_name','cpi','completes', 'sub_supplier_status','loi','incidence', 'targeting_description', 'sub_supplier_survey_url','sub_supplier_completeurl', 'sub_supplier_terminateurl', 'sub_supplier_quotafullurl', 'sub_supplier_securityterminateurl', 'sub_supplier_internal_terminate_redirect_url', 'sub_supplier_terminate_no_project_available','sub_supplier_postbackurl']
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
            'sub_supplier_survey_url':{
                'read_only': True,
            },
            'sub_supplier_completeurl':{
                'required': True,
            },
            'sub_supplier_terminateurl':{
                'required': True,
            },
            'sub_supplier_quotafullurl':{
                'required': True,
            },
            'sub_supplier_securityterminateurl':{
                'required': True,
            },
        }



class ProjectGroupNewSurveyAvailableSerializer(serializers.ModelSerializer):
    
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
            max_cpi = SubSupplierOrganisation.objects.get(sub_supplier_code = self.context['sub_source']).max_authorized_cpi
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