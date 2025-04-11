# ************** Django libraries *************
from django.db.models import *
from django.db.models.functions import Coalesce

# ************** rest-framework libraries *************
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

# ************** knox libraries *************
from knox.auth import TokenAuthentication

# ************** in-project imports *************
from Project.models import *
from Report_section.serializers import *
from employee.models import *
from Surveyentry.models import *
from Report_section.serializers import *
from Invoice.models import Invoice
from SupplierInvoice.models import *

# ************** third-party libraries *************
from datetime import datetime, date


class ProjectManagerProjectList(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PMworkloadSerializer

    def get(self, request, *args, **kwargs):
        employee_list = EmployeeProfile.objects.exclude(is_superuser = True, user_type = '1').exclude(emp_type = '10')
        project_revenue_month = request.GET.get('month',list(range(1,13)))
        project_revenue_year = request.GET.get('year',None)

        resp_details_obj = RespondentDetail.objects.filter(url_type='Live', resp_status = 4).values('project_number').annotate(projectcounts = Count('project_number'))
        
        projectList = Project.objects.select_related().filter(project_revenue_month__in = project_revenue_month)
        if project_revenue_year:
            projectList = projectList.filter(project_revenue_year = project_revenue_year)
        
        serializers = self.serializer_class(employee_list,context={'projectList':projectList,'querystring':request.GET}, many=True)
        return Response(serializers.data, status = status.HTTP_200_OK)


class ProjectManagerSalesProjectList(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PMSalesworkloadSerializer

    def get(self, request, *args, **kwargs):
        employee_list = EmployeeProfile.objects.filter(user_type = '1').exclude(is_superuser = True).exclude(emp_type = '10')
        project_revenue_month = request.GET.get('month',list(range(1,13)))
        project_revenue_year = request.GET.get('year',None)

        resp_details_obj = RespondentDetail.objects.filter(url_type='Live', resp_status = 4).values('project_number').annotate(projectcounts = Count('project_number'))
        
        projectList = Project.objects.select_related().filter(project_revenue_month__in = project_revenue_month)
        if project_revenue_year:
            projectList = projectList.filter(project_revenue_year = project_revenue_year)
        
        serializers = self.serializer_class(employee_list,context={'projectList':projectList,'querystring':request.GET}, many=True)
        return Response(serializers.data, status = status.HTTP_200_OK)


class CustomerReportingView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomerReportingSerializer

    def get(self, request, customer_id):
        # respondentdetails_obj = RespondentDetail.objects.
        project_list = Project.objects.filter(project_status = 'Live',project_customer__id = customer_id)
        serializer = self.serializer_class(project_list, many=True)
        return Response (serializer.data, status=status.HTTP_200_OK)

class ProjectstWithRevenueExpenseSupplier(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        project_list = Project.objects.filter(project_status = 'Live')
        serializer = self.serializer_class(project_list, many=True)
        return Response (serializer.data, status=status.HTTP_200_OK)

class CustomerReportwithDate(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        customer_id = request.data.get('customer_id', None)
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)
        if start_date and end_date:
            converted_start_date = datetime.strptime(start_date, "%d-%m-%Y").date()
            converted_end_date = datetime.strptime(end_date, "%d-%m-%Y").date()

            resp_relationsfield_obj = RespondentDetailsRelationalfield.objects.select_related('respondent').values(
                project_number = F('project__project_number'),
                customer_name=F('project__project_customer__cust_org_name'),
            ).filter(
                respondent__resp_status__in=[4,8,9], 
                respondent__url_type='Live', 
                respondent__end_time__date__range = [converted_start_date, converted_end_date]
            ).distinct().annotate(
                total_collected_completes = Count('source', filter=Q(respondent__resp_status__in=[4,8,9])), 
                accepted_completes = Count('source', filter=Q(respondent__resp_status__in=[4,9])), 
                rejected_completes = Count('source', filter=Q(respondent__resp_status__in=[8])), 
                revenue = Sum('respondent__project_group_cpi', filter=Q(respondent__resp_status__in=[4,9])), 
                expense = Sum('respondent__supplier_cpi', filter=Q(respondent__resp_status__in=[4]))
            )

            if customer_id not in ['', None]:
                resp_relationsfield_obj = resp_relationsfield_obj.filter(
                    project__project_customer__id = customer_id
                )
            
            return Response(list(resp_relationsfield_obj), status=status.HTTP_200_OK)
        return Response({'detail': 'start_date and end_date is required..!'}, status=status.HTTP_400_BAD_REQUEST)


class SupplierReportwithDate(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        supplier_id = request.data.get('supplier_id', None)
        start_date = request.data.get('start_date', None)
        end_date = request.data.get('end_date', None)
        project_no = request.data.get('project_no', None)
        converted_start_date = None
        converted_end_date = None


        if start_date and end_date:
            converted_start_date = datetime.strptime(start_date, "%d-%m-%Y").date()
            converted_end_date = datetime.strptime(end_date, "%d-%m-%Y").date()

        resp_relationsfield_obj = RespondentDetailsRelationalfield.objects.select_related('respondent').values(
            project_number = F('project__project_number'), 
            supplier_name = F('source__supplier_name'),
        ).filter(
            Q(respondent__end_time__date__range = [converted_start_date, converted_end_date]) if converted_start_date and converted_end_date else Q(),
            respondent__resp_status__in=[4,8,9],
            respondent__url_type='Live', 
        ).distinct().annotate(
            total_collected_completes = Count('source', filter=Q(respondent__resp_status__in=[4,8,9])), 
            accepted_completes = Count('source', filter=Q(respondent__resp_status__in=[4,9])), 
            rejected_completes = Count('source', filter=Q(respondent__resp_status__in=[8])), 
            revenue = Sum('respondent__project_group_cpi', filter=Q(respondent__resp_status__in=[4,9])), 
            expense = Sum('respondent__supplier_cpi', filter=Q(respondent__resp_status__in=[4]))
        )

        if supplier_id in ['', None]:
            return Response({"error":"Please select supplier..!"}, status=status.HTTP_400_BAD_REQUEST)
        
        if start_date in ['', None] or end_date in ['', None]:
            if project_no not in ['', None]:
                resp_relationsfield_obj = resp_relationsfield_obj.filter(source__id=supplier_id,project__project_number = project_no)
                return Response(list(resp_relationsfield_obj), status=status.HTTP_200_OK)
            else:
                return Response({"error":"Please select start date and end date or project number..!"}, status=status.HTTP_400_BAD_REQUEST) 
        
        if supplier_id and start_date and end_date:
            resp_relationsfield_obj = resp_relationsfield_obj.filter(source__id=supplier_id)
        
        return Response(list(resp_relationsfield_obj), status=status.HTTP_200_OK)


class SupplierFinalidsbyDate(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        supplier_id = request.GET.get('supplier_id', None)
        start_date = request.GET.get('start_date', None)
        end_date = request.GET.get('end_date', None)

        if supplier_id and start_date and end_date:
            converted_start_date = datetime.strptime(start_date, "%d-%m-%Y").date()
            converted_end_date = datetime.strptime(end_date, "%d-%m-%Y").date()

            finalidslist = RespondentURLDetail.objects.filter(respondent__end_time__date__range = [converted_start_date, converted_end_date],respondent__source__in = supplier_id.split(',')).select_related('respondent').values(project_number = F('respondent__project_number'), survey_number = F('respondent__project_group_number'), client_cpi = F('respondent__project_group_cpi'), supplier_cpi = F('respondent__supplier_cpi'), resp_status = F('respondent__resp_status'), start_time = F('respondent__start_time'),supplier_name = F('respondent__respondentdetailsrelationalfield__source__supplier_name'))
            
            return Response(list(finalidslist), status=status.HTTP_200_OK)
        return Response({'detail': 'supplier_id, start_date and end_date is required..!'}, status=status.HTTP_400_BAD_REQUEST)



class SupplierRevenuePerMonth(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        revenue_month = request.GET.get('month',list(range(1,13)))
        revenue_year = request.GET.get('year','')
        due_month = request.GET.get('due_month', list(range(1,13)))
        due_year = request.GET.get('due_year', '')

        if revenue_year in ['', None] and due_year in ['', None]:
            return Response({'error': 'Year is required..!'}, status=status.HTTP_400_BAD_REQUEST)
        
        if revenue_year not in ['', None]:
            if not isinstance(revenue_month, list):
                revenue_month = revenue_month.split(',')
            supp_invoice_obj = SupplierInvoice.objects.filter(invoice_date__month__in=revenue_month, invoice_date__year__in = revenue_year.split(',')).values(supplier_name=F('supplier_org__supplier_name'), currency_name=F('currency__currency_iso')).annotate(Sum('total_invoice_amount'))
        else:
            if not isinstance(due_month, list):
                due_month = due_month.split(',')
            supp_invoice_obj = SupplierInvoice.objects.filter(due_date__month__in=due_month, due_date__year__in = due_year.split(',')).values(supplier_name=F('supplier_org__supplier_name'), currency_name=F('currency__currency_iso')).annotate(Sum('total_invoice_amount'))
            
        return Response(supp_invoice_obj, status=status.HTTP_200_OK)



class ClientwiseInvoicingRevenuePerMonth(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        revenue_month = request.GET.get('month',list(range(1,13)))
        revenue_year = request.GET.get('year','')
        due_month = request.GET.get('due_month', list(range(1,13)))
        due_year = request.GET.get('due_year', '')

        if revenue_year in ['', None] and due_year in ['', None]:
            return Response({'error': 'Year is required..!'}, status=status.HTTP_400_BAD_REQUEST)

        if revenue_year not in ['', None]:
            if not isinstance(revenue_month, list):
                revenue_month = revenue_month.split(',')
            invoice_obj = Invoice.objects.filter(invoice_date__month__in=revenue_month, invoice_date__year = revenue_year)
        else:
            if not isinstance(due_month, list):
                due_month = due_month.split(',')
            invoice_obj = Invoice.objects.filter(invoice_due_date__month__in=due_month, invoice_due_date__year = due_year)

        invoice_dtl = invoice_obj.values(customer = F('invoice_customer__cust_org_name'), currency=F('invoice_currency__currency_iso')).annotate(
            invoice_total_amount=Coalesce(Sum('invoice_total_amount'), Value(0.0))
        ).order_by()
        
        invoice_currency_dtl = invoice_obj.values(currency=F('invoice_currency__currency_iso')).annotate(
            total_amount=Coalesce(Sum('invoice_total_amount'), Value(0.0))
        ).order_by()
        return Response({'invoice_details':invoice_dtl,'total_amounts': invoice_currency_dtl}, status=status.HTTP_200_OK)



class ClientwiseLockedPendingRevenuePerMonth(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        revenue_month = request.GET.get('month',date.today().month)
        revenue_year = request.GET.get('year', date.today().year)
        
        client_revenue_dtl = RespondentDetailsRelationalfield.objects.filter(respondent__resp_status__in = [4,9], project__project_revenue_month=revenue_month, project__project_revenue_year=revenue_year).values(customer=F('project__project_customer__cust_org_name')).annotate(
            locked_revenue = Coalesce(
                Sum("respondent__project_group_cpi", filter=Q(project__project_status__in=['Reconciled', 'Invoiced'])), Value(0),output_field=FloatField()
                ),
            pending_revenue = Coalesce(
                Sum("respondent__project_group_cpi", filter=Q(project__project_status__in=['Live', 'Paused', 'Closed'])), Value(0),output_field=FloatField()
                ),
            ).order_by()

        return Response(client_revenue_dtl, status=status.HTTP_200_OK)
