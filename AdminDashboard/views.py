from django.db import connection
from django.db.models import Q
from django.db.models.functions import Cast,Coalesce,TruncMonth, Concat
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.template.loader import render_to_string
#================= restframework library ====================
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

# in-project imports
from AdminDashboard.serializers import *
from Bid.models import Bid
from Invoice.models import Invoice, InvoiceRow
from Project.models import *
from Project.serializers import median_value
from SupplierInvoice.models import ProjectInvoicedApproved, ProjectSecondaryAuditApproved, SupplierInvoice, SupplierInvoiceRow
from affiliaterouter.models import Visitors

# third_party module imports
from knox.auth import TokenAuthentication
from datetime import datetime, timedelta
from operator import itemgetter

from automated_email_notifications.email_configurations import sendEmailSendgripAPIIntegration



def dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


# Create your views here.
class OverallHealthView(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 
    serializer_class = OverallHealthSerializer
    queryset = Project.objects.all()


class LiveProjectGroupWiseStatsAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        days30ago_time = datetime.now() - timedelta(days=30)
        projectgrp_qs_list = ProjectGroup.objects.filter(project_group_status='Live').order_by('-project__project_number','-project_group_number').values('project_group_number').annotate(completes=Count('respondentdetailsrelationalfield__respondent__resp_status', filter=Q(respondentdetailsrelationalfield__respondent__resp_status='4',respondentdetailsrelationalfield__respondent__url_type='Live')), incompletes=Count('respondentdetailsrelationalfield__respondent__resp_status',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='3')),
                terminates=Count('respondentdetailsrelationalfield__respondent__resp_status',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='5')),quota_full=Count('respondentdetailsrelationalfield__respondent__resp_status',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='6')),security_terminate=Count('respondentdetailsrelationalfield__respondent__resp_status',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='7')),starts=Cast(F('incompletes')+F('completes')+F('terminates')+F('quota_full')+F('security_terminate'), output_field=models.FloatField()), 
                conversion=Case(When(Q(starts=0),then=0), default=Cast((F('completes')/F('starts'))*100, output_field=models.DecimalField(max_digits=7, decimal_places=2)), output_field=models.DecimalField(max_digits=7, decimal_places=2)), 
                country=F('project_group_country__country_name'), Language=F('project_group_language__language_name'), 
                revenue=Coalesce(Cast(Sum('respondentdetailsrelationalfield__respondent__project_group_cpi', filter=Q(respondentdetailsrelationalfield__respondent__resp_status='4',respondentdetailsrelationalfield__respondent__url_type='Live')), output_field=models.DecimalField(max_digits=7, decimal_places=2)), Value(0), output_field=models.DecimalField(max_digits=7, decimal_places=2)), 
                expense=Coalesce(Cast(Sum('respondentdetailsrelationalfield__respondent__supplier_cpi', filter=Q(respondentdetailsrelationalfield__respondent__resp_status='4',respondentdetailsrelationalfield__respondent__url_type='Live')), output_field=models.DecimalField(max_digits=7, decimal_places=2)), Value(0), output_field=models.DecimalField(max_digits=7, decimal_places=2)), 
                project_number=F('project__project_number'), customer_name=F('project__project_customer__cust_org_name')
        )
        return Response(projectgrp_qs_list)


class Last7DayWiseOnlyStatsAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        todays_date = datetime.now().date()
        todays_time = datetime.now()
        seven_days_ago = datetime.now().date() - timedelta(days=7)
        seven_days_time = datetime.now() - timedelta(days=7)
        resp_details_list = RespondentDetail.objects.filter(end_time_day__lte=todays_date, end_time_day__gte=seven_days_ago).values('end_time_day').annotate(completes=Count('id', filter=Q(resp_status='4',url_type='Live')), 
        revenue=Coalesce(Sum('project_group_cpi', filter=Q(resp_status='4',url_type='Live')), Value(0.0)), expense=Coalesce(Sum('supplier_cpi', filter=Q(resp_status='4',url_type='Live')), Value(0.0))
        )

        with connection.cursor() as cursor:
            cursor.execute("SELECT created_at::date AS created_at__date, COUNT(id) AS total_projects FROM Project_project WHERE created_at <= %s and created_at >= %s GROUP BY created_at::date", [todays_time,seven_days_time])
            project_list = dictfetchall(cursor)

        last_7days_date = []
        last_7days_date = [todays_date-timedelta(days=item) for item in range(0,7)]

        resp_7days_date = [item['end_time_day'] for item in resp_details_list]
        resp_details_lists = list(resp_details_list)
        for date in last_7days_date:
            if date not in resp_7days_date:
                resp_details_lists.append({'end_time_day':date, 'completes':0, 'revenue':0, 'expense':0})

        project_7days_date = [item['created_at__date'] for item in project_list]
        for date in last_7days_date:
            if date not in project_7days_date:
                project_list.append({'created_at__date':date, 'total_projects':0})

        project_list = sorted(project_list, key=itemgetter('created_at__date'))
        resp_details_lists = sorted(resp_details_lists, key=itemgetter('end_time_day'))

        for resp_data,prj_data in zip(resp_details_lists,project_list):
            resp_data.update({'total_projects':prj_data['total_projects']})

        return Response(resp_details_lists)


class DayWiseCompleteCountsAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        requested_days = request.GET.get('day')

        if requested_days and requested_days not in ['1D','3D','7D','15D','1M','6M','1Y']:
            return Response({'detail':'You do not have access to view this API'})

        elif requested_days and requested_days in ['1D','3D','7D','15D','1M','6M','1Y']:
            todays_date = datetime.now().date()
            if requested_days == '1D':
                days_ago = todays_date - timedelta(days=1)
                resp_details_list = RespondentDetail.objects.filter(end_time_day__lte=todays_date, end_time_day__gte=days_ago, url_type='Live').values('end_time_day').annotate(completes=Count('resp_status', filter=Q(resp_status='4')), incompletes=Count('resp_status', filter=Q(resp_status='3')), terminates=Count('resp_status', filter=Q(resp_status='5')), quota_full=Count('resp_status', filter=Q(resp_status='6')), date_wise_data=F('end_time_day')
                )
            elif requested_days == '3D':
                days_ago = todays_date - timedelta(days=3)
                resp_details_list = RespondentDetail.objects.filter(end_time_day__lte=todays_date, end_time_day__gte=days_ago, url_type='Live').values('end_time_day').annotate(completes=Count('resp_status', filter=Q(resp_status='4')), incompletes=Count('resp_status', filter=Q(resp_status='3')), terminates=Count('resp_status', filter=Q(resp_status='5')), quota_full=Count('resp_status', filter=Q(resp_status='6')), date_wise_data=F('end_time_day')
                )
            elif requested_days == '7D':
                days_ago = todays_date - timedelta(days=7)
                resp_details_list = RespondentDetail.objects.filter(end_time_day__lte=todays_date, end_time_day__gte=days_ago, url_type='Live').values('end_time_day').annotate(completes=Count('resp_status', filter=Q(resp_status='4')), incompletes=Count('resp_status', filter=Q(resp_status='3')), terminates=Count('resp_status', filter=Q(resp_status='5')), quota_full=Count('resp_status', filter=Q(resp_status='6')), date_wise_data=F('end_time_day')
                )
            elif requested_days == '15D':
                days_ago = todays_date - timedelta(days=15)
                resp_details_list = RespondentDetail.objects.filter(end_time_day__lte=todays_date, end_time_day__gte=days_ago, url_type='Live').values('end_time_day').annotate(completes=Count('resp_status', filter=Q(resp_status='4')), incompletes=Count('resp_status', filter=Q(resp_status='3')), terminates=Count('resp_status', filter=Q(resp_status='5')), quota_full=Count('resp_status', filter=Q(resp_status='6')), date_wise_data=F('end_time_day')
                )
            elif requested_days == '1M':
                days_ago = todays_date - timedelta(days=30)

                resp_details_list = RespondentDetail.objects.filter(end_time_day__lte=todays_date, end_time_day__gte=days_ago, url_type='Live').values('end_time_day').annotate(completes=Count('resp_status', filter=Q(resp_status='4')), incompletes=Count('resp_status', filter=Q(resp_status='3')), terminates=Count('resp_status', filter=Q(resp_status='5')), quota_full=Count('resp_status', filter=Q(resp_status='6')), date_wise_data=F('end_time_day')

                )
            elif requested_days == '6M':
                days_ago = todays_date - timedelta(days=180)
                resp_details_list = RespondentDetail.objects.filter(end_time_day__lte=todays_date, end_time_day__gte=days_ago, url_type='Live').annotate(month=TruncMonth('end_time_day')).values('month').annotate(completes=Count('resp_status', filter=Q(resp_status='4')), incompletes=Count('resp_status', filter=Q(resp_status='3')), terminates=Count('resp_status', filter=Q(resp_status='5')), quota_full=Count('resp_status', filter=Q(resp_status='6')), date_wise_data=F('month')
                )
            elif requested_days == '1Y':
                days_ago = todays_date - timedelta(days=365)

                resp_details_list = RespondentDetail.objects.filter(end_time_day__lte=todays_date, end_time_day__gte=days_ago, url_type='Live').annotate(month=TruncMonth('end_time_day')).values('month').annotate(completes=Count('resp_status', filter=Q(resp_status='4')), incompletes=Count('resp_status', filter=Q(resp_status='3')), terminates=Count('resp_status', filter=Q(resp_status='5')), quota_full=Count('resp_status', filter=Q(resp_status='6')), date_wise_data=F('month')

                )
            return Response(resp_details_list)
        else:
            todays_date = datetime.now().date()
            days_ago = todays_date - timedelta(days=1)
            resp_details_list = RespondentDetail.objects.filter(end_time_day__lte=todays_date, end_time_day__gte=days_ago, url_type='Live').values('end_time_day').annotate(completes=Count('resp_status', filter=Q(resp_status='4')), incompletes=Count('resp_status', filter=Q(resp_status='3')), terminates=Count('resp_status', filter=Q(resp_status='5')), quota_full=Count('resp_status', filter=Q(resp_status='6'))
            )
            return Response(resp_details_list)


class ProjectStatusCountsAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        projects_count_dict = Project.objects.all().aggregate(live=Count('project_status', filter=Q(project_status='Live')), paused=Count('project_status', filter=Q(project_status='Paused')), closed=Count('project_status', filter=Q(project_status='Closed')), reconciled=Count('project_status', filter=Q(project_status='Reconciled'))
        )
        return Response(projects_count_dict)


class MonthWiseCustomerStatsCountAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        requested_months = request.GET.get('months')
        requested_years = request.GET.get('year')

        if requested_months in ['', None, 'undefined']:
            requested_months = datetime.now().month
        else:
            requested_months = requested_months.split(',')
        if requested_years in ['', None, 'undefined']:
            requested_years = datetime.now().year
        else:
            requested_years = requested_years.split(',')

        if type(requested_months) == int:
            resp_details_list = RespondentDetail.objects.filter(end_time_day__month=requested_months, url_type='Live')
        elif type(requested_months) == list:
            resp_details_list = RespondentDetail.objects.filter(end_time_day__month__in=requested_months, url_type='Live')

        if type(requested_years) == int:
            resp_details_list = resp_details_list.filter(end_time_day__year=requested_years)
        elif type(requested_years) == list:
            resp_details_list = resp_details_list.filter(end_time_day__year__in=requested_years)

        resp_details_list = resp_details_list.values(
            customer_name=F('respondentdetailsrelationalfield__project__project_customer__cust_org_name')
        ).annotate(
            completes=Count('resp_status', filter=Q(resp_status='4')), 
            incompletes=Count('resp_status',filter=Q(resp_status='3')),
            terminates=Count('resp_status',filter=Q(resp_status='5')), 
            quota_full=Count('resp_status',filter=Q(resp_status='6')),
            security_terminate=Count('resp_status',filter=Q(resp_status='7')), 
            starts=Cast(F('incompletes')+F('completes')+F('terminates')+F('quota_full')+F('security_terminate'), output_field=models.FloatField()), 
            conversion_rate=Case(
                When(Q(starts=0),then=Cast(0.0, output_field=models.DecimalField(max_digits=7,decimal_places=2))), 
                default=Cast(F('completes')/F('starts')*100, output_field=models.DecimalField(max_digits=7,decimal_places=2))
            ),
            revenue=Coalesce(
                Sum(
                    'project_group_cpi', 
                    filter=Q(resp_status__in=['4','9'])
                ),0.0
            ),
            expense=Coalesce(
                Sum(
                    'supplier_cpi', 
                    filter=Q(resp_status='4')
                ), 0.0
            ),
            margin=Case(
                When(Q(revenue=0.0)|Q(revenue=None),then=Cast(0.0, models.DecimalField(max_digits=7,decimal_places=2))), 
                default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'), output_field=models.DecimalField(max_digits=7,decimal_places=2)),
            ),
            client_rejected=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='8', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','ReadyForInvoiceApproved','ReadyForInvoice','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ),
            completesII=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='4', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','ReadyForInvoiceApproved','ReadyForInvoice','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ),
            pvp_rejected=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='9', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','ReadyForInvoiceApproved','ReadyForInvoice','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ),
            rejection_rate=Cast(
                Case(When(Q(completesII=0) & Q(client_rejected=0) & Q(pvp_rejected=0),then='completesII'), 
                default=(F('client_rejected') / (F('completesII') + F('client_rejected') + F('pvp_rejected')))*100), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            )
        )
        return Response(resp_details_list)


class MonthWiseSupplierStatsCountAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        requested_months = request.GET.get('months')
        requested_years = request.GET.get('year')

        if requested_months in ['', None, 'undefined']:
            requested_months = datetime.now().month
        else:
            requested_months = requested_months.split(',')
        if requested_years in ['', None, 'undefined']:
            requested_years = datetime.now().year
        else:
            requested_years = requested_years.split(',')

        if type(requested_months) == int:
            resp_details_list = RespondentDetail.objects.filter(end_time_day__month=requested_months, url_type='Live')
        elif type(requested_months) == list:
            resp_details_list = RespondentDetail.objects.filter(end_time_day__month__in=requested_months, url_type='Live')

        if type(requested_years) == int:
            resp_details_list = resp_details_list.filter(end_time_day__year=requested_years)
        elif type(requested_years) == list:
            resp_details_list = resp_details_list.filter(end_time_day__year__in=requested_years)

        resp_details_list = resp_details_list.values('end_time_day__month').annotate(
            supplier_name=Case(
                When(Q(respondentdetailsrelationalfield__source__supplier_name=None),then=Value('-')), 
                default=F('respondentdetailsrelationalfield__source__supplier_name')
            ), 
            completes=Count('resp_status', filter=Q(resp_status='4')), 
            incompletes=Count('resp_status',filter=Q(resp_status='3')),
            terminates=Count('resp_status',filter=Q(resp_status='5')), 
            quota_full=Count('resp_status',filter=Q(resp_status='6')), 
            security_terminate=Count('resp_status',filter=Q(resp_status='7')), 
            starts=Cast(
                F('incompletes')+F('completes')+F('terminates')+F('quota_full')+F('security_terminate'), 
                output_field=models.DecimalField(max_digits=7, decimal_places=2)
            ), 
            conversion_rate=Case(
                When(Q(starts=0),then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))), 
                default=Cast(
                    (F('completes')/F('starts'))*100, 
                    output_field=models.DecimalField(max_digits=7, decimal_places=2)
                )
            ), 
            revenue=Coalesce(
                Sum(
                    'project_group_cpi', 
                    filter=Q(resp_status__in=['4','9'])
                ), 0.0
            ), 
            expense=Coalesce(
                Sum(
                    'supplier_cpi', 
                    filter=Q(resp_status='4'), 
                ), 0.0
            ), 
            margin=Case(
                When(
                    Q(revenue=0.0)|Q(revenue=None),
                    then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))
                ),
                default=Cast(
                    ((F('revenue')-F('expense'))*100)/F('revenue'), 
                    output_field=models.DecimalField(max_digits=7,decimal_places=2)
                )
            ), 
            client_rejected=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='8', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','ReadyForInvoiceApproved','ReadyForInvoice','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ), 
            completesII=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='4', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','ReadyForInvoiceApproved','ReadyForInvoice','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ), 
            pvp_rejected=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='9', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','ReadyForInvoiceApproved','ReadyForInvoice','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ), 
            rejection_rate=Case(
                When(
                    Q(completesII=0) & Q(pvp_rejected=0),
                    then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))), 
                default=Cast(
                    (F('client_rejected') / (F('completesII') + F('client_rejected')))*100, 
                    output_field=models.DecimalField(max_digits=7,decimal_places=2)
                )
            )
        )
        return Response(resp_details_list)


class ProjectManagerWiseStatsAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        get_month = request.GET.get('months')
        requested_year = request.GET.get('year')

        if get_month in ['', None, 'undefined']:
            get_month = datetime.now().month
        if requested_year in ['', None, 'undefined']:
            requested_year = datetime.now().year

        emp_project_count = EmployeeProfile.objects.select_related('project_manager', 'project_manager__respondentdetailsrelationalfield__respondent').filter(is_superuser = False,user_type = '1',project_manager__project_revenue_month=get_month, project_manager__project_revenue_year=requested_year).exclude(emp_type = '10').values('email', pm_name=Concat('first_name', Value(' '), 'last_name')).order_by('id').annotate(
            live_projects=Count('project_manager__project_status', filter=Q(project_manager__project_status='Live')), 
            paused_projects=Count('project_manager__project_status', filter=Q(project_manager__project_status='Paused')), 
            closed_projects=Count('project_manager__project_status', filter=Q(project_manager__project_status='Closed')), 
            reconciled_projects=Count('project_manager__project_status', filter=Q(project_manager__project_status='Reconciled')), 
            invoiced_projects=Count('project_manager__project_status', filter=Q(project_manager__project_status='Invoiced'))
        )

        emp_resphits_sum = EmployeeProfile.objects.filter(is_superuser = False,user_type = '1',project_manager__project_revenue_month=get_month, project_manager__project_revenue_year=requested_year).exclude(emp_type = '10').values('email').order_by('id').annotate(
            revenue=Coalesce(
                    Sum(
                        'project_manager__respondentdetailsrelationalfield__respondent__project_group_cpi', 
                        filter=Q(project_manager__respondentdetailsrelationalfield__respondent__resp_status='4', project_manager__respondentdetailsrelationalfield__respondent__url_type='Live')
                    ), 0.0
                ),
            expense=Coalesce(
                    Sum(
                        'project_manager__respondentdetailsrelationalfield__respondent__supplier_cpi', 
                        filter=Q(project_manager__respondentdetailsrelationalfield__respondent__resp_status='4', project_manager__respondentdetailsrelationalfield__respondent__url_type='Live')
                    ), 0.0
                ),
            margin=Case(
                When(Q(revenue=0) | Q(revenue=None),then=Cast(0.0, output_field=models.DecimalField(max_digits=7,decimal_places=2))), 
                default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'), output_field=models.DecimalField(max_digits=7,decimal_places=2)), 
            )
        )

        pmwise_projecthits_list = []
        for project, respondent in zip(emp_project_count, emp_resphits_sum):
            project.update({'revenue':respondent['revenue'], 'expense':respondent['expense'], 'margin':respondent['margin']})
            pmwise_projecthits_list.append(project)

        return Response(pmwise_projecthits_list)

class ComputedOnHoldProjectsRespStatsAPI(ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ComputedOnHoldProjectsRespStatSerializer


    def get(self, request):
        fifteen_days_ago = datetime.now().date() - timedelta(days=15)
        project_number_list = RespondentDetail.objects.filter(end_time_day__gte=fifteen_days_ago, url_type='Live').values_list('project_number', flat=True)
        Project_obj = Project.objects.filter(project_status__in = ["Live","Paused","Closed"]).exclude(
        project_number__in = project_number_list
        ).values(
            'project_number',
            'project_name',
            client_name = F('project_customer__cust_org_name')
            ).annotate(
            revenue = Sum("respondentdetailsrelationalfield__respondent__project_group_cpi", filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,9],respondentdetailsrelationalfield__respondent__url_type = "Live" )),
            completes = Count('respondentdetailsrelationalfield__respondent',filter=Q(respondentdetailsrelationalfield__respondent__url_type = "Live")),
            expense = Sum('respondentdetailsrelationalfield__respondent__supplier_cpi'),
            margin = Cast(((F('revenue')-F('expense'))*100)/F('revenue'), output_field=models.DecimalField(max_digits=50, decimal_places=2)))
        if self.request.GET.get('user_id'):
            Project_obj = Project_obj.filter(project_manager = self.request.user)
        if self.request.GET.get('customercode'):
            Project_obj = Project_obj.filter(project_customer__in = self.request.GET.get('customercode'))
        if self.request.GET.get('project_status'):
            Project_obj = Project_obj.filter(project_status__in = self.request.GET.get('project_status'))
        
        return Response(Project_obj)
    
    def post(self,request):
        fifteen_days_ago = datetime.now().date() - timedelta(days=15)

        resp_details_qs = RespondentDetail.objects.filter(end_time_day__lte=fifteen_days_ago, url_type='Live', respondentdetailsrelationalfield__project__project_status__in=['Live','Paused','Closed'])

        resp_details_subquery = resp_details_qs.filter(project_number=OuterRef('project_number')).order_by('-end_time_day').values('end_time_day')[:1]

        resp_details_qs = resp_details_qs.values('respondentdetailsrelationalfield__project__project_number').annotate(
            project_name=F('respondentdetailsrelationalfield__project__project_name'), 
            project_status=F('respondentdetailsrelationalfield__project__project_status'), 
            customer=F('respondentdetailsrelationalfield__project__project_customer__cust_org_name'), 
            completes=Count('id', filter=Q(resp_status='4', url_type='Live')), 
            revenue=Coalesce(Cast(Sum('project_group_cpi', filter=Q(resp_status='4', url_type='Live')), output_field=models.DecimalField(max_digits=7, decimal_places=2)), Value(0)), 
            expense=Coalesce(Cast(Sum('supplier_cpi', filter=Q(resp_status='4', 
            url_type='Live')), output_field=models.DecimalField(max_digits=7, decimal_places=2)), Value(0)), 
            margin=Case(When(Q(revenue=0) | Q(revenue=None),then=Value(0)), default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'), output_field=models.DecimalField(max_digits=7, decimal_places=2))), 
            project_number=F('respondentdetailsrelationalfield__project__project_number'), 
            last_complete_date=Subquery(resp_details_subquery), 
            customercode=F('respondentdetailsrelationalfield__project__project_customer_id'), 
            user_id=F('respondentdetailsrelationalfield__project__project_manager_id')
        )

        ComputedOnHoldProjectsRespStats.objects.all().delete()

        for item in resp_details_qs:
            item.pop('respondentdetailsrelationalfield__project__project_number')
            ComputedOnHoldProjectsRespStats.objects.create(**item)

        return Response({"message":"Success"})


class AddProjectToStickyBoardView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    

    def post(self, request):
        project_number = request.data.get('project_number')
        if project_number:
            try:
                project_obj = Project.objects.get(project_number=project_number, project_status="Live")
            except Project.DoesNotExist:
                return Response({'error':'Please pass a valid live project number'}, status=status.HTTP_400_BAD_REQUEST)
            if project_obj.prj_sticky_board:
                data = {'error':'Project already added..!','project_number':project_obj.project_number, 'prj_sticky_board': project_obj.prj_sticky_board}
                return Response(data, status=status.HTTP_400_BAD_REQUEST)

            project_obj.prj_sticky_board = True
            project_obj.save()

            data = {'project_number':project_obj.project_number, 'prj_sticky_board': project_obj.prj_sticky_board}
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({'error':'Please pass a project number'}, status=status.HTTP_400_BAD_REQUEST)


class RemoveProjectStickyBoardView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    

    def post(self, request):
        project_number = request.data.get('project_number')
        if project_number:
            try:
                project_obj = Project.objects.get(project_number=project_number)
            except Project.DoesNotExist:
                return Response({'error':'Please pass a valid project number'}, status=status.HTTP_400_BAD_REQUEST)
            project_obj.prj_sticky_board = False
            project_obj.save()

            data = {'project_number':project_obj.project_number, 'prj_sticky_board': project_obj.prj_sticky_board}
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response({'error':'Please pass a project number'}, status=status.HTTP_400_BAD_REQUEST)


class StickyBoardProjectListView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    

    def get(self, request):
        project_values_qs = Project.objects.filter(prj_sticky_board=True).annotate(project_no=F('project_number'), cust_org_name=F('project_customer__cust_org_name'), revenue_month=F('project_revenue_month'), revenue_year=F('project_revenue_year'), criticality_level=F('project_criticality_level'), list_notes=F('project_list_notes')
        ).values('project_no', 'cust_org_name', 'revenue_month','revenue_year','criticality_level','list_notes')

        project_number_list = [item['project_no'] for item in project_values_qs]

        resp_details_values_qs = RespondentDetail.objects.filter(project_number__in=project_number_list, url_type='Live').values('project_number','project_group_number').annotate(required_completes=Sum(Cast('respondentprojectdetail__project_group_completes', output_field=IntegerField())), achieved_completes=Count('resp_status', filter=Q(resp_status='4')), incompletes=Count('resp_status',filter=Q(resp_status='3')),
            terminates=Count('resp_status',filter=Q(resp_status='5')), quota_full=Count('resp_status',filter=Q(resp_status='6')),security_terminate=Count('resp_status',filter=Q(resp_status='7')), starts=F('incompletes')+F('achieved_completes')+F('terminates')+F('quota_full')+F('security_terminate'), conversion_rate=Case(When(Q(starts=0),then=0.0), default=ExpressionWrapper((F('achieved_completes')/F('starts')*100),output_field=models.FloatField())), median_LOI=ExpressionWrapper(Value(round(float(median_value(RespondentDetail.objects.filter(resp_status__in=[4,8,9]), 'duration')),2)),output_field=models.FloatField())
        )

        project_values_qs_list = list(project_values_qs)

        for item in project_values_qs_list:
            resp_details_stats_list = []
            for item1 in resp_details_values_qs:
                if item['project_no'] == item1['project_number']:
                    resp_details_stats_list.append(item1)
                    item.update({'project_grp_stats':resp_details_stats_list})

        return Response(project_values_qs_list)


class ReserachDefenderFailureDataView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request,survey_no):

        research_defender_failure_obj = ResearchDefenderFailureReasonDataStore.objects.filter(respondent__project_group_number = survey_no).values(
            supplier_name = F('respondent__respondentdetailsrelationalfield__project_group_supplier__supplier_org__supplier_name'),
            rid = F('respondent__respondenturldetail__RID'),
            res_status = F('respondent__resp_status'),
            research_defender_response = F('defender_response')
        )
        
        return Response(research_defender_failure_obj, status=status.HTTP_200_OK)


class ProjectWiseManagerRevenueReport(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self,request):
        sher_no_of_project = float(request.GET.get('sher_no_of_project'))
        revenue = int(request.GET.get('revenue'))
        margin_i = int(request.GET.get('margin_i'))
        month = request.GET.get('month')
        year = request.GET.get('year')

        respondentdetaildata = RespondentDetail.objects.filter(resp_status__in = ['4','9'],
        respondentdetailsrelationalfield__project__invoice__invoice_date__month = month,
        respondentdetailsrelationalfield__project__invoice__invoice_date__year = year,url_type="Live")
        projectmanagerreport = respondentdetaildata.values(
            'respondentdetailsrelationalfield__project__project_manager',
            'respondentdetailsrelationalfield__project__project_manager__email').annotate(
                invoiced_project_count = Count('respondentdetailsrelationalfield__project__project_number',distinct=True),
                invoiced_project_count__point =  (Count('respondentdetailsrelationalfield__project__project_number',distinct=True)*100)/len(Project.objects.filter(invoice__invoice_date__month = month,invoice__invoice_date__year = year))*sher_no_of_project/100,
                
                invoice_total_amount = Sum('project_group_cpi'),
                invoice_total_amount__point = (Sum('project_group_cpi')*100/respondentdetaildata.aggregate(Sum("project_group_cpi"))['project_group_cpi__sum'])*revenue/100,
                
                margin = ((Sum('project_group_cpi') - Sum('supplier_cpi',filter=Q(resp_status='4')))),
                margin__point = (((F('margin')) * 100)/((respondentdetaildata.aggregate(Sum("project_group_cpi"))['project_group_cpi__sum'] - respondentdetaildata.aggregate(Sum("supplier_cpi"))['supplier_cpi__sum'])))*margin_i/100,
                
                total_points = F('invoiced_project_count__point') + F('invoice_total_amount__point') +F('margin__point')
            )

        return Response(projectmanagerreport)
    

class RouterReport(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        start_date = request.GET.get('start_date','2024-04-01')
        last_date = request.GET.get('last_date',None)
        source = request.GET.get('source',None)
        suppliertype = request.GET.get('suppliertype',None)
        visitorredirectobj = Visitors.objects.all()
        if source:
            visitorredirectobj = visitorredirectobj.filter(source = source)
        if start_date:
            visitorredirectobj = visitorredirectobj.filter(created_at__date__gte = start_date)
        if last_date:
            visitorredirectobj = visitorredirectobj.filter(created_at__date__lte = last_date)
        if suppliertype == '1':
            visitorredirectobj = visitorredirectobj.values('source') 
        elif suppliertype == '2':
            visitorredirectobj = visitorredirectobj.exclude(subsource__exact = '').values('subsource')
        try:
            visitorredirectobj = visitorredirectobj.annotate(
                visit = Count(F('id')),
                clientside_redirect = Count('id', filter=Q(respondent_status='2')),
                )
            return Response(visitorredirectobj, status=status.HTTP_200_OK)
        except:
            return Response({'message':'No Supplier Available'}, status=status.HTTP_400_BAD_REQUEST)


class SourceRouterReport(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def get(self,request,source):
        start_date = request.GET.get('start_date','2024-04-01')
        last_date = request.GET.get('last_date',None)
        suppliertype = request.GET.get('suppliertype',None)
        if suppliertype == '1':
            visitorredirectobj = RespondentDetail.objects.filter(us = '2',respondentdetailsrelationalfield__source__supplier_code = source)
        elif suppliertype == '2':
            visitorredirectobj = RespondentDetail.objects.filter(us = '2',respondenturldetail__sub_sup_id = source)
        else:
            return Response({'message':'No Survey Available'}, status=status.HTTP_400_BAD_REQUEST)
            
        if start_date:
            visitorredirectobj = visitorredirectobj.filter(start_time__date__gte = start_date)
        if last_date:
            visitorredirectobj = visitorredirectobj.filter(start_time__date__lte = last_date)

        visitorredirectobj = visitorredirectobj.values(
            survey_number = F('project_group_number')).annotate(
                client_redirect = Count('id'),
                client_side_completes=Count('id', filter=Q(resp_status='4')),
                client_sideinternal_terminate=Count('id', filter=Q(resp_status__in=['2'])),
                client_sidesecurity_terminate=Count('id', filter=Q(resp_status__in=['7'])),
                client_side_terminate=Count('id', filter=Q(resp_status__in=['5'])),
                client_side_incomplete=Count('id', filter=Q(resp_status__in=['3'])),
                client_side_quotafull=Count('id', filter=Q(resp_status__in=['6']))
            )
        if visitorredirectobj:
            return Response(visitorredirectobj, status=status.HTTP_200_OK) 
        else:
            return Response({'message':'No Survey Available'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectClientRevenueAndSupplierExpenseApi(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):

        page = self.request.GET.get('page',1)
        search_project_no = self.request.GET.get("search_project_no")
        project_status = self.request.GET.get("status",None)
        project_second_status = self.request.GET.get("secondstatus",None)
        
        project_obj = Project.objects.only(
            'id',
            'project_number',
            'project_status',
            'project_customer__cust_org_name'
            ).filter(
                project_status = "Invoiced", 
                )
        if search_project_no:
            project_obj = project_obj.filter(
                project_number__icontains = search_project_no
            )
        if project_status:
            if project_status == '1':
                project_obj = project_obj.exclude(
                    projectinvoicedapproved__project_invoice_status__in = ['2','3','4','5'] 
                )
            else:
                project_obj = project_obj.filter(
                    projectinvoicedapproved__project_invoice_status = str(project_status)
                )
        if project_second_status:
            if project_second_status == '1':
                project_obj = project_obj.exclude(
                    projectsecondaryauditapproved__project_audit_status__in = ['2','3','4','5'] 
                )
            else:
                project_obj = project_obj.filter(
                    projectsecondaryauditapproved__project_audit_status = str(project_second_status)
                )
        project_obj = project_obj.values(
                    'project_number',
                    'project_customer__cust_org_name',
                    invoice_date = F('invoicerow__invoice__invoice_date'),
                    invoice_currency = F('invoicerow__invoice__invoice_customer__customer_invoice_currency__currency_iso'),
                    ).annotate(
                        projectid = F('id'),
                        total_complete = Count('respondentdetailsrelationalfield',filter=Q(
                            respondentdetailsrelationalfield__respondent__resp_status__in=['4','9'],
                            respondentdetailsrelationalfield__respondent__url_type = "Live"), distinct=True),
                        
                        total_revenue = Coalesce(Cast(Sum(
                            'respondentdetailsrelationalfield__respondent__project_group_cpi',
                            filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=['4','9'],
                                    respondentdetailsrelationalfield__respondent__url_type = "Live")),
                                    output_field=models.DecimalField(max_digits=7, decimal_places=2)), Value(0),
                                    output_field=models.DecimalField(max_digits=7, decimal_places=2)),
                        
                        project_audit_status = F('projectinvoicedapproved__project_invoice_status'),
                        secondary_status = F('projectsecondaryauditapproved__project_audit_status')
                        ).order_by('-id','-projectinvoicedapproved__project_invoice_status')
        
        paginator = Paginator(project_obj,15)
        try:
            project_obj = paginator.page(page)
        except PageNotAnInteger:
            project_obj = paginator.page(1)
        except EmptyPage:
            project_obj = {"message":"No More Data Available.!"}
            return Response(project_obj, status=status.HTTP_400_BAD_REQUEST)

        return Response(project_obj.object_list, status=status.HTTP_200_OK)
    

class ProjectRevenueExpenseSurveyEntryWise(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        project_number = self.request.GET.get('project_number')

        respdata = RespondentDetail.objects.filter(
            project_number = project_number,
            url_type = 'Live',
            resp_status__in = ['4','8','9']
        ).values(
            supplier_cpii = F('supplier_cpi'),
            client_cpi = F('project_group_cpi'),
            supplier_name = F('respondentdetailsrelationalfield__source__supplier_name')
        ).annotate(
            project_group_number = F('project_group_number'),
            source = F('source'),
            total_completes = Count('id',filter=Q(resp_status__in=['4'])),
            completes_rejected_8 = Count('id',filter=Q(resp_status = '8')),
            completes_rejected_9 = Count('id',filter=Q(resp_status = '9'))
        )
        return Response(respdata, status=status.HTTP_200_OK)


class ProjectInvoiceReportDataView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def get(self, request):
            project_number = self.request.GET.get('project_number')

            project_obj = Project.objects.only(
                    'project_number',
                    'project_status',
                    'project_customer__cust_org_name'
                ).filter(
                    project_number = project_number,
                ).values(
                    invoice_number = F('invoicerow__invoice__invoice_number'),
                    invoice_complete = F('invoicerow__row_completes'),
                    invoice_cpi = F('invoicerow__row_cpi'),
                    invoice_currency = F('invoicerow__invoice__invoice_currency__currency_iso'),
                    invoice_total_amount = F('invoicerow__row_total_amount'),
                    conversion_rate = F('draftinvoice__conversion_rate'),
                )
            return Response(project_obj, status=status.HTTP_200_OK)


class ProjectWiseSupplierInvoiceReport(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        project_number = self.request.GET.get('project_number')
        supplier_invoice_row_obj = SupplierInvoiceRow.objects.filter(
            project__project_number = project_number
            ).values(
                'id',
                supplier_name = F("supplier_org__supplier_name"),
            ).annotate(
                supplier_invoice_id = F('supplier_invoice_id'),
                system_complete = F('completes'),
                system_cpi = F('cpi'),
                invoice_currency = F('supplier_invoice__currency__currency_iso'),
                invoiced_complete = F('invoiced_completes'),
                invoiced_cpis = F('invoiced_cpi'),
                total_amount = F('total_amount'),
                conversion_rate = F('supplier_invoice__conversion_rate'),
            )
        return Response(supplier_invoice_row_obj, status=status.HTTP_200_OK)


class ProjectReportInvoiceApprovedAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        project_number = request.data.get("project_number")
        revenue = request.data.get("revenue")
        expense = request.data.get("expense")
        project_status = request.data.get("status")
        operationcost = request.data.get("operationcost")

        try:
            margin = 0 if revenue == 0 else (float(revenue)-float(expense))*100/float(revenue)
            projectobj = Project.objects.get(project_number = project_number)
            ProjectInvoicedApproved.objects.update_or_create(
                project_id = projectobj.id,
                defaults = {
                    'revenue' : revenue,
                    'expense' : expense,
                    'margin' : margin,
                    'project_invoice_status' : project_status,
                    'operationcost' : operationcost,
                    'created_by' : request.user,
                }
            )
            return Response({"message":"Project Status Updated Successfully.!"}, status=status.HTTP_200_OK)
        except:
            return Response({"message":"Project Invoiced Already Approved..!"}, status=status.HTTP_400_BAD_REQUEST)


class SupplierInvoiceRowUpdateDashboard(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
 
    def put(self,request,id):
        if request.user.email == 'narendra@panelviewpoint.com':
            data = request.data
            SupplierInvoiceRow.objects.filter(
                id=id).update(
                    cpi = float(data['system_cpi']),
                    completes = int(data['system_complete']),
                )
 
            return Response({"message":"Supplier Invoice Row Updated..!"}, status=status.HTTP_200_OK)
        else:
            return Response({"message":"You Do Not Have Permission..!"}, status=status.HTTP_400_BAD_REQUEST)
   
    def delete(self,request,id):
 
        if request.user.email == 'narendra@panelviewpoint.com':
            SupplierInvoiceRow.objects.filter(id=id).delete()
            return Response({"message":"Supplier Invoice Row Deleted..!"}, status=status.HTTP_200_OK)
        else:
            return Response({"message":"You Do Not Have Permission..!"}, status=status.HTTP_400_BAD_REQUEST)


class EmailSendProjectManagerCPIUpdate(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self,request,project_number):
        supplierdata = request.data['supplierdata']
        project_obj = Project.objects.get(project_number = project_number)
        if settings.SERVER_TYPE == 'production':
            projecturl = f'https://admin.panelviewpoint.com/projects/details/{project_obj.id}?suppliercpipopup=open'
            to_emails = [project_obj.project_manager.email,'deepak@panelviewpoint.com','projects@panelviewpoint.com']
            if project_obj.secondary_project_manager:
                to_emails.append(project_obj.secondary_project_manager.email)
            cc_emails = 'audit@panelviewpoint.com'
        else:
            projecturl = f'http://192.168.1.16:5000/projects/details/{project_obj.id}?suppliercpipopup=open'
            to_emails = [project_obj.project_manager.email]
            if project_obj.secondary_project_manager:
                to_emails.append(project_obj.secondary_project_manager.email)
            cc_emails = 'tech@panelviewpoint.com'
            
        htmldata = {
            'project_number' : project_number,
            'projecturl' : projecturl,
            'supplierdata' : supplierdata
        }
        html_message = render_to_string('Project/project_manager_cpi_update_notify.html',htmldata)
       
        sendEmailSendgripAPIIntegration(
            to_emails = to_emails,
            cc_emails = cc_emails,
            subject = f'CPI MisMatch in ProjectNumber - {project_number}',
            html_message= html_message
        )
        ProjectCPIApprovedManager.objects.filter(project__project_number = project_number).delete()
        return Response({"message":"Email Send Successfully..!"}, status=status.HTTP_200_OK)


class ProjectsecondaryInvoiceApprovedAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self,request):
        try:
            if request.user.email == 'narendra@panelviewpoint.com':
                project_number = request.data.get("project_number")
                project_status = request.data.get("status")
                projectobj = Project.objects.get(project_number = project_number)
                ProjectSecondaryAuditApproved.objects.update_or_create(
                    project_id = projectobj.id,
                    defaults={
                        'project_audit_status' : project_status
                    }
                )
                return Response({"message":"Project Status Updated Successfully.!"}, status=status.HTTP_200_OK)
            else:
                return Response({"message":"You Do Not Have Permission..!"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"error":"Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)


class ClientSupplierPMWiseReport(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):

        requested_months = request.GET.get('months')
        requested_years = request.GET.get('year')
        wise = request.GET.get('wise')

        if requested_months in ['', None, 'undefined']:
            requested_months = datetime.now().month
        else:
            requested_months = requested_months.split(',')
        if requested_years in ['', None, 'undefined']:
            requested_years = datetime.now().year
        else:
            requested_years = requested_years.split(',')

        if type(requested_months) == int:
            resp_details_list = RespondentDetail.objects.filter(end_time_day__month=requested_months, url_type='Live',
            respondentdetailsrelationalfield__project__project_status__in=['Reconciled','ReadyForInvoiceApproved','ReadyForInvoice','Invoiced'])
        elif type(requested_months) == list:
            resp_details_list = RespondentDetail.objects.filter(end_time_day__month__in=requested_months, url_type='Live',
            respondentdetailsrelationalfield__project__project_status__in=['Reconciled','ReadyForInvoiceApproved','ReadyForInvoice','Invoiced'])

        if type(requested_years) == int:
            resp_details_list = resp_details_list.filter(end_time_day__year=requested_years)
        elif type(requested_years) == list:
            resp_details_list = resp_details_list.filter(end_time_day__year__in=requested_years)

        if wise == '1':#Customer Wise
            resp_details_list = resp_details_list.order_by('respondentdetailsrelationalfield__project__project_customer__cust_org_name').values(
                customer_name=F('respondentdetailsrelationalfield__project__project_customer__cust_org_name')
            )
        elif wise =='2':#Supplier Wise
            resp_details_list = resp_details_list.order_by('respondentdetailsrelationalfield__source__supplier_name').values(
                suppliers_name=F('respondentdetailsrelationalfield__source__supplier_name')
            )
        elif wise == '3':#Project Manager Wise
            resp_details_list = resp_details_list.order_by('respondentdetailsrelationalfield__project__project_manager__email').values(
                project_manager=F('respondentdetailsrelationalfield__project__project_manager__email')
            )
        resp_details_list = resp_details_list.annotate(
            completes=Count('resp_status', filter=Q(resp_status__in=['4','8','9'])),
            completes_approved=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='4', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','ReadyForInvoiceApproved','ReadyForInvoice','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ),
            client_rejected=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='8', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','ReadyForInvoiceApproved','ReadyForInvoice','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ),
            pvp_rejected=Cast(
                Count(
                    'resp_status', 
                    filter=Q(resp_status='9', respondentdetailsrelationalfield__project__project_status__in=['Reconciled','ReadyForInvoiceApproved','ReadyForInvoice','Invoiced'])
                ), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            ),
            rejection_rate=Cast(
                Case(When(Q(completes_approved=0) & Q(client_rejected=0) & Q(pvp_rejected=0),then='completes_approved'), 
                default=(F('client_rejected') / (F('completes_approved') + F('client_rejected') + F('pvp_rejected')))*100), output_field=models.DecimalField(max_digits=7,decimal_places=2)
            )
        )
        return Response(resp_details_list, status=status.HTTP_200_OK)


class ProjectManagerINRReport(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            month = request.GET.get('month',datetime.now().month)
            year = request.GET.get('year',datetime.now().year)
            conversion = float(request.GET.get('conversion',1.0))
            projectmanagerreport = {}

            Invoicerowdata = InvoiceRow.objects.filter(
                invoice__created_at__year = year,
                invoice__created_at__month = month
            ).exclude(invoice__invoice_status='4')

            Invoicerowrevenue = Invoicerowdata.values(
                project_manager = F('row_project_number__project_manager__email')
            ).annotate(
                revenue=Sum(
                    Case(
                        When(invoice__invoice_currency__currency_iso='USD', then=F('row_total_amount') * Value(conversion)),
                        default=F('row_total_amount'),
                        output_field=DecimalField(),
                    )
                ),
            ).order_by('row_project_number__project_manager__email')
            
            Invoicerowexpense = RespondentDetail.objects.filter(
                project_number__in = Invoicerowdata.values_list('row_project_number__project_number',flat=True).distinct(),
                url_type='Live'
                ).values(
                    project_manager = F('respondentdetailsrelationalfield__project__project_manager__email')).annotate(
                        expense=Coalesce(Sum('supplier_cpi', filter=Q(resp_status='4'))*conversion, 0.0)
                )
            projectmanagerreport = {
                'Invoicerowrevenue' : Invoicerowrevenue,
                'Invoicerowexpense' : Invoicerowexpense
            }
            
            return Response(projectmanagerreport, status=status.HTTP_200_OK)
        except:
            return Response({'error':'Something want wrong'}, status=status.HTTP_400_BAD_REQUEST)



class ProjectReportAuditMultipleInvoicedApprovedAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def post(self, request):
        
        try:
            if request.user.email == 'narendra@panelviewpoint.com':
                for data in request.data:
                    margin = float(data["revenue"])-float(data["expense"])*100/float(data["revenue"])
                    projectobj = Project.objects.get(project_number = data["project_number"])
                    ProjectInvoicedApproved.objects.update_or_create(
                        project_id = projectobj.id,
                        defaults = {
                            'revenue' : data["revenue"],
                            'expense' : data["expense"],
                            'margin' : margin,
                            'project_invoice_status' : data['status'],
                            'operationcost' : data["operationcost"],
                            'created_by' : request.user,
                        }
                    )
                return Response({"message":"Project Status Updated Successfully.!"}, status=status.HTTP_200_OK)
            else:
                return Response({"error":"You don't have access.!"}, status=status.HTTP_400_BAD_REQUEST)

        except:
            return Response({"message":"Project Invoiced Already Approved..!"}, status=status.HTTP_400_BAD_REQUEST)


class SalesOverviewApis(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
 
    def get(self,request):
        try:
            invoice_dict = {}
            invoiced_data =  Invoice.objects.filter(invoice_date__year = datetime.now().year)
            supplier_invoiced_data = SupplierInvoice.objects.filter(invoice_date__year = datetime.now().year)
 
            invoice_dict = {
                "this_year_invoiced_amount" : invoiced_data.values(currency = F('invoice_currency__currency_iso')).annotate(invoice_total_amount = Sum('invoice_total_amount')),
 
                "this_month_invoiced_amount" : invoiced_data.filter(invoice_date__month = datetime.now().month).values(currency = F('invoice_currency__currency_iso')).annotate(invoice_total_amount = Sum('invoice_total_amount')),
 
                "this_year_due_invoices" : invoiced_data.filter(invoice_status = '2',invoice_due_date__lte = datetime.now().date()).values(currency = F('invoice_currency__currency_iso')).annotate(invoice_total_amount = Sum('invoice_total_amount')),
 
                "this_month_due_invoices" : invoiced_data.filter(invoice_status = '2',invoice_due_date__lte = datetime.now().date(),invoice_date__month = datetime.now().month).values(currency = F('invoice_currency__currency_iso')).annotate(invoice_total_amount = Sum('invoice_total_amount')),
 
                "this_year_supplier_invoice_received" : supplier_invoiced_data.filter(invoice_status__in = ['1','4','5','6']).values(supplier_currency = F('currency__currency_iso')).annotate(invoice_total_amount = Sum('total_from_invoice_amount')),
 
                "this_month_supplier_invoice_received" : supplier_invoiced_data.filter(invoice_status__in = ['1','4','5','6'],invoice_date__month = datetime.now().month).values(supplier_currency = F('currency__currency_iso')).annotate(invoice_total_amount = Sum('total_from_invoice_amount')),
 
                "this_year_supplier_invoice_due" : supplier_invoiced_data.filter(invoice_status = '4',supplierinvoicepayment__expected_invoice_payment__lte = datetime.now().date()).values(supplier_currency = F('currency__currency_iso')).annotate(invoice_total_amount = Sum('total_from_invoice_amount')),
 
                "this_month_supplier_invoice_due" : supplier_invoiced_data.filter(invoice_status = '4',supplierinvoicepayment__expected_invoice_payment__lte = datetime.now().date(),invoice_date__month = datetime.now().month).values(supplier_currency = F('currency__currency_iso')).annotate(invoice_total_amount = Sum('total_from_invoice_amount')),
 
            }
            return Response(invoice_dict, status=status.HTTP_200_OK)
        except:
             return Response({"message":"Something want wrong"}, status=status.HTTP_400_BAD_REQUEST)


class ClientStats(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            respdata = RespondentDetail.objects.filter(
                end_time_day__year = datetime.now().year,url_type='Live').values(
                    customer_name = F('respondentdetailsrelationalfield__project__project_customer__cust_org_name')).annotate(
                        revenue=Coalesce(
                            Sum('project_group_cpi', filter=Q(resp_status__in=['4','9'])), 0.0), 
                        expense=Coalesce(
                            Sum('supplier_cpi', filter=Q(resp_status='4'), ), 0.0), 
                        margin=Case(
                            When(Q(revenue=0.0)|Q(revenue=None),then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))),
                            default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'),output_field=models.DecimalField(max_digits=7,decimal_places=2)),
                        ), 
                        completes = Count('id', filter=Q(resp_status = 4)),
                    ).exclude(revenue=0).order_by('-revenue','-margin')
            return Response(respdata, status=status.HTTP_200_OK)
        except:
            return Response({"message":"Something want wrong"}, status=status.HTTP_400_BAD_REQUEST)
        
class SupplierStats(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            respdata = RespondentDetail.objects.filter(
                end_time_day__year = datetime.now().year,url_type='Live').values(
                    supplier_name = F('respondentdetailsrelationalfield__source__supplier_name')).annotate(
                        revenue=Coalesce(
                            Sum('project_group_cpi', filter=Q(resp_status__in=['4','9'])), 0.0), 
                        expense=Coalesce(
                            Sum('supplier_cpi', filter=Q(resp_status='4'), ), 0.0), 
                        margin=Case(
                            When(Q(revenue=0.0)|Q(revenue=None),then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))),
                            default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'),output_field=models.DecimalField(max_digits=7,decimal_places=2)),
                        ), 
                        completes = Count('id', filter=Q(resp_status = 4)),
                    ).exclude(revenue=0).order_by('-revenue','-margin')
            return Response(respdata, status=status.HTTP_200_OK)
        except:
            return Response({"message":"Something want wrong"}, status=status.HTTP_400_BAD_REQUEST)

class ProjectManagerStats(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            respdata = RespondentDetail.objects.filter(
                end_time_day__year = datetime.now().year,url_type='Live').values(
                    pmid = F('respondentdetailsrelationalfield__project__project_manager')).annotate(
                        first_name = F('respondentdetailsrelationalfield__project__project_manager__first_name'),
                        last_name = F('respondentdetailsrelationalfield__project__project_manager__last_name'),
                        revenue=Coalesce(
                            Sum('project_group_cpi', filter=Q(resp_status__in=['4','9'])), 0.0), 
                        expense=Coalesce(
                            Sum('supplier_cpi', filter=Q(resp_status='4'), ), 0.0), 
                        margin=Case(
                            When(Q(revenue=0.0)|Q(revenue=None),then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))),
                            default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'),output_field=models.DecimalField(max_digits=7,decimal_places=2)),
                        ), 
                        completes = Count('id', filter=Q(resp_status = 4)),
                    ).exclude(revenue=0).order_by('-revenue','-margin')
            return Response(respdata, status=status.HTTP_200_OK)
        except:
            return Response({"message":"Something want wrong"}, status=status.HTTP_400_BAD_REQUEST)
        
class UserDailyVisits(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            today = timezone.now().date()
            seven_days_ago = today - timedelta(days=7)
            respdata = RespondentDetail.objects.filter(
                end_time_day__gte=seven_days_ago,end_time_day__lte=today).values(
                    date = F('end_time_day')).annotate(
                        visit = Count('id'),
                        incomplete = Count('id', filter=Q(resp_status = '3')),
                        completes = Count('id', filter=Q(resp_status = '4')),
                        terminate = Count('id', filter=Q(resp_status__in = ['5','2','7'])),
                    ).order_by('date')
            return Response(respdata, status=status.HTTP_200_OK)
        except:
            return Response({"message":"Something want wrong"}, status=status.HTTP_400_BAD_REQUEST)

class ProjectManagersWorkLoad(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            if 'date' in request.GET:
                liveprojectscount = Bid.objects.filter(bid_won_date = request.GET.get('date')).values(
                    pmid = F('project_manager__id'),
                    first_name = F('project_manager__first_name'),
                    last_name = F('project_manager__last_name'),
                ).annotate(
                    count = Count('id')
                ).exclude(count=0).order_by('-count')
            else:
                liveprojectscount = Project.objects.filter(
                    project_status = 'Live').values(
                        pmid = F('project_manager')).annotate(
                            first_name = F('project_manager__first_name'),
                            last_name = F('project_manager__last_name'),
                            count = Count('id',filter=Q(project_status = 'Live'))
                    ).exclude(count=0).order_by('-count')
            return Response(liveprojectscount, status=status.HTTP_200_OK)
        except:
            return Response({"message":"Something want wrong"}, status=status.HTTP_400_BAD_REQUEST)
        
class APIClientStats(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            projects = Project.objects.filter(
                project_status = 'Live',
                created_at__date__month = datetime.now().month,
                created_at__date__year = datetime.now().year,
                project_customer__customer_url_code__in = ['toluna','zamplia','sago']).values(
                    cust_name = F('project_customer__cust_org_name')).annotate(
                        visit = Count('respondentdetailsrelationalfield__respondent'),
                        incomplete = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status = '3')),
                        completes = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status = '4')),
                        terminate = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in = ['5','2','7'])),
                )
            return Response(projects, status=status.HTTP_200_OK)
        except:
            return Response({"message":"Something want wrong"}, status=status.HTTP_400_BAD_REQUEST)


class SalesOverviewGraph(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            now = timezone.now()
            one_year_ago = now - timedelta(days=365)
            Invoicedata = Invoice.objects.filter(
                invoice_date__gte = one_year_ago).values(
                    'invoice_date__month','invoice_date__year','invoice_currency'
                ).annotate(
                    totalsum = F('invoice_total_amount'),
                ).order_by('invoice_date')
            total_INR_invoiced_data = {}
            total_USD_invoiced_data = {}
            total_GBP_invoiced_data = {}

            for i in Invoicedata:
                monthyear = str(i['invoice_date__month'])+'-'+str(i['invoice_date__year'])
                if i['invoice_currency'] in [62,'62']:
                    total_INR_invoiced_data[monthyear] = i['totalsum'] + total_INR_invoiced_data[monthyear] if monthyear in total_INR_invoiced_data.keys() else i['totalsum']
                elif i['invoice_currency'] in [156,'156']:
                    total_USD_invoiced_data[monthyear] = i['totalsum'] + total_USD_invoiced_data[monthyear] if monthyear in total_USD_invoiced_data.keys() else i['totalsum']
                elif i['invoice_currency'] in [112,'112']:
                    total_GBP_invoiced_data[monthyear] = i['totalsum'] + total_GBP_invoiced_data[monthyear] if monthyear in total_GBP_invoiced_data.keys() else i['totalsum']
            return Response({"INR":total_INR_invoiced_data,"USD":total_USD_invoiced_data,"GBP":total_GBP_invoiced_data}, status=status.HTTP_200_OK)
        except:
            return Response({"message":"Something want wrong"}, status=status.HTTP_400_BAD_REQUEST)


class CountryWiseTotalSurveysLive(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            countrywisesurveycount = ProjectGroup.objects.filter(
                project_group_status = 'Live',
            ).values(
                country_name = F('project_group_country__country_name')
            ).annotate(
                count = Count('id')
            ).order_by('-count')
            return Response(countrywisesurveycount, status=status.HTTP_200_OK)
        except:
            return Response({"message":"Something want wrong"}, status=status.HTTP_400_BAD_REQUEST)