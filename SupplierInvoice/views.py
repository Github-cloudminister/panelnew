# ********* Django Libraries **********
from django.http import HttpResponse
from django.db.models import *
from datetime import date
from django.views.generic import TemplateView
from django.conf import settings

# ********* REST API Libraries **********
from rest_framework import status
from rest_framework.generics import ListCreateAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from Invoice.models import Invoice, InvoiceRow

# ********* in-project imports **********
from SupplierInvoice.serializers import *
from Surveyentry.custom_function import get_object_or_none

# ********* third-party libraries **********
import xlsxwriter
from io import BytesIO
from django.template.loader import render_to_string
from automated_email_notifications.email_configurations import sendEmailSendgripAPIIntegration


# Create your views here.
class Round(Transform):
    function = 'ROUND'
    arity = 2


class SupplierInvoiceAmountByDateListView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        queryset = SupplierInvoice.objects.filter(due_date__lte=end_date, due_date__gte=start_date).values('supplier_org__supplier_name').annotate(accrued_amount=Cast(Sum('total_invoice_amount'), output_field=models.DecimalField(max_digits=7, decimal_places=2)))
        return Response(queryset, status=status.HTTP_200_OK)


class SupplierInvoiceListView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = SupplierInvoiceListSerializer

    def get_queryset(self):
        queryset = SupplierInvoice.objects.all()
        supplier_org = self.request.GET.get('supplier_id').split(',') if self.request.GET.get('supplier_id') else []
        start_date = self.request.GET.get('start_date','')
        end_date = self.request.GET.get('end_date','')
        exp_date = self.request.GET.get('exp_date','')
        invoice_status = self.request.GET.get('invoice_status').split(",")

        if self.request.GET.get('od') == '2':
            queryset = queryset.filter(created_from = '2')
        if self.request.GET.get('od') == '1':
            queryset = queryset.filter(created_from = '1')
        if supplier_org:
            queryset = queryset.filter(supplier_org__id__in=supplier_org)
        if start_date:
            queryset = queryset.filter(invoice_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(invoice_date__lte=end_date)
        if invoice_status:
            queryset = queryset.filter(invoice_status__in = invoice_status)
        if exp_date:
            queryset = queryset.filter(supplierinvoicepayment__expected_invoice_payment__lte = exp_date)
        return queryset.order_by('-invoice_date')



class SupplierInvoiceBulkUpdateView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)


    def post(self, request, supplierOrg_id):
        data = request.data
        invoice_number = data.get('invoice_number')
        invoice_date = data.get('invoice_date')
        due_date = data.get('invoice_due_date')
        conversion_rate = data.get('conversion_rate')
        total_invoice_amount = data.get('invoice_total_amount')
        total_from_invoice_amount = data.get('total_from_invoice_amount')
        currency_id = data.get('currency_id')
        company_id = data.get('company_id')
        already_generated_invoices = []

        supplierOrg_obj = get_object_or_none(SupplierOrganisation, id=supplierOrg_id)
        company_detail_obj = get_object_or_none(CompanyDetails, id=company_id)
        supplier_inv_obj = SupplierInvoice.objects.create(invoice_number=invoice_number, invoice_date=invoice_date, due_date=due_date, conversion_rate=conversion_rate, total_invoice_amount=total_invoice_amount,total_from_invoice_amount = total_from_invoice_amount, currency_id=currency_id,supplier_org=supplierOrg_obj, company = company_detail_obj)

        if data.get('project') and invoice_number and invoice_date:
            for project in data.get('project'):
                suppinv_row_qs = SupplierInvoiceRow.objects.filter(id=project['suppinv_row_id'])
                if suppinv_row_qs:
                    if suppinv_row_qs.filter(invoice_received=True):
                        already_generated_invoices.append({'InvoiceRow ID': suppinv_row_qs[0].id, 'project_number':suppinv_row_qs[0].project.project_number, 'invoice_number':suppinv_row_qs[0].supplier_invoice.invoice_number})
                    else:
                        suppinv_row_qs.update(invoice_received=True, invoiced_completes=project['completes'], invoiced_cpi=project['cpi'], total_amount=project['total'], supplier_invoice=supplier_inv_obj)
                else:
                    SupplierInvoiceRow.objects.create(invoiced_completes=project['completes'], invoiced_cpi=project['cpi'], total_amount=project['total'], supplier_invoice=supplier_inv_obj, supplier_org=supplierOrg_obj)

            # This is not required now, we can remove this now
            if not supplier_inv_obj.supplierinvoicerow_set.all():
                SupplierInvoice.objects.filter(id=supplier_inv_obj.id).delete()

            return Response({'message':'Supplier\'s Invoices That were not Received Updated Successfully', 'Invoice Already Generated for that particular Project Number & Invoice Number and InvoiceRow ID':already_generated_invoices}, status=status.HTTP_200_OK)
        else:
            return Response({'message':'Please provide the parameters'}, status=status.HTTP_200_OK)



class SupplierInvoiceVerificationView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)


    def post(self, request, supplierOrg_id):
        data = request.data
        supp_inv_data = data.get('supplier_data')
        supp_data_list = []
        if supp_inv_data:
            for inv_obj in supp_inv_data:
                project_number = inv_obj['project_number'].strip()
                supplier_invrow_qs = SupplierInvoiceRow.objects.filter(supplier_org=supplierOrg_id, project__project_number=project_number, cpi=inv_obj['cpi'])
                if supplier_invrow_qs:
                    for supp_invrow_obj in supplier_invrow_qs:
                        inv_data_dict = {'supplierOrg_id':supplierOrg_id, 'project_number':project_number, 'cpi':inv_obj['cpi'], 'completes':inv_obj['completes'], 'suppinv_row_id':supp_invrow_obj.id, 'systemcpi':supp_invrow_obj.cpi, 'systemcompletes':supp_invrow_obj.completes, 'invoice_received':supp_invrow_obj.invoice_received,'data_verified':True}
                        supp_data_list.append(inv_data_dict)
                else:
                    inv_data_dict = {'supplierOrg_id':supplierOrg_id, 'project_number':project_number, 'cpi':inv_obj['cpi'], 'completes':inv_obj['completes'], 'suppinv_row_id':'-', 'systemcpi':0.0, 'systemcompletes':0, 'invoice_received':'-','data_verified':False}
                    supp_data_list.append(inv_data_dict)

            return Response(supp_data_list, status=status.HTTP_200_OK)

        return Response({'message':'Please provide the Supplier Data'}, status=status.HTTP_200_OK)



class SupplierInvoiceUpdateStatusView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)


    def post(self, request, invoiceid):

        try:
            gst_deductible = request.data.get('gst_deductible')
            tds_receivable = request.data.get('tds_receivable')
            total_payable_amount = request.data.get('payable_amount')
            expected_invoice_payment = request.data.get('expected_invoice_payment')
            obj , created = SupplierInvoicePayment.objects.update_or_create(
                supplier_invoice_id = int(invoiceid),
                defaults = {
                    'gst_deductible' : gst_deductible,
                    'tds_receivable' : tds_receivable,
                    'total_payable_amount' : total_payable_amount,
                    'expected_invoice_payment' : expected_invoice_payment
                    }
                )
            SupplierInvoice.objects.filter(id = invoiceid).update(
                invoice_status = '4'
            )
            if str(obj.supplier_invoice.invoice_date) > settings.SUPPLIER_INVOICE_DEPLOYE_DATE:
                cc_emails = 'accounts@panelviewpoint.com' if settings.SERVER_TYPE == 'production' else 'tech@panelviewpoint.com'
                suppliercontactemails = list(SupplierContact.objects.filter(supplier_id = obj.supplier_invoice.supplier_org).values_list('supplier_email',flat=True))
                
                htmldata = {
                    'invoice_number' : obj.supplier_invoice.invoice_number,
                    'invoice_date'  : obj.supplier_invoice.invoice_date,
                    'invoice_due_date'  : obj.supplier_invoice.due_date,
                    'expected_payment_date'  : obj.expected_invoice_payment,
                    'total_payable_amount'  : obj.total_payable_amount
                }
                html_message = render_to_string('Supplier/supplier_invoice_approved.html',htmldata)
                subject = f'Invoice {obj.supplier_invoice.invoice_number} has been Approved for Payment'

                sendEmailSendgripAPIIntegration(
                    to_emails = suppliercontactemails,
                    cc_emails = cc_emails,
                    subject = subject,
                    html_message= html_message
                )
            return Response({'message':'Invoice Payment Details Updated..!'}, status=status.HTTP_200_OK)
        except:
            return Response({'error':'Invoice Payment Details Not Updated'}, status=status.HTTP_400_BAD_REQUEST)


class SupplierInvoiceRetrieveUpdateView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def get(self,request,invoiceid):

        try:
            queryset = SupplierInvoice.objects.get(id = invoiceid)
            serializer = SupplierInvoiceRetrieveUpdateSerializer(queryset)
            
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response({'message':'No data found for Supplier Invoice'}, status=status.HTTP_200_OK)



class ListSupplierInvoiceRowAPI(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = SupplierInvoiceRowListSerializer


    def get_queryset(self):
        supplier_invrow_qs = SupplierInvoiceRow.objects.all()
        if self.request.GET.get('project_id'):
            supplier_invrow_qs = supplier_invrow_qs.filter(project=self.request.GET['project_id'])
        if self.request.GET.get('supplier_org_id'):
            supplier_invrow_qs = supplier_invrow_qs.filter(supplier_org=self.request.GET['supplier_org_id'])
        return supplier_invrow_qs


class SupplierInvoiceRowCreateUpdateAPI(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)


    def post(self, request):
        supplier_invrow_data = request.data.get('supplier_invrows')
        for supp_invrow_dict in supplier_invrow_data:
            supplier_invrow_obj = SupplierInvoiceRow.objects.filter(id=supp_invrow_dict['supp_invrow_id'])
            if supplier_invrow_obj:
                supplier_invrow_obj.update(cpi=supp_invrow_dict['system_cpi'],completes=supp_invrow_dict['system_completes'])
            else:
                SupplierInvoiceRow.objects.create(supplier_org_id=supp_invrow_dict['supplier_org_id'],project_id=supp_invrow_dict['project_id'],cpi=supp_invrow_dict['system_cpi'],completes=supp_invrow_dict['system_completes'])
        
        return Response({'message':'Supplier Invoice Rows Created/Updated Successfully'}, status=status.HTTP_201_CREATED) 


class SupplierInvoiceRowsXLSXDownload(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def get(self, request):
        output = BytesIO()
        invoice_number = request.GET.get('invoice_numbers')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        supplier_org_ids = request.GET.get('supplier_id')

        if invoice_number and start_date and end_date:
            invoice_number_list = invoice_number.split(',')
            supplier_invoice_row_qs = SupplierInvoiceRow.objects.select_related('supplier_invoice','supplier_invoice__supplier_org','supplier_invoice__currency').filter(supplier_invoice__invoice_number__in=invoice_number_list, supplier_invoice__invoice_date__gte=start_date, supplier_invoice__invoice_date__lte=end_date).order_by('supplier_invoice','id')
        elif not invoice_number and start_date and end_date:
            supplier_invoice_row_qs = SupplierInvoiceRow.objects.select_related('supplier_invoice','supplier_invoice__supplier_org','supplier_invoice__currency').filter( supplier_invoice__invoice_date__gte=start_date, supplier_invoice__invoice_date__lte=end_date).order_by('supplier_invoice','id')
        else:
            return Response({'message': 'Please provide a Start Date & an End Date'}, status=status.HTTP_400_BAD_REQUEST)

        if not supplier_invoice_row_qs:
            return Response({'message': 'No Invoices exist for the given Invoice Numbers'}, status=status.HTTP_400_BAD_REQUEST)

        if supplier_org_ids:
            supplier_org_ids = supplier_org_ids.split(',')
            supplier_invoice_row_qs = supplier_invoice_row_qs.filter(supplier_invoice__supplier_org_id__in=supplier_org_ids)

        if not supplier_invoice_row_qs:
            return Response({'message': 'No Invoices exist for the given Suppliers'}, status=status.HTTP_400_BAD_REQUEST)
            
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Supplier Invoice')
        column_incr = 0
        head_columns = ['Invoice No','Invoice date','Party Name','State','Party GST','Item Name','Unit','HSN No','GST Per','Sales Ledger','Qty','Rate','Conversion Rate','Converted CPI','Taxable CPI','Tax CPI','Item Amount','Taxable Amount','Tax Amount','Currency']
        cell_format = workbook.add_format({'bold': True, 'bg_color': 'yellow'})
        for _ , column in zip(range(20), head_columns):
            worksheet.set_column(column_incr, column_incr, len(column)+2)
            worksheet.write(0, column_incr, column, cell_format)
            column_incr+=1
        worksheet.set_column(5, 5, 25)
        worksheet.set_column(0, 0, 20)
        worksheet.set_column(2, 2, 15)
        worksheet.set_column(6, 6, 15)

        data_row_incr = 1
        #Looping through Rows
        for supp_invrow_obj in supplier_invoice_row_qs:
            try:
                project_number = supp_invrow_obj.project.project_number
            except:
                project_number = 'N/A'
            taxable_amount = round(supp_invrow_obj.total_amount/1.18, 2)
            tax_amount = supp_invrow_obj.total_amount - taxable_amount
            converted_cpi = supp_invrow_obj.invoiced_cpi * supp_invrow_obj.supplier_invoice.conversion_rate
            taxable_cpi = round(converted_cpi/1.18, 2)
            tax_cpi = converted_cpi - taxable_cpi
            columns_data = [
                supp_invrow_obj.supplier_invoice.invoice_number,
                datetime.strftime(supp_invrow_obj.supplier_invoice.invoice_date, "%d-%m-%Y"),
                supp_invrow_obj.supplier_invoice.supplier_org.supplier_name,
                supp_invrow_obj.supplier_invoice.supplier_org.supplier_state,
                supp_invrow_obj.supplier_invoice.supplier_org.supplier_TAX_id,
                project_number,
                'Completes',
                '998371',
                '18',
                'Sales GST',
                supp_invrow_obj.invoiced_completes,
                supp_invrow_obj.invoiced_cpi,
                supp_invrow_obj.supplier_invoice.conversion_rate,
                converted_cpi,
                taxable_cpi,
                tax_cpi,
                supp_invrow_obj.total_amount,
                taxable_amount,
                tax_amount,
                supp_invrow_obj.supplier_invoice.currency.currency_iso
            ]
            data_column_incr = 0
            #Looping through Columns in those Rows
            for _ , column in zip(range(20), columns_data):
                worksheet.write(data_row_incr, data_column_incr, column)
                data_column_incr+=1
            data_row_incr+=1

        workbook.close()

        response = HttpResponse(output.getvalue(), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=AdvancedSales.xlsx'
        return response



class ClientWiseReceivablesView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request,supplier_id,*args,**kwargs):
        today_month = date.today()

        supplier_receivable = SupplierInvoice.objects.filter(invoice_date__lte=today_month,invoice_status="1",supplier_org__id=supplier_id).values("id","supplier_org","invoice_date","total_invoice_amount","total_from_invoice_amount")

        return Response({"client receivable amount":supplier_receivable}, status=status.HTTP_200_OK)
    

class SupplierWisePayablesView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request,supplier_id,*args,**kwargs):
        today_month = date.today().strftime("%Y")

        supplier_payables = SupplierInvoice.objects.filter(invoice_date__year__lte=today_month,invoice_status="2",supplier_org__id=supplier_id).values("id","supplier_org","invoice_date","total_invoice_amount","total_from_invoice_amount")

        return Response({"supplier payables amount":supplier_payables}, status=status.HTTP_200_OK)
    


class SupplierInvoiceRowDataProjectSupplierWise(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        supplier_id = self.request.GET.get('supplier_id')
        project_no = self.request.GET.get('project_no')

        supplier_invoice_row_data = SupplierInvoiceRow.objects.filter(supplier_org = supplier_id, project__project_number = project_no).values('id',
            supplier_name = F('supplier_org__supplier_name'),
            project_number = F('project__project_number'),
            complete = F('completes'),
            cpis = F('cpi'),
            supplier_invoice_number = F('supplier_invoice__invoice_number'),
            invoice_receiveds = F('invoice_received')
            )
        
        return Response({"supplier_invoice_row_data":supplier_invoice_row_data}, status=status.HTTP_200_OK)
    


class SupplierInvoiceNullRowUpdateApi(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        supplier_invoice_row_update = SupplierInvoiceRow.objects.filter(supplier_invoice = None).update(invoice_received = False,invoiced_completes = 0,invoiced_cpi = 0)

        return Response({"message":"Supplier Invoice Row Update Successfully.!"}, status=status.HTTP_200_OK)


class PaymentReminderHTMlView(TemplateView):
    template_name = "Invoice/invoice_payment_reminder_email.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today_date = datetime.now().date()
        client_contact_qs = ClientContact.objects.filter(id__in=["1"])
        client_emails = client_contact_qs.values_list('client_email',flat=True)
        invoice_qs = Invoice.objects.filter(id__in=["25"]).annotate(due_days=datetime.now().date() - F('invoice_due_date'))
        sum_invoice_row_amount = Invoice.objects.filter(id__in=invoice_qs).aggregate(Sum('invoice_total_amount'))
        invoice_row_qs = InvoiceRow.objects.filter(invoice__in = invoice_qs).annotate(due_days=datetime.now().date() - F('invoice__invoice_due_date'))

        context['invoice_row_qs'] = invoice_row_qs
        context['sum_invoice_row_amount'] = sum_invoice_row_amount
        context['today_date'] = today_date

        return context

class InvoicefieldStatusChange(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self,request):
        try:
            data = request.data
            invoiceobj = SupplierInvoice.objects.get(id = data['invoiceid'])
            if invoiceobj.invoice_status == '4':
                return Response({"error":"Invoice Row Already Approved"}, status=status.HTTP_400_BAD_REQUEST)
            if data['invoicefieldsstatus'] != '4':
                invoiceobj.invoice_status = data['invoicefieldsstatus']
            invoiceobj.clarification = data['clarification']
            invoiceobj.save()
            suppliercontactemails = list(SupplierContact.objects.filter(supplier_id = invoiceobj.supplier_org).values_list('supplier_email',flat=True))
            if data['invoicefieldsstatus'] == '5' and str(invoiceobj.invoice_date) > settings.SUPPLIER_INVOICE_DEPLOYE_DATE:
                if settings.SERVER_TYPE == 'production':
                    cc_emails = 'accounts@panelviewpoint.com' 
                    redirect = f'{settings.SUPPLIER_DASHBOARD_FRONTEND_URL}#/invoice'
                
                else:
                    cc_emails = 'tech@panelviewpoint.com'
                    redirect = f'{settings.SUPPLIER_DASHBOARD_FRONTEND_URL}#/invoice'
    
                htmldata = {
                    'redirect' : redirect
                }
                html_message = render_to_string('Supplier/supplier_invoice_clarification_email.html',htmldata)
                subject = f'Discrepancy in the Invoice-{invoiceobj.invoice_number}'

                email_response = sendEmailSendgripAPIIntegration(
                    to_emails = suppliercontactemails,
                    cc_emails = cc_emails,
                    subject = subject,
                    html_message= html_message
                )
            return Response({"invoicedatastatus":data['invoicefieldsstatus'],"message" : data['clarification']}, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Invoice Details/Status Not Approved"}, status=status.HTTP_400_BAD_REQUEST)

class SupplierInvoicePaidMarkView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def put(self,request):
        data = request.data
        paid_date = request.data.get('paid_date')
        SupplierInvoicePayment.objects.filter(supplier_invoice_id__in = data['invoiceid']).update(date_invoice_paid = paid_date)
        SupplierInvoice.objects.filter(
            id__in = data['invoiceid'],invoice_status = '4').update(invoice_status = '2')
        return Response({"message":"Status Updated Successfully"}, status=status.HTTP_200_OK)


class InvoicePyamentDetailsView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request,invoiceid):
        invoicepaymentdetails = SupplierInvoicePayment.objects.filter(supplier_invoice_id = invoiceid).values('gst_deductible','tds_receivable','total_payable_amount','expected_invoice_payment')
        return Response(invoicepaymentdetails, status=status.HTTP_200_OK)
    


class SupplierInvoiceDeleteAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data = request.data

        supplier_invoice_id = data.get('supplier_invoice_id')

        try:
            if supplier_invoice_id in ['', None]:
                return Response({"error":"Supplier invoice id field Required.!"}, status=status.HTTP_400_BAD_REQUEST)
            supplier_invoice_obj = SupplierInvoice.objects.get(id = supplier_invoice_id)
            
            supplier_invoice_row_obj = SupplierInvoiceRow.objects.filter(supplier_invoice = supplier_invoice_obj)

            supplier_invoice_row_obj.update(invoiced_completes = None, invoiced_cpi = None, total_amount = None, invoice_received = False, supplier_invoice = None)
            supplier_invoice_obj.delete()

            return Response({"message":"Supplier Invoice Delete Successfully..!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message":f"Something went wrong--{e}"}, status=status.HTTP_200_OK)
    



