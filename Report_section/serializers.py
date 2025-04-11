# *********** django libraries ***************
from django.db.models import Sum

# *********** rest-framework libraries ***************
from rest_framework import serializers

# *********** in-project imports ***************
from Project.models import *
from Surveyentry.models import *
from employee.models import *


class PMworkloadSerializer(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField()

    def get_projects(self, instance):
        project_obj = self.context['projectList'].filter(project_manager = instance)

        try:
            month = self.context['querystring']['month']
        except:
            month = datetime.now().month
        try:
            year = self.context['querystring']['year']
        except:
            year = datetime.now().year

        revenue = RespondentDetail.objects.filter(resp_status=4, respondentdetailsrelationalfield__project__project_manager = instance, url_type='Live',respondentdetailsrelationalfield__project__project_revenue_month = month, respondentdetailsrelationalfield__project__project_revenue_year = year).exclude(source = 0).aggregate(Sum('project_group_cpi'))
        
        expense = RespondentDetail.objects.filter(resp_status = 4, respondentdetailsrelationalfield__project__project_manager = instance, url_type='Live',respondentdetailsrelationalfield__project__project_revenue_month = month, respondentdetailsrelationalfield__project__project_revenue_year = year).exclude(source = 0).aggregate(Sum('supplier_cpi'))
        projectvalue = {
            "live_projects":project_obj.filter(project_status="Live").count(),
            "paused_projects":project_obj.filter(project_status="Paused").count(),
            "closed_projects":project_obj.filter(project_status="Closed").count(),
            "reconciled_projects":project_obj.filter(project_status="Reconciled").count(),
            "total_revenue":revenue['project_group_cpi__sum'],
            "total_expense":expense['supplier_cpi__sum'],
           
        }
        return projectvalue

    class Meta:
        model = EmployeeProfile
        fields = ['first_name','last_name','email','projects']


class PMSalesworkloadSerializer(serializers.ModelSerializer):
    projects = serializers.SerializerMethodField()

    def get_projects(self, instance):
        project_obj = self.context['projectList'].filter(project_sales_person = instance)

        try:
            month = self.context['querystring']['month']
        except:
            month = datetime.now().month
        try:
            year = self.context['querystring']['year']
        except:
            year = datetime.now().year

        revenue = RespondentDetail.objects.filter(resp_status=4, respondentdetailsrelationalfield__project__project_sales_person = instance, url_type='Live',respondentdetailsrelationalfield__project__project_revenue_month = month, respondentdetailsrelationalfield__project__project_revenue_year = year).exclude(source = 0).aggregate(Sum('project_group_cpi'))
        
        expense = RespondentDetail.objects.filter(resp_status = 4, respondentdetailsrelationalfield__project__project_sales_person = instance, url_type='Live',respondentdetailsrelationalfield__project__project_revenue_month = month, respondentdetailsrelationalfield__project__project_revenue_year = year).exclude(source = 0).aggregate(Sum('supplier_cpi'))
        projectvalue = {
            "live_projects":project_obj.filter(project_status="Live").count(),
            "paused_projects":project_obj.filter(project_status="Paused").count(),
            "closed_projects":project_obj.filter(project_status="Closed").count(),
            "reconciled_projects":project_obj.filter(project_status="Reconciled").count(),
            "total_revenue":revenue['project_group_cpi__sum'],
            "total_expense":expense['supplier_cpi__sum'],
           
        }
        return projectvalue

    class Meta:
        model = EmployeeProfile
        fields = ['first_name','last_name','email','projects']


class CustomerReportingSerializer(serializers.ModelSerializer):
    expense = serializers.SerializerMethodField()
    revenue = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = ["id", "project_number", "project_name", "expense", "revenue", "project_total_revenue"]
        

    def get_expense(self, instance):
        expense = RespondentDetail.objects.filter(project_number=instance.project_number, resp_status=4, url_type='Live').aggregate(Sum("supplier_cpi"))
        return expense['supplier_cpi__sum']

    def get_revenue(self, instance):
        revenue = RespondentDetail.objects.filter(resp_status=4,project_number=instance.project_number, url_type='Live').aggregate(Sum("project_group_cpi"))
        return revenue['project_group_cpi__sum']
