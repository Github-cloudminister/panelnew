# django imports
from django.http import HttpResponse
from django.db.models import Sum, Count, Q, Avg, F
from django.conf import settings
from django.template.loader import get_template
from django.views.generic import TemplateView
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from PyPDF3 import PdfFileMerger 
# rest_framework imports
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveDestroyAPIView
from Invoice.filters import DraftInvoiceFilterSet, DraftInvoiceRowFilterSet
# in-invoice imports
from Invoice.models import *
from Invoice.serializers import *
from Logapp.models import InvoiceExceptionsLog
from Logapp.views import draft_invoice_log, invoice_log
from Notifications.models import EmployeeNotifications
from Project.models import *
from Supplier_Final_Ids_Email.models import SupplierIdsMarks
from Surveyentry.custom_function import get_object_or_none
from Surveyentry.models import *
from Invoice.permissions import *
from CompanyBankDetails.models import *

# automated email notifications imports
from automated_email_notifications.email_configurations import *

# third_party module imports
from knox.auth import TokenAuthentication
from xhtml2pdf import pisa
from os import stat
import os, csv
import base64
import xlsxwriter
from io import BytesIO
import asyncio
from datetime import date, datetime

# Sendgrid library
from sendgrid.helpers.mail import Attachment, FileContent, FileName, FileType, Disposition

from automated_email_notifications.project_custom_functions import update_status


def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access those
    resources
    """
    result = finders.find(uri)
    if result:
            if not isinstance(result, (list, tuple)):
                    result = [result]
            result = list(os.path.realpath(path) for path in result)
            path=result[0]
    else:
            sUrl = settings.STATIC_URL        # Typically /static/
            sRoot = settings.STATIC_ROOT      # Typically /home/userX/project_static/
            mUrl = settings.MEDIA_URL         # Typically /media/
            mRoot = settings.MEDIA_ROOT       # Typically /home/userX/project_static/media/

            if uri.startswith(mUrl):
                    path = os.path.join(mRoot, uri.replace(mUrl, ""))
            elif uri.startswith(sUrl):
                    path = os.path.join(sRoot, uri.replace(sUrl, ""))
            else:
                    return uri

    # make sure that file exists
    if not os.path.isfile(path):
            raise Exception(
                    'media URI must start with %s or %s' % (sUrl, mUrl)
            )
    return path

class InvoiceNumber(APIView):

    def newInvoiceNumber(self,request):

        customer_obj = CustomerOrganization.objects.get(id = request.GET.get('customer'))
        
        if customer_obj.company_invoice_bank_detail.company_details.company_local_currency.id == int(request.GET.get('currency')):

            invoice_new_no = customer_obj.company_invoice_bank_detail.company_details.company_invoice_suffix_local_currency
            company_prefix_local_currency = customer_obj.company_invoice_bank_detail.company_details.company_invoice_prefix_local_currency
            new_invoice_number = int(invoice_new_no)+1
            invoice_number = f"{company_prefix_local_currency}-{new_invoice_number}"
        else:
            
            invoice_new_no = customer_obj.company_invoice_bank_detail.company_details.company_invoice_suffix_international_currency
            company_prefix_international_currency = customer_obj.company_invoice_bank_detail.company_details.company_invoice_prefix_international_currency
            new_invoice_number = int(invoice_new_no)+1
            invoice_number = f"{company_prefix_international_currency}-{new_invoice_number}"

        return invoice_number
    
class InvoiceList(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = InvoiceListSerializer

    def get_queryset(self):
        invoice_status = self.request.query_params.get('invoice_status')
        invoice_customer = self.request.query_params.get('invoice_customer')
        invoice_currency = self.request.query_params.get('invoice_currency')
        invoice_company_details = self.request.query_params.get('company_detail')
        invoice_number = self.request.query_params.get('invoice_number')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        invoice_year = self.request.GET.get('year','')
        invoice_month = self.request.GET.get('month','')
        
        # year = datetime.now().year
        
        # if year in ['', None] or month in ['', None]:
        #     # return "year & month are required.!"
        #     return Response({"error":"year & month are required.!"}, status=status.HTTP_400_BAD_REQUEST)

        qs = Invoice.objects.select_related().all().order_by("-id")
        if invoice_status not in ['', None]:
            qs = qs.filter(invoice_status = invoice_status)
        if invoice_customer not in ['',None]:
            qs = qs.filter(invoice_customer = invoice_customer)
        if invoice_currency not in ['', None]:
            qs = qs.filter(invoice_currency = invoice_currency)
        if invoice_company_details not in ['',None]:
            qs = qs.filter(company_invoice_bank_detail__company_details__id = invoice_company_details)
        if invoice_number not in ['',None]:
            qs = qs.filter(invoice_number = invoice_number)
        if start_date not in ['',None]:
            qs = qs.filter(invoice_date__gte = start_date)
        if end_date not in ['',None]:
            qs = qs.filter(invoice_date__lte = end_date)

        if invoice_year not in ['', None]:
            qs = qs.filter(invoice_date__year = invoice_year)
        if invoice_month not in ['', None]:
            qs = qs.filter(invoice_date__month = invoice_month)
        
        return qs

    def get(self, request):
        invoicelist = self.get_queryset()
        serializer = self.serializer_class(invoicelist, many=True)
        return Response(serializer.data)


class CustomerOrganizationReconciledProjectView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomerOrganizationReconciledProjectSerializer

    def get(self, request, cust_org_id):
        projects = Project.objects.filter(project_status = "Reconciled", project_customer__id = cust_org_id)
        serializer = self.serializer_class(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectGroupInvoiceList(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ProjectGroupInvoiceSerializer

    def post(self, request):

        requested_data = dict(request.data)
        # resp_details_obj = RespondentDetail.objects.only('id','project_group_cpi').filter(project_number__in = requested_data['project_number'], resp_status__in=["4","9"], url_type = 'Live').values('project_number','project_group_number').annotate(
        #     project_group_completes = Count('id'),
        #     project_group_cpis = Sum('project_group_cpi')
        # )

        try:
            project_no = requested_data['project_number']
        except:
            project_no = []

        project_grp_obj = ProjectGroup.objects.filter(project__project_number__in = project_no).values(
            'project_group_name',
            'project_group_number',
            'project_group_cpi',
            project_number = F('project__project_number'),
            po_number = F('project__project_po_number')
        ).annotate(
            project_group_completes = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=["4","9"])),
            project_group_total_amount = Sum('respondentdetailsrelationalfield__respondent__project_group_cpi', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=["4","9"]))
        )
    
        return Response(project_grp_obj, status=status.HTTP_200_OK)
        # return Response([resp_details_obj], status=status.HTTP_200_OK)


class CreateInvoice(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = InvoiceSerializer

    def post(self, request):

        requested_data = dict(request.data)
        invoice_exists = Invoice.objects.filter(invoice_number = requested_data['invoice_number']).exists()
        if invoice_exists:
            return Response({'message': 'Invoice Number Already Exists New Invoice Number Updated'}, status= status.HTTP_208_ALREADY_REPORTED)
        
        if requested_data['invoice_show_conversion_rate'] == False:
            requested_data.pop('invoice_conversion_rate')
            requested_data.pop('invoice_total_amount_in_USD')

        try:
            project_groups = requested_data['project_groups']
        except:
            project_groups = []

        projectlist = requested_data['invoice_project']

        proj_obj = Project.objects.filter(project_number__in = projectlist).exclude(project_status="ReadyForInvoiceApproved").exists()
        if not proj_obj:
            if len(project_groups) > 0:

                if len(projectlist) <= 15:
                
                    serializer = self.serializer_class(data=requested_data)

                    if serializer.is_valid(raise_exception=True):
                        invoice_obj = serializer.save(created_by = request.user)
                        invoice_log(serializer.data,'',invoice_obj,None,request.user)
                        try:
                            # PROJECTS ADDED FOR MANY2MANY FIELD BASED ON PROJECT NUMBERS
                            [invoice_obj.invoice_project.add(item) for item in Project.objects.filter(project_number__in=projectlist)]
                            # -----------------------------------------------------------

                            invoice_obj.invoice_status = "1"

                            # =================== BEGIN::Round the all Amounts ===================
                            invoice_obj.invoice_total_amount = round(invoice_obj.invoice_total_amount, 0 if invoice_obj.invoice_currency.currency_iso=='INR' else 2)
                            invoice_obj.invoice_subtotal_amount = round(invoice_obj.invoice_subtotal_amount, 2)
                            invoice_obj.invoice_IGST_value = round(invoice_obj.invoice_IGST_value, 2)
                            invoice_obj.invoice_SGST_value = round(invoice_obj.invoice_SGST_value, 2)
                            invoice_obj.invoice_CGST_value = round(invoice_obj.invoice_CGST_value, 2)
                            invoice_obj.invoice_TDS_amount = round(invoice_obj.invoice_TDS_amount, 2)
                            # =================== END::Round the all Amounts ===================

                            project_obj = Project.objects.filter(project_number__in = projectlist)
                            for project_id in project_obj:
                                update_status(project_id.id, "Invoiced", action='change-project-status',user=request.user)
                            
                            # UPDATE DRAFTINVOICE'S project_invoiced_date FIELD AS WELL FOR ALL INVOICED PROJECTS, SO THAT INVOICED DRAFTINVOICES CAN BE FETCHED BASED ON THE CUSTOM DATE
                            DraftInvoice.objects.filter(project__project_number__in=projectlist).update(project_invoiced_date=datetime.now().date())
                            
                            customer_obj = CustomerOrganization.objects.get(id = invoice_obj.invoice_customer.id)
                            
                            try:
                                if customer_obj.company_invoice_bank_detail.company_details.company_local_currency.id == int(invoice_obj.invoice_currency.id):
                                    invoice_new_no = customer_obj.company_invoice_bank_detail.company_details.company_invoice_suffix_local_currency
                                    company_prefix_local_currency = customer_obj.company_invoice_bank_detail.company_details.company_invoice_prefix_local_currency
                                    new_invoice_number = int(invoice_new_no)+1
                                    invoice_number = f"{company_prefix_local_currency}-{new_invoice_number}"
                                    invoice_obj.prefix = company_prefix_local_currency
                                    invoice_obj.suffix = new_invoice_number

                                    ## Invoice New Number Update in Company Details
                                    CompanyDetails.objects.filter(id =customer_obj.company_invoice_bank_detail.company_details.id).update(company_invoice_suffix_local_currency = new_invoice_number)

                                else:
                                    invoice_new_no = customer_obj.company_invoice_bank_detail.company_details.company_invoice_suffix_international_currency
                                    company_prefix_international_currency = customer_obj.company_invoice_bank_detail.company_details.company_invoice_prefix_international_currency
                                    new_invoice_number = int(invoice_new_no)+1
                                    invoice_number = f"{company_prefix_international_currency}-{new_invoice_number}"
                                    invoice_obj.prefix = company_prefix_international_currency
                                    invoice_obj.suffix = new_invoice_number

                                    ## Invoice New Number Update in Company Details
                                    CompanyDetails.objects.filter(id =customer_obj.company_invoice_bank_detail.company_details.id).update(company_invoice_suffix_international_currency = new_invoice_number)

                                
                                invoice_obj.invoice_number = invoice_number
                                invoice_obj.company_invoice_bank_detail = invoice_obj.invoice_customer.company_invoice_bank_detail

                                invoice_obj.save(force_update=True)
                            except Exception as e:
                                InvoiceExceptionsLog.objects.create(
                                    invoice = invoice_obj,request_data = requested_data,exception_raise = e,created_by= request.user)

                            invoice_subtotal = 0

                            invoice_row_list = []
                            projects_not_approved = []

                            for project_group in project_groups:
                                generate_invoice_row = True

                                if project_group.get('project_number'):
                                    if Project.objects.filter(project_number=project_group['project_number']).exclude(project_status__in=['ReadyForInvoiceApproved','Invoiced']).exists():
                                        projects_not_approved.append(project_group['project_number'])

                                if (generate_invoice_row):
                                    total_amount = project_group['project_group_total_amount']
                                    if total_amount == None:
                                        total_amount = 0
                                    else:
                                        # =================== BEGIN::Round the Row Total Amount ===================
                                            total_amount = round(total_amount, 2)
                                        # =================== END::Round the Row Total Amount ===================

                                    # Calculate Invoice row total amount for Invoice Subtotal
                                    invoice_subtotal += total_amount

                                    try:
                                        row_description = project_group['project_group_description']
                                    except:
                                        row_description = ""
                                    try:
                                        row_po_number = project_group['po_number']
                                    except:
                                        Invoice.objects.filter(id=invoice_obj.id).delete()
                                        Project.objects.filter(project_number__in=projectlist).update(project_status="ReadyForInvoiceApproved")
                                        return Response({'error': 'Pass the mandatory po_number field in project_groups array of objects, Invoice and its Rows Not Created'}, status= status.HTTP_400_BAD_REQUEST)
                                        
                                    invoice_row_list.append(
                                        InvoiceRow(invoice = invoice_obj,
                                            row_completes = project_group['project_group_completes'],
                                            row_cpi = round(project_group['project_group_cpi'], 2),
                                            row_total_amount = total_amount,
                                            row_description = row_description,
                                            created_by = request.user,
                                            row_project_number=Project.objects.filter(project_number=project_group['project_number'])[0] if Project.objects.filter(project_number=project_group.get('project_number')) else None,
                                            row_po_number=row_po_number,
                                            row_hsn_code=project_group.get('project_group_hsn_code') if project_group.get('project_group_hsn_code') else None
                                        )
                                    )
                            # =================== BEGIN::Bulk Create Invoice Row ===================
                            if invoice_row_list:
                                InvoiceRow.objects.bulk_create(invoice_row_list)
                            # =================== END::Bulk Create Invoice Row ===================

                            if projects_not_approved:
                                Invoice.objects.filter(id=invoice_obj.id).delete()
                                Project.objects.filter(project_number__in=projectlist).update(project_status="ReadyForInvoiceApproved")
                                return Response({'error': 'Some Project Numbers inserted are not ReadyForInvoiceApproved, so the Invoice not Created', 'Projects Not Approved List':projects_not_approved}, status= status.HTTP_400_BAD_REQUEST)

                            # CREATE SUPPLIERIDSMARKS WHEN PROJECT IS INVOICED
                            [SupplierIdsMarks.objects.update_or_create(project=project_id,
                            defaults={'supplier_ids_sent': 'No','final_ids_available_by':datetime.now().date()}) for project_id in project_obj]

                            return Response({'invoice_number': invoice_obj.invoice_number}, status=status.HTTP_200_OK)
                        except Exception as e:
                            InvoiceExceptionsLog.objects.create(
                                invoice = invoice_obj,request_data = requested_data,exception_raise = e,created_by= request.user)
                    else:
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'error':'You cannot create an invoice more than 15 Project'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'There are no projects'}, status= status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'You cannot create an invoice since you are trying to create an invoice for project which is not ReadyForInvoiceApproved.'}, status= status.HTTP_400_BAD_REQUEST)



class InvoiceUpdateStatusView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, UpdateInvoice)
    serializer_class = InvoiceUpdateStatusSerializer

    def get_object(self, invoice_number):

        try:
            invoice_obj = Invoice.objects.get(invoice_number=invoice_number)
            return invoice_obj
        except:
            return None

    def get(self, request, invoice_number):

        instance = self.get_object(invoice_number)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'Given Invoice number does not exist..!'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, invoice_number):

        instance = self.get_object(invoice_number)
        if instance != None:
            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid(raise_exception=True):
                if instance.invoice_status == "3" and serializer.validated_data.get('invoice_status') == "4":
                    return Response({'error': 'You cannot cancel the incoice if you have paid invoice..!'}, status=status.HTTP_400_BAD_REQUEST)

                invoice_obj = serializer.save(modified_by = request.user)
                if serializer.validated_data.get('invoice_status') == "4":
                    invoice_obj.invoice_total_amount = 0
                    invoice_obj.invoice_subtotal_amount = 0
                    invoice_obj.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Given Invoice number does not exist..!'}, status=status.HTTP_404_NOT_FOUND)


class InvoiceUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, UpdateInvoice)
    serializer_class = InvoiceUpdateSerializer

    def get_object(self, invoice_number):

        try:
            invoice_obj = Invoice.objects.get(invoice_number=invoice_number)
            return invoice_obj
        except:
            return None

    def get(self, request, invoice_number):

        instance = self.get_object(invoice_number)
        if instance != None:
            serializer = InvoiceGetDataSerializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'Given Invoice number does not exist..!'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, invoice_number):

        instance = self.get_object(invoice_number)
        final_invoice_number =  invoice_number
        if instance != None:
            serializer = self.serializer_class(instance,data=request.data)
            if serializer.is_valid(raise_exception=True):
                if instance.invoice_status == "3" and serializer.validated_data.get('invoice_status') == "4":
                    return Response({'error': 'You cannot cancel the incoice if you have paid invoice..!'}, status=status.HTTP_400_BAD_REQUEST)

                pre_update_instance = instance.invoice_currency.currency_iso
                pre_update_customer = instance.invoice_customer.id

                invoice_obj = serializer.save(modified_by = request.user)
                invoice_log(serializer.data,'',invoice_obj,None,request.user)
                # in case of any change in customer organisation of invoice
                if pre_update_customer != invoice_obj.invoice_customer.id:
                    invoice_obj.invoice_project.all().update(project_customer=invoice_obj.invoice_customer, project_client_contact_person=invoice_obj.invoice_contact, project_client_invoicing_contact_person=invoice_obj.invoice_contact, project_currency=invoice_obj.invoice_customer.currency)
                    DraftInvoice.objects.filter(project_id__in = invoice_obj.invoice_project.values_list('id',flat = True)).update(invoice_to_customer_id=invoice_obj.invoice_customer.id)

                # invoice cancel
                if serializer.validated_data.get('invoice_status') == "4":
                    invoice_obj.invoice_total_amount = 0
                    invoice_obj.invoice_subtotal_amount = 0


                # In case of currency change
                if pre_update_instance != serializer.validated_data.get('invoice_currency').currency_iso:
                    customer_obj = CustomerOrganization.objects.get(id = invoice_obj.invoice_customer.id)
                    if customer_obj.company_invoice_bank_detail.company_details.company_local_currency.id == int(invoice_obj.invoice_currency.id):
                        exist_invoice_no = customer_obj.company_invoice_bank_detail.company_details.company_invoice_suffix_local_currency
                        company_prefix_local_currency = customer_obj.company_invoice_bank_detail.company_details.company_invoice_prefix_local_currency
                        no = int(exist_invoice_no)+1
                        nonInr_invoice_obj = Invoice.objects.filter(pk=invoice_obj.pk).values()[0]
                        nonInr_invoice_obj.pop('id')
                        nonInr_invoice_obj.pop('invoice_number')
                        nonInr_invoice_obj = Invoice.objects.create(**nonInr_invoice_obj)
                        nonInr_invoice_obj.invoice_number = f"{company_prefix_local_currency}-{str(no)}"
                        for item in invoice_obj.invoice_project.all():
                            nonInr_invoice_obj.invoice_project.add(item)
                        for item in invoice_obj.invoicerow_set.all():
                            nonInr_invoice_obj.invoicerow_set.add(item)
                        nonInr_invoice_obj.save()

                        # We are also update invoice number in comapany details
                        company_details_obj = CompanyDetails.objects.filter(id =customer_obj.company_invoice_bank_detail.company_details.id).update(company_invoice_suffix_local_currency = no)
                        
                        invoice_obj.invoice_status = '4'
                        invoice_obj.invoice_total_amount = 0
                        invoice_obj.invoice_subtotal_amount = 0
                        invoice_obj.invoice_total_amount_in_USD = 0
                        invoice_obj.invoice_currency = Currency.objects.get(currency_iso=pre_update_instance)

                        final_invoice_number = nonInr_invoice_obj.invoice_number

                    else:
                        exist_invoice_no = customer_obj.company_invoice_bank_detail.company_details.company_invoice_suffix_international_currency
                        company_prefix_international_currency = customer_obj.company_invoice_bank_detail.company_details.company_invoice_prefix_international_currency
                        no = int(exist_invoice_no)+1
                        nonInr_invoice_obj = Invoice.objects.filter(pk=invoice_obj.pk).values()[0]
                        nonInr_invoice_obj.pop('id')
                        nonInr_invoice_obj.pop('invoice_number')
                        nonInr_invoice_obj = Invoice.objects.create(**nonInr_invoice_obj)
                        nonInr_invoice_obj.invoice_number = f"{company_prefix_international_currency}-{str(no)}"
                        for item in invoice_obj.invoice_project.all():
                            nonInr_invoice_obj.invoice_project.add(item)
                        for item in invoice_obj.invoicerow_set.all():
                            nonInr_invoice_obj.invoicerow_set.add(item)
                        nonInr_invoice_obj.save()

                        # We are also update invoice number in comapany details
                        CompanyDetails.objects.filter(id =customer_obj.company_invoice_bank_detail.company_details.id).update(company_invoice_suffix_international_currency = no)
                        
                        invoice_obj.invoice_status = '4'
                        invoice_obj.invoice_total_amount = 0
                        invoice_obj.invoice_subtotal_amount = 0
                        invoice_obj.invoice_total_amount_in_USD = 0
                        invoice_obj.invoice_currency = Currency.objects.get(currency_iso=pre_update_instance)

                        final_invoice_number = nonInr_invoice_obj.invoice_number
                        
                    invoice_obj.company_invoice_bank_detail = invoice_obj.invoice_customer.company_invoice_bank_detail

                invoice_obj.save()
                    
                return Response({'invoice_number':final_invoice_number}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Given Invoice number does not exist..!'}, status=status.HTTP_404_NOT_FOUND)


class InvoiceRowUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = InvoiceRowUpdateSerializer

    def get_object(self, invoice_row_id):

        try:
            invoice_row_obj = InvoiceRow.objects.get(id=invoice_row_id)
            return invoice_row_obj
        except:
            return None

    def get(self, request, invoice_row_id):

        instance = self.get_object(invoice_row_id)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response({'error': 'Given Invoice Row object does not exist..!'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, invoice_row_id):

        instance = self.get_object(invoice_row_id)
        if instance != None:
            serializer = self.serializer_class(instance,data=request.data)
            if serializer.is_valid(raise_exception=True):
                invoice_row_obj = serializer.save(modified_by = request.user)
                # =================== BEGIN::Round the Row Total Amount ===================
                invoice_row_obj.row_cpi = round(invoice_row_obj.row_cpi, 2)
                invoice_row_obj.row_total_amount = round(invoice_row_obj.row_total_amount, 2)
                invoice_row_obj.save(force_update=True)
                # =================== END::Round the Row Total Amount ===================

                # =================== BEGIN::Update Project Number if Passed from the FrontEnd ===================
                if request.data.get('row_project_number'):
                    try:
                        invoice_row_obj.row_project_number = Project.objects.get(project_number=request.data.get('row_project_number'))
                        invoice_row_obj.save()
                    except:
                        pass
                # =================== END::Update Project Number if Passed from the FrontEnd ===================

                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({'error': 'Given Invoice Row object does not exist..!'}, status=status.HTTP_404_NOT_FOUND)


    def delete(self, request, invoice_row_id):
        invoiceRow_qs = InvoiceRow.objects.filter(id=invoice_row_id)
        if invoiceRow_qs:
            invoiceRow_qs.delete()
            return Response({'detail': 'Given Invoice Row Deleted Successfully'}, status=status.HTTP_200_OK)
        return Response({'error': 'Given Invoice Row object does not exist..!'}, status=status.HTTP_404_NOT_FOUND)


class InvoicePdfView(APIView):

    def get_object(self, invoice_number):

        try:
            invoice_obj = Invoice.objects.get(invoice_number=invoice_number)
            return invoice_obj
        except:
            return None

    def render_to_pdf(self,template_src, context_dict):

        template = get_template(template_src)
        html  = template.render(context_dict)
        from io import BytesIO
        response = BytesIO()

        pdf = pisa.CreatePDF(html.encode('UTF-8'), response, encoding="UTF-8", link_callback=link_callback)
        if not pdf.err:
            return HttpResponse(response.getvalue(), content_type='application/pdf')
        else:
            return HttpResponse("Error Rendering PDF" + html, status=400)

    def get(self, request, invoice_number):

        template_path = "Invoice/new_invoice.html"
        instance = self.get_object(invoice_number)

        if instance != None:
            serializer = InvoicePdfGetDataSerializer(instance)
            context = serializer.data
            
            #rendering the template
            pdf = self.render_to_pdf(template_path, context)
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename=' + context["invoice_number"] + '.pdf'
            return pdf
            
        else:
            return Response({'error': 'Given Invoice number does not exist..!'}, status=status.HTTP_400_BAD_REQUEST)


class invoiceHTML(TemplateView):
    template_name = "Invoice/new_invoice.html"

    def get_object(self, invoice_number):

        try:
            invoice_obj = Invoice.objects.get(invoice_number=invoice_number)
            return invoice_obj
        except:
            return None

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        invoice_number = request.GET.get('invoice_number','0')
        instance = self.get_object(invoice_number)
        if instance != None:
            serializer = InvoicePdfGetDataSerializer(instance)
            context = serializer.data
        else:
            context = {}
        return self.render_to_response(context)


class InvoiceRowView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = InvoiceRowSerilaizer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            invoice_row_obj = serializer.save(created_by=request.user)
            # =================== BEGIN::Round the Row Total Amount ===================
            invoice_row_obj.row_cpi = round(invoice_row_obj.row_cpi, 2)
            invoice_row_obj.row_total_amount = round(invoice_row_obj.row_total_amount, 2)
            invoice_row_obj.save(force_update=True)
            # =================== END::Round the Row Total Amount ===================

            # =================== BEGIN::Update Project Number if Passed from the FrontEnd ===================
            if request.data.get('row_project_number'):
                try:
                    invoice_row_obj.row_project_number = Project.objects.get(project_number=request.data.get('row_project_number'))
                    invoice_row_obj.save()
                except:
                    pass
            # =================== END::Update Project Number if Passed from the FrontEnd ===================

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendInvoicePdfEmailView(APIView):

    def get_object(self, invoice_number):

        try:
            invoice_obj = Invoice.objects.get(invoice_number=invoice_number)
            return invoice_obj
        except:
            return None

    def post(self, request):

        template_path = "Invoice/new_invoice.html"
        invoice_number = request.data.get('invoice_number')
        customerid = request.data.get('customerid')
        instance = self.get_object(invoice_number)

        if instance != None:
            serializer = InvoicePdfGetDataSerializer(instance)
            context = serializer.data
            actual_url = request.build_absolute_uri().rsplit("/",4)[0]
            context.update({"actual_url":actual_url, "EMAIL_STATICFILE_BASE_URL":settings.EMAIL_STATICFILE_BASE_URL})
            
            # find the template and render it.
            template = get_template(template_path)
            html = template.render(context)

            # ************ BEGIN:: Write a pdf from static directory ************
            output_filename = os.path.join('{}/pdf/invoice_{}.pdf'.format(settings.STATIC_DIR,instance.invoice_number))
            result_file = open(output_filename, "wb")
            # ************ END:: Write a pdf from static directory ************

            # create a pdf
            pisa_status = pisa.CreatePDF(
            html, dest=result_file, link_callback=link_callback)
            result_file.close() 

            with open(output_filename, 'rb') as f:
                data = f.read()
                f.close()

            encoded = base64.b64encode(data).decode()

            # if error then show some funy view
            if pisa_status.err:
                return HttpResponse('We had some errors <pre>' + html + '</pre>', status=400)
            
            customercontacts = ClientContact.objects.filter(id__in = customerid).values_list('client_email', flat=True)
            to_emails = list(customercontacts)
            subject = f'Invoice - {instance.invoice_number} from PANEL VIEWPOINT PRIVATE LIMITED'
            html_message = render_to_string('Invoice/invoice_email_temaplate.html',
                                {'context':context,'month':datetime.now().strftime("%B"),'year':datetime.now().strftime("%Y")})
            attachedFile = Attachment(FileContent(encoded), FileName(f"invoice_{instance.invoice_number}.pdf"), FileType('application/pdf'),Disposition('attachment'))
            
            if settings.SERVER_TYPE == 'production':
                cc_emails = 'ar@panelviewpoint.com'
            else:
                cc_emails = 'tech@panelviewpoint.com'
            
            sendEmail = sendEmailSendgripAPIIntegration(from_email = ('accounts@panelviewpoint.com', 'Accounts Team'),to_emails=to_emails, subject=subject, html_message=html_message, attachedFile=attachedFile, cc_emails = cc_emails)

            # ************ BEGIN:: Remove a csv from static directory ************
            output_filename = os.path.join('{}/pdf/invoice_{}.pdf'.format(settings.STATIC_DIR,instance.invoice_number))
            os.remove(output_filename)  
            # ************ END:: Remove a csv from static directory ************

            if sendEmail.status_code == 200:
                instance.invoice_status = '2'
                instance.save()
                return Response({'msg': 'Email sent successfully..!'}, status=status.HTTP_200_OK)
            else:
                return sendEmail
        else:
            return Response({'error': 'Given Invoice number does not exist..!'}, status=status.HTTP_400_BAD_REQUEST)

class InvoiceListXLSDownload(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = InvoiceExcelSerializer

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=invoice_stats.csv'


        if request.GET.get('invoice_status') and request.GET.get('invoice_customer'):
            invoice_qs = Invoice.objects.select_related('invoice_customer','invoice_contact','invoice_currency').prefetch_related('invoice_project').filter(invoice_status=request.GET['invoice_status'],invoice_customer_id=request.GET['invoice_customer']).order_by('-id')
        elif request.GET.get('invoice_status') and not request.GET.get('invoice_customer'):
            invoice_qs = Invoice.objects.select_related('invoice_customer','invoice_contact','invoice_currency').prefetch_related('invoice_project').filter(invoice_status=request.GET['invoice_status']).order_by('-id')
        elif not request.GET.get('invoice_status') and request.GET.get('invoice_customer'):
            invoice_qs = Invoice.objects.select_related('invoice_customer','invoice_contact','invoice_currency').prefetch_related('invoice_project').filter(invoice_customer_id=request.GET['invoice_customer']).order_by('-id')
        elif not request.GET.get('invoice_status') and not request.GET.get('invoice_customer'):
            invoice_qs = Invoice.objects.select_related('invoice_customer','invoice_contact','invoice_currency').prefetch_related('invoice_project').all().order_by('-id')

        if not invoice_qs.exists():
            return Response({'detail':'Invoice does not exist for this Customer'})

        serializer = self.serializer_class(invoice_qs, many=True)
        serializer_data = serializer.data

        writer = csv.writer(response)
    
        csv_header = ['Invoice Status', 'Invoice Number', 'Invoice Project Number', 'Invoice Customer','Billing Person', 'Invoice Date','Invoice Due Date', 'Invoice Currency', 'Invoice Total Amount', 'Invoice PO Number']
        writer.writerow(csv_header)

        for invoice_data in serializer_data:
            invoice_status = invoice_data['invoice_status']
            invoice_number = invoice_data['invoice_number']
            invoice_project = invoice_data['invoice_project']
            invoice_customer = invoice_data['invoice_customer']
            invoice_contact = invoice_data['invoice_contact']
            invoice_date = invoice_data['invoice_date']
            invoice_due_date = invoice_data['invoice_due_date']
            invoice_currency = invoice_data['invoice_currency']
            invoice_total_amount = invoice_data['invoice_total_amount']
            invoice_po_number = invoice_data['invoice_po_number']
            content = [invoice_status, invoice_number, invoice_project, invoice_customer, invoice_contact, str(invoice_date), str(invoice_due_date), invoice_currency, invoice_total_amount, invoice_po_number]
            writer.writerow(content)

        return response


class InvoiceRowsXLSXDownload(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        output = BytesIO()
        invoice_number = request.GET.get('invoice_numbers')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if invoice_number and start_date and end_date:
            invoice_number_list = invoice_number.split(',')
            invoice_row_qs = InvoiceRow.objects.select_related('invoice','invoice__invoice_customer','invoice__invoice_currency').filter(invoice__invoice_number__in=invoice_number_list, invoice__invoice_date__gte=start_date, invoice__invoice_date__lte=end_date).order_by('invoice','id')
        elif not invoice_number and start_date and end_date:
            invoice_row_qs = InvoiceRow.objects.select_related('invoice','invoice__invoice_customer','invoice__invoice_currency').filter( invoice__invoice_date__gte=start_date, invoice__invoice_date__lte=end_date).order_by('invoice','id')
        else:
            return Response({'message': 'Please provide a Start Date & an End Date'}, status=status.HTTP_400_BAD_REQUEST)

        if not invoice_row_qs:
            return Response({'message': 'No Invoices exist for the given Invoice Numbers'}, status=status.HTTP_400_BAD_REQUEST)
            
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Invoice')
        column_incr = 0
        head_columns = ['Bill No','Bill date','Party Name','State','Party GST','Item Name', 'Project Number','PO Number','Unit','HSN No','GST Per','Sales Ledger','Qty','Rate','Item Amount','CGST','SGST','IGST Ledger','IGST','Currency']
        cell_format = workbook.add_format({'bold': True, 'bg_color': 'yellow'})
        for _ , column in zip(range(19), head_columns):
            worksheet.set_column(column_incr, column_incr, len(column)+2)
            worksheet.write(0, column_incr, column, cell_format)
            column_incr+=1
        worksheet.set_column(5, 5, 25)
        worksheet.set_column(4, 4, 20)
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(2, 2, 15)
        worksheet.set_column(6, 6, 15)

        data_row_incr = 1
        #Looping through Rows
        for invrow_obj in invoice_row_qs:
            try:
                project_number = invrow_obj.row_project_number.project_number
            except:
                project_number = 'N/A'

            try:
                row_po_number = invrow_obj.row_po_number
            except:
                row_po_number = 'N/A'

            columns_data = [
                invrow_obj.invoice.invoice_number,
                datetime.strftime(invrow_obj.invoice.invoice_date, "%d-%m-%Y"),
                invrow_obj.invoice.invoice_customer.cust_org_name,
                invrow_obj.invoice.invoice_customer.cust_org_state,
                invrow_obj.invoice.invoice_customer.cust_org_TAXVATNumber,
                invrow_obj.row_description,
                project_number,
                row_po_number,
                'Completes',
                '998371',
                '18',
                'Sales GST',
                invrow_obj.row_completes,
                invrow_obj.row_cpi,
                invrow_obj.row_total_amount,
                (invrow_obj.row_total_amount*9)/100 if invrow_obj.invoice.invoice_tax == '3' else None,
                (invrow_obj.row_total_amount*9)/100 if invrow_obj.invoice.invoice_tax == '3' else None,None,
                (invrow_obj.row_total_amount*18)/100 if invrow_obj.invoice.invoice_tax == '2' else None,
                invrow_obj.invoice.invoice_currency.currency_iso
            ]
            data_column_incr = 0
            #Looping through Columns in those Rows
            for _ , column in zip(range(len(columns_data)), columns_data):
                worksheet.write(data_row_incr, data_column_incr, column)
                data_column_incr+=1
            data_row_incr+=1

        workbook.close()

        response = HttpResponse(output.getvalue(), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=AdvancedSales.xlsx'
        return response



class InvoiceByProjectXLSX(ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = InvoiceByProjectXLSXSerializer
    queryset = Project.objects.all()


    def get(self, request):
        response_type = request.GET.get('response_type')

        if response_type == 'json':
            return super().get(self, request)
            
        elif response_type == 'xlsx':
            in_memory = BytesIO()
            workbook = xlsxwriter.Workbook(in_memory)
            worksheet = workbook.add_worksheet('Invoice')

            column_incr = 0
            cell_format = workbook.add_format({'bold': True, 'italic':True, 'bg_color': 'purple','font_color':'yellow'})

            head_columns = ['Status','Invoice #','Project #','Project Name','Customer Name','Invoice Date', 'Due Date','Invoice Received','Invoice Amount','Currency']
            for column in head_columns:
                worksheet.set_column(column_incr, column_incr, 19)
                worksheet.write(0, column_incr, column, cell_format)
                column_incr+=1

            # Project Queryset & its Invoice Querysets
            project_data = []
            for project in super().get(self, request).data:
                dict_project = dict(project)
                invoice_set = dict_project.pop('invoice_set')
                project_data.append(dict_project)
                nested_inv_list = []
                for invoice in invoice_set:
                    nested_inv_list.append(dict(invoice))
                    dict_project.update({'invoice_set':nested_inv_list})
                
            data_row_incr = 1
            for project_dict in project_data:
                for invoice_dict in project_dict['invoice_set']:
                    data_column_incr = 0
                    worksheet.write(data_row_incr, data_column_incr, invoice_dict['invoice_status'])
                    data_column_incr+=1
                    worksheet.write(data_row_incr, data_column_incr, invoice_dict['invoice_number'])
                    data_column_incr+=1
                    worksheet.write(data_row_incr, data_column_incr, project_dict['project_number'])
                    data_column_incr+=1
                    worksheet.write(data_row_incr, data_column_incr, project_dict['project_name'])
                    data_column_incr+=1
                    worksheet.write(data_row_incr, data_column_incr, project_dict['project_customer'])
                    data_column_incr+=1
                    worksheet.write(data_row_incr, data_column_incr, invoice_dict['invoice_date'])
                    data_column_incr+=1
                    worksheet.write(data_row_incr, data_column_incr, invoice_dict['invoice_due_date'])
                    data_column_incr+=1
                    worksheet.write(data_row_incr, data_column_incr, 'Yes')
                    data_column_incr+=1
                    worksheet.write(data_row_incr, data_column_incr, invoice_dict['invoice_total_amount'])
                    data_column_incr+=1
                    worksheet.write(data_row_incr, data_column_incr, invoice_dict['invoice_currency'])
                    data_column_incr+=1
                    data_row_incr+=1

            workbook.close()

            response = HttpResponse(in_memory.getvalue(), content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=Client Invoice Report.xlsx'
            return response

        else:
            return Response(data={'message':'Please specify response_type to either json or xlsx'}, status=status.HTTP_400_BAD_REQUEST)


# DRAFTINVOICE AND DRAFTINVOICEROW APIS

class DraftInvoiceAndRowsCreate(generics.CreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = DraftInvoiceSerializer
    queryset = DraftInvoice.objects.all()

    def post(self, request):
        data = request.data
        obj_exist_without_id = False
        has_id = data.get('id')
        project_obj = get_object_or_none(Project, id=data.get('project'), project_status__in=['Reconciled','ReadyForAudit','ReadyForInvoice'])
        if project_obj:

            # DRAFTINVOICE UPDATE WITHOUT ID
            draft_invoice_unique_qs = DraftInvoice.objects.filter(project__id=data.get('project'))
            if draft_invoice_unique_qs:
                obj_exist_without_id = True
                serializer = self.serializer_class(draft_invoice_unique_qs.first(), data=data,context = {'user':request.user,'emp_type':request.user.emp_type})
            
            if not obj_exist_without_id:
                if has_id not in ['', None]:
                    draft_invoice_obj = get_object_or_none(DraftInvoice, id=data.get('id'))
                    if draft_invoice_obj:
                        serializer = self.serializer_class(draft_invoice_obj, data=data,context = {'user':request.user,'emp_type':request.user.emp_type})
                    else:
                        return Response(data={'message':'DraftInvoice & its DraftInvoiceRows not created due to Project not being in ReadyForInvoice or Reconciled'}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
                else:
                    serializer = self.serializer_class(data=data,context = {'user':request.user,'emp_type':request.user.emp_type})

            if serializer.is_valid(raise_exception=True):
                project_obj.project_customer = serializer.validated_data.get('invoice_to_customer')
                project_obj.save(force_update=True, update_fields=['project_status','project_customer'])
                draft_invoice_obj = serializer.save()
                DraftInvoiceChangesStore.objects.create(draft_invoice_id = draft_invoice_obj.id,payload_data = serializer.data,created_by = request.user)
                draft_invoice_log(serializer.data,'',draft_invoice_obj,project_obj.project_status,request.user)
                return Response({'draft_invoice_id':draft_invoice_obj.id,'message':'DraftInvoice & its DraftInvoiceRows Created Successfully'}, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={'error':'Project Not Updated to ReadyForInvoice successfully, Pass the correct project ID/Project Not Reconciled/ReadyForInvoice'}, status=status.HTTP_400_BAD_REQUEST)


class DraftInvoiceListView(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = DraftInvoiceSerializer
    queryset = DraftInvoice.objects.all()
    filterset_class = DraftInvoiceFilterSet


class DraftInvoiceRowsListView(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = DraftInvoiceRowListSerializer
    queryset = DraftInvoiceRow.objects.filter(draft_invoice__project__project_status='ReadyForInvoiceApproved')
    filterset_class = DraftInvoiceRowFilterSet



class DraftInvoiceStatusUpdateView(generics.CreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = DraftInvoicesAndRowsByIDsSerializer


    # PUT FUNCTION TO UPDATE THE DRAFTINVOICE TO APPROVED = TRUE & TO UPDATE THE PROJECT STATUS FROM READYFORINVOICE TO READYFORINVOICEAPPROVED
    def post(self, request):

        if settings.SERVER_TYPE == 'production':
            cc_emails = 'narendra@panelviewpoint.com'
        else:
            cc_emails = 'tech@panelviewpoint.com'

        status = request.data.get('status')

        if status in ('ReadyForInvoiceApproved', None):
            if request.user.emp_type not in ('4','7','9','11'):
                return Response(data={'message':'Only Accountant Executives & Leadership are allowed to Approve the ReadyForInvoice Status'})

        if status not in ('Reconciled','ReadyForAudit','ReadyForInvoiceApproved','ReadyForInvoice','',None):
            return Response(data={'message':'Only Reconciled,ReadyForInvoiceApproved,ReadyForInvoice value allowed in status'})

        note = request.data.get('note')
        draft_invoice_ids = request.data.get('draft_invoice_ids')

        if not draft_invoice_ids:
            return Response(data={'message':'Please pass draft_invoice_ids'})
            
        draft_invoice_ids = draft_invoice_ids.split(',')

        if status == 'Reconciled':
            project_qs = Project.objects.filter(draftinvoice__id__in=draft_invoice_ids)

            # ALSO UPDATE THE STATUSES OF PROJECTGROUP & PROJECTGROUPSUPPLIER
            list(map(lambda x:update_status(x.id,status,action='change-project-status',user=request.user)), project_qs)

            # SEND INDIVIDUAL EMAIL TO ALL PROJECT MANAGERS OF THE PROJECTS WHOSE STATUS ARE RECONCILED
            for project in project_qs:
                if note in (None,''):
                    return Response(data={'error':'Please pass note key when Changing the Project Status to Reconciled'})
                DraftInvoice.objects.filter(id__in=draft_invoice_ids).update(approval_note=note)
                html_message = render_to_string('Invoice/project_status_reconciled_invoice_rejected.html', context={'project':project, 'request':request})
                sendEmailSendgripAPIIntegration(from_email='accountsupdate@panelviewpoint.com', to_emails=project.project_manager.email, subject=f'Project Invoice Rejected By Accounts : {project.project_number}', html_message=html_message, cc_emails=cc_emails)

            return Response(data={'message':'All passed DraftInvoice Ids deleted due to status being Reconciled'})

        if status in ['ReadyForAudit'] and request.user.emp_type not in ['4','7','9']:
            return Response({"message":"You do not have permission to access."})
        
        if status in ['ReadyForInvoice'] and request.user.emp_type not in ['4','7','9','11']:
            return Response({"message":"You do not have permission to access."})

        if status in ['ReadyForAudit']:
            DraftInvoice.objects.filter(id__in=draft_invoice_ids).update(draft_approved=False, approval_note=note if note else '', conversion_rate=request.data.get('conversion_rate'), BA_approved = False, Accountant_approved = False, BA_approved_by = None, modified_by = request.user)

        if status in ['ReadyForInvoice']:
            DraftInvoice.objects.filter(id__in=draft_invoice_ids).update(draft_approved=False, approval_note=note if note else '', conversion_rate=request.data.get('conversion_rate'), BA_approved = True, Accountant_approved = False, BA_approved_by = request.user, modified_by = request.user)

        if status in ('ReadyForInvoiceApproved', None):
            if request.data.get('conversion_rate') in (None,''):
                return Response(data={'message':'DraftInvoice Not Approved and Project Status not changed to ReadyForInvoiceApproved as conversion_rate not passed'})

            DraftInvoice.objects.filter(id__in=draft_invoice_ids).update(draft_approved=True, approval_note=note if note else '', conversion_rate=request.data.get('conversion_rate'), BA_approved = True, Accountant_approved = True, modified_by = request.user)


        project_qs = Project.objects.filter(draftinvoice__id__in=draft_invoice_ids)
        project_qs.update(project_status=status if status else 'ReadyForInvoiceApproved')

        # ALSO UPDATE THE STATUSES OF PROJECTGROUP & PROJECTGROUPSUPPLIER
        update_status(project_qs.first().id,status if status else 'ReadyForInvoiceApproved',action='change-project-status',user=request.user)

        serializer = self.serializer_class(DraftInvoice.objects.filter(id__in=draft_invoice_ids), many=True)
        # if note not in [None,'']:
        #     DraftInvoiceNotes.objects.create(draft_invoice_id = request.data.get('draft_invoice_ids'), notes = note, created_by = request.user)

        DraftInvoiceChangesStore.objects.create(draft_invoice_id = request.data.get('draft_invoice_ids'), approved_date = datetime.now(), approved_by = request.user, payload_data = serializer.data)

        return Response(data=serializer.data)



class DraftInvoiceUpdateFileUploadView(generics.UpdateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = DraftInvoiceUpdateFileUploadSerializer
    queryset = DraftInvoice.objects.all()



class InvoicePaymentReminderEmailView(generics.CreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = InvoicePaymentReminderEmailViewSerializer
    queryset = InvoicePaymentReminderEmail.objects.all()


    def post(self, request):
        request.data.update({'added_by':request.user.id})
        response_dict = super().post(request).data

        invoice_ids = request.data.get('invoices')
        client_cntct_ids = request.data.get('client_ids')
        today_date = datetime.now().date()
        client_contact_qs = ClientContact.objects.filter(id__in=client_cntct_ids)
        client_emails = client_contact_qs.values_list('client_email',flat=True)
        invoice_qs = Invoice.objects.filter(id__in=invoice_ids).annotate(due_days=datetime.now().date() - F('invoice_due_date')).order_by('id')

        invoice_row_qs = InvoiceRow.objects.filter(invoice__in = invoice_qs).annotate(due_days=datetime.now().date() - F('invoice__invoice_due_date'))

        html_message = render_to_string('Invoice/invoice_payment_reminder_email.html', {'invoice_row_qs':invoice_row_qs, 'today_date':today_date})

        sendEmail = sendEmailSendgripAPIIntegration(
            from_email = ('accounts@panelviewpoint.com', 'Payment Reminder'), 
            to_emails=list(client_emails), 
            cc_emails = 'ar@panelviewpoint.com' if settings.SERVER_TYPE == 'production' else 'pythonteam1@slickservices.in', subject=f'Followup : Payment status - {client_contact_qs[0].customer_id.cust_org_name} {datetime.now().date()}', html_message=html_message)

        if sendEmail.status_code not in [200, 201]:
            InvoicePaymentReminderEmail.objects.filter(id=response_dict['id']).delete()
            fail_reason = json.loads(sendEmail.content.decode())['message']
            return Response(data={'message':'Invoice Payment Reminder Email to Client Contacts not sent successfully', 'reason':fail_reason}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data={'message':'Invoice Payment Reminder Email Sent successfully to Client Contacts & Table Created'}, status=status.HTTP_201_CREATED)
        


class InvoiceListPaymentReminderEmailView(generics.CreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = InvoicePaymentReminderEmailViewSerializer
    queryset = InvoicePaymentReminderEmail.objects.all()

    def post(self, request):
        request.data.update({'added_by':request.user.id})
        response_dict = super().post(request).data

        invoice_ids = request.data.get('invoices')
        client_cntct_ids = request.data.get('client_ids')
        today_date = datetime.now().date()
        client_contact_qs = ClientContact.objects.filter(id__in=client_cntct_ids)
        client_emails = client_contact_qs.values_list('client_email',flat=True)
        invoice_qs = Invoice.objects.filter(id__in=invoice_ids).annotate(due_days=datetime.now().date() - F('invoice_due_date')).order_by("invoice_number")
        invoice_row_qs = InvoiceRow.objects.filter(invoice__in = invoice_qs).values(
            'invoice__invoice_number',
            'row_po_number',
            'row_completes',
            'row_cpi',
            'row_total_amount',
            'row_description',
            invoice_number = F('invoice__invoice_number'),
            invoice_currency = F('invoice__invoice_currency__currency_iso')
        ).annotate(
            due_days=datetime.now().date() - F('invoice__invoice_due_date')
        ).order_by("invoice__invoice_number")
        

        template_path = "Invoice/new_invoice_row_pdf.html"
        context = {"invoice_rows":invoice_row_qs,"invoice_currency":invoice_row_qs[0]['invoice_currency']}

        # Create a Django response object, and specify content_type as pdf
        """
        response = HttpResponse(content_type='application/pdf')
        content = "attachment; filename='invoice_reminder_details.pdf'"
        response['Content-Disposition'] = content
        """
        # find the template and render it.
        template = get_template(template_path)
        html = template.render(context)

        # # ************ BEGIN:: Write a pdf from static directory ************
        output_filename = os.path.join('{}/pdf/invoice_details{}.pdf'.format(settings.STATIC_DIR,'invoice_reminder'))

        result_file = open(output_filename, "wb")
        # # ************ END:: Write a pdf from static directory ************

        # create a pdf
        pisa_status = pisa.CreatePDF(
        html, dest=result_file, link_callback=link_callback)
        result_file.close()

        with open(output_filename, 'rb') as f:
            data = f.read()
            f.close()

        encoded = base64.b64encode(data).decode()

        # if error then show some funy view
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>', status=400)
        
        attachedFile = Attachment(FileContent(encoded), FileName(f"invoice_po_list.pdf"), FileType('application/pdf'),Disposition('attachment'))

        html_message = render_to_string('Invoice/invoice_payment_reminder_email.html', {'invoice_list':invoice_qs,'invoice_rows':invoice_row_qs, 'today_date':today_date})

        sendEmail = sendEmailSendgripAPIIntegration(
            from_email = ('accounts@panelviewpoint.com', 'Accounts Team'), 
            to_emails=list(client_emails), 
            cc_emails = 'ar@panelviewpoint.com' if settings.SERVER_TYPE == 'production' else 'tech@panelviewpoint.com', subject=f'Followup : Payment status - {client_contact_qs[0].customer_id.cust_org_name} {datetime.now().date()}', html_message=html_message, attachedFile=attachedFile)

        if sendEmail.status_code not in [200, 201]:
            InvoicePaymentReminderEmail.objects.filter(id=response_dict['id']).delete()
            fail_reason = sendEmail.content
            return Response(data={'message':'Invoice Payment Reminder Email to Client Contacts not sent successfully', 'reason':fail_reason}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data={'message':'Invoice Payment Reminder Email Sent successfully to Client Contacts & Table Created'}, status=status.HTTP_201_CREATED)



class DraftInvoiceGetCounts(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self, request):
            total_counts_dict = DraftInvoice.objects.all().aggregate(approval_counts=Count('id', filter=Q(project__project_status='ReadyForInvoice')),
            audit_counts=Count('id', filter=Q(project__project_status='ReadyForAudit')),
            approved_counts=Count('id', filter=Q(project__project_status='ReadyForInvoiceApproved')),
            invoiced_today_counts=Count('id', filter=Q(project__project_status='Invoiced', project_invoiced_date=datetime.now().date()))
            )

            return Response(data=total_counts_dict)



class ListDraftInvoiceStatsApprovedStatus(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self, request):
        approved_status_list = DraftInvoice.objects.filter(project__project_status='ReadyForInvoiceApproved').values('invoice_to_customer__id','invoice_currency__id').annotate(
            customer_name=F('invoice_to_customer__cust_org_name'),
            cust_currency=F('invoice_currency__id'),
            total_approved=Count('id'),
            total_invoice_amount=Sum('invoice_total')
        )

        return Response(data=approved_status_list)



class DraftInvoiceRowsListByProjectView(generics.ListAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = DraftInvoiceRowsListByProjectSerializer


    def get_queryset(self):
        project_number = self.request.GET.get('project_number')
        if project_number:
            queryset = DraftInvoiceRow.objects.filter(draft_invoice__project__project_number=project_number)
            return queryset
        else:
            return None


class DraftInvoiceRowsDeleteAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        draft_invoice_row_id = request.data.get('draft_invoice_row_id')
        
        draft_invoice_row_obj = DraftInvoiceRow.objects.filter(id__in = draft_invoice_row_id)
        if draft_invoice_row_obj.exists():
            DraftInvoice.objects.filter(
                draftinvoicerow__id = draft_invoice_row_obj.first().id).update(
                    bid_total = F('bid_total') -  draft_invoice_row_obj.first().bid_total)
            draft_invoice_row_obj.delete()
            return Response({"message":"Draft Invoice Row Delete Successfully.!"}, status=status.HTTP_200_OK)
        else:
            return Response({"error":"Given Draft Invoice Row Id does not exists.!"}, status=status.HTTP_400_BAD_REQUEST)


class InvoiceDeleteView(RetrieveDestroyAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'invoice_id'


class TotalOverDueReceivablesView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self,request,customer_id,*args,**kwargs):
        today_date = date.today()
        receivable_obj = Invoice.objects.filter(invoice_customer__id=customer_id,invoice_date__lte=today_date,invoice_status="2").values('id','invoice_status','invoice_customer__cust_org_name','invoice_total_amount')

        return Response({"receivable amount":receivable_obj}, status=status.HTTP_200_OK)


class TotalOverDuePayablesView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self,request,customer_id,*args,**kwargs):
        today_date = date.today()
        payables_obj = Invoice.objects.filter(invoice_customer__id=customer_id,invoice_date__lte=today_date,invoice_status="3").values('id','invoice_status','invoice_customer__cust_org_name','invoice_total_amount')

        return Response({"payables amount":payables_obj}, status=status.HTTP_200_OK) 

class GetInvoiceNumber(InvoiceNumber):
    def get(self,request):
        invoice_number = self.newInvoiceNumber(request=request)
        return Response({"NextInvoiceNumber":invoice_number}, status=status.HTTP_200_OK)



class InvoiceRevertApi(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, invoice_number):

        try:
            invoice_obj = Invoice.objects.get(invoice_number = invoice_number)
            invoice_obj.invoice_total_amount = 0
            invoice_obj.invoice_subtotal_amount = 0
            invoice_obj.invoice_status = "4"
            InvoiceRow.objects.filter(invoice = invoice_obj).update(row_total_amount = 0, row_project_number = None)

            invoice_obj.invoice_project.all().update(project_status = "ReadyForInvoiceApproved")
            project_list = invoice_obj.invoice_project.all()
            ProjectGroup.objects.filter(project__in = project_list).update(project_group_status = "ReadyForInvoiceApproved")
            DraftInvoice.objects.filter(project__in=project_list).update(project_invoiced_date=None)
            SupplierIdsMarks.objects.filter(project__in=project_list).update(final_ids_available_by = None)
            invoice_obj.invoice_project.clear()
            invoice_obj.save()

            return Response({"message":"Invoice Revert Successfully..!"}, status=status.HTTP_200_OK)
        except:
            return Response({'error': 'Given Invoice number does not exist..!'}, status=status.HTTP_400_BAD_REQUEST)



class CustomerInvoiceDueDateReminderList(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self, request):
        today_date = datetime.now().date()
        customer_invoice_duedate_list = Invoice.objects.filter(invoice_due_date__lte = today_date,invoice_status = "2").values('invoice_customer__id','invoice_currency__id').annotate(
            customer_name = F("invoice_customer__cust_org_name"),
            cust_currency = F("invoice_currency__id"),
            total_invoice = Count('id'),
            total_invoice_amount = Sum('invoice_total_amount')
        ).order_by("invoice_customer__cust_org_name")

        return Response(customer_invoice_duedate_list, status=status.HTTP_200_OK)
    

class CustomerWiseInvoiceDueDateList(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, customer_id, invoice_currency_id):
        today_date = datetime.now().date()

        customer_invoice_list = Invoice.objects.filter(invoice_due_date__lte = today_date,invoice_customer_id = customer_id,invoice_currency = invoice_currency_id,invoice_status = "2").values(
            invoice_id = F("id"),
            invoice_no = F("invoice_number"),
            project_number = F("invoice_project__project_number"),
            customer_name = F("invoice_customer__cust_org_name"),
            cust_currency = F("invoice_currency__id"),
            total_invoice_amount = F("invoice_total_amount"),
            due_date = F("invoice_due_date")
            )

        return Response(customer_invoice_list, status=status.HTTP_200_OK)
    


class MulitpleInvoiceInSinglePdfDownload(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def render_to_pdf(self,template_src, context_dict):

        template = get_template(template_src)
        html  = template.render(context_dict)
        from io import BytesIO
        response = BytesIO()
        pdf = pisa.CreatePDF(html.encode('UTF-8'), response, encoding="UTF-8", link_callback=link_callback)
        if not pdf.err:
            return HttpResponse(response.getvalue(), content_type = 'application/pdf')
        else:
            return HttpResponse("Error Rendering PDF" + html, status=400)

    def post(self, request):
        data = request.data
        invoice_number = data['invoice_number']

        merger = PdfFileMerger()
        
        template_path = "Invoice/new_invoice.html"
        invoice_obj = Invoice.objects.filter(invoice_number__in = invoice_number)
        for invoice in invoice_obj:
            serializer = InvoicePdfGetDataSerializer(invoice)
            context = serializer.data        
            # for context_data in context:
            #rendering the template
            template = get_template(template_path)
            html = template.render(context)
            pdf = self.render_to_pdf(template_path, context)

            output_filename = os.path.join('{}/pdf/invoice_{}.pdf'.format(settings.STATIC_DIR,f"{context['invoice_number']}"))
            result_file = open(output_filename, "wb")
            # create a pdf
            pisa_status = pisa.CreatePDF(
            html, dest=result_file, link_callback=link_callback)
            result_file.close() 
            pdf["Content-Disposition"] = 'attachment; filename=' + context["invoice_number"] + '.pdf'
            merger.append(output_filename)
              
        response = HttpResponse(merger, content_type = 'application/pdf')
        merger.write(response)
        merger.close()

        return response

class InvoiceCompanyUpdate(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self,request):
        invoice_number = request.data.get('invoice_number')
        invoice_currency_id = request.data.get('invoice_currency_id')
        company_invoice_bank_detail = request.data.get('company_invoice_bank_detail')
        invoice_date = request.data.get('invoice_date')

        old_invoice_obj = Invoice.objects.filter(invoice_number=invoice_number)
        new_invoice_data = old_invoice_obj.values()[0]
        new_invoice_data.pop('id')
        new_invoice_data.pop('invoice_number')

        # Create new invoice
        new_invoice_obj = Invoice.objects.create(**new_invoice_data)
        new_invoice_obj.invoice_date = invoice_date
        new_invoice_obj.invoice_currency = Currency.objects.get(id=invoice_currency_id)

        # Update old invoice to cancel, and set amount to 0.
        old_invoice_obj.update(invoice_status = '4',invoice_total_amount = 0,invoice_subtotal_amount = 0,invoice_total_amount_in_USD = 0)
        old_invoice_obj = old_invoice_obj.first()

        # Set new values in invoices
        # Set company values
        companybankobj = CompanyInvoiceBankDetail.objects.get(id = company_invoice_bank_detail)
        new_invoice_obj.company_invoice_bank_detail = companybankobj

        # Set invoice number
        # check currency
        if companybankobj.company_details.company_local_currency.id == invoice_currency_id:
            prefix = companybankobj.company_details.company_invoice_prefix_local_currency
            suffix = int(companybankobj.company_details.company_invoice_suffix_local_currency)+1
            new_invoice_obj.invoice_number = f"{prefix}-{suffix}"
            new_invoice_obj.prefix = prefix
            new_invoice_obj.suffix = suffix
            companybankobj.company_details.company_invoice_suffix_local_currency = suffix
            companybankobj.company_details.save()
            if companybankobj.company_details.company_local_currency.currency_iso == "INR":
                if new_invoice_obj.invoice_customer.cust_org_TAXVATNumber[:2] == '24':
                    new_invoice_obj.invoice_tax = '3'
                    new_invoice_obj.invoice_SGST_value = new_invoice_obj.invoice_subtotal_amount*0.09
                    new_invoice_obj.invoice_CGST_value = new_invoice_obj.invoice_subtotal_amount*0.09
                    new_invoice_obj.invoice_total_amount = new_invoice_obj.invoice_subtotal_amount + (new_invoice_obj.invoice_subtotal_amount*0.18)

                else:
                    new_invoice_obj.invoice_tax = '2'
                    new_invoice_obj.invoice_IGST_value = new_invoice_obj.invoice_subtotal_amount*0.18
                    new_invoice_obj.invoice_total_amount = new_invoice_obj.invoice_subtotal_amount + (new_invoice_obj.invoice_subtotal_amount*0.18)
        else:
            prefix = companybankobj.company_details.company_invoice_prefix_international_currency
            suffix = int(companybankobj.company_details.company_invoice_suffix_international_currency)+1
            new_invoice_obj.invoice_number = f"{prefix}-{suffix}"
            new_invoice_obj.prefix = prefix
            new_invoice_obj.suffix = suffix
            new_invoice_obj.invoice_tax = '1'
            new_invoice_obj.invoice_SGST_value = 0
            new_invoice_obj.invoice_CGST_value = 0
            new_invoice_obj.invoice_IGST_value = 0
            new_invoice_obj.invoice_total_amount = new_invoice_obj.invoice_subtotal_amount
            companybankobj.company_details.company_invoice_suffix_international_currency = suffix
            companybankobj.company_details.save()
        
        invoicerowobjlist = old_invoice_obj.invoicerow_set.all()
        for item in old_invoice_obj.invoice_project.all():
            new_invoice_obj.invoice_project.add(item)
        for item in invoicerowobjlist:
            new_invoice_obj.invoicerow_set.add(item)

        old_invoice_obj.invoice_project.clear()
        # Need to remove projects from Old invoice
        companybankobj.save()
        new_invoice_obj.save()
      
        return Response({"message":"Success","Invoice Number" : new_invoice_obj.invoice_number},status=status.HTTP_200_OK)


class DraftInvoiceRevert(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def post(self,request,project_id,draftinvoice_id):
        statuss = request.data.get('status')
        try:
            if statuss in ['Closed']:
                DraftInvoice.objects.filter(project_id = project_id,id = draftinvoice_id).delete()
                DraftInvoiceRow.objects.filter(draft_invoice_id = draftinvoice_id).delete()
                # Project.objects.filter(id = project_id).update(project_status = 'Closed')
                # ProjectGroup.objects.filter(project = project_id).update(project_group_status = 'Closed')
                ProjectCPIApprovedManager.objects.filter(project_id = project_id).delete()
                SupplierIdsMarks.objects.filter(project_id = project_id).delete()
                update_status(project_id, 'Closed', action='change-project-status',user=request.user)
                # return Response({"message":"Draft Invoice Successfully Reverted"},status=status.HTTP_200_OK)

            if statuss in ['Reconciled']:
                DraftInvoice.objects.filter(project_id = project_id,id = draftinvoice_id).delete()
                DraftInvoiceRow.objects.filter(draft_invoice_id = draftinvoice_id).delete()
                # Project.objects.filter(id = project_id).update(project_status = 'Reconciled')
                # ProjectGroup.objects.filter(project = project_id).update(project_group_status = "Reconciled")
                ProjectCPIApprovedManager.objects.filter(project_id = project_id).delete()
                update_status(project_id, 'Reconciled', action='change-project-status',user=request.user)

            return Response({"message":"Draft Invoice Successfully Reverted"},status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something Went Wrong"},status=status.HTTP_400_BAD_REQUEST)

    

class InvoiceListSendEmailMonthWiseAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data = request.data

        invoice_number = data.get("invoice_no")
        today_date = datetime.now().date()
        try:
            if invoice_number:
                invoice_obj = Invoice.objects.filter(invoice_number__in = invoice_number)
                client_contact_qs = ClientContact.objects.filter(customer_id = invoice_obj[0].invoice_customer)

                html_message = render_to_string('Invoice/invoice_month_wise_email_send.html', {'invoice_list':invoice_obj,'today_date':today_date})

                sendEmail = sendEmailSendgripAPIIntegration(
                    from_email = ('accounts@panelviewpoint.com', 'Accounts Team'), 
                    to_emails=list(client_contact_qs.values_list('client_email', flat=True)), 
                    cc_emails = 'ar@panelviewpoint.com' if settings.SERVER_TYPE == 'production' else 'tech@panelviewpoint.com', subject=f'Followup : Payment status - {client_contact_qs[0].customer_id.cust_org_name} {datetime.now().date()}', html_message=html_message)

                if sendEmail.status_code not in [200, 201]:
                    fail_reason = sendEmail.content
                    return Response(data={'message':'Invoice Send Email to Client Contacts not sent successfully', 'reason':fail_reason}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response(data={'message':'Invoice Send Email Sent successfully to Client Contacts'}, status=status.HTTP_201_CREATED)
            else:
                return Response({"error":"Invoice number is required.!"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error":"Mulitiply invoice customer not allowed!"}, status=status.HTTP_400_BAD_REQUEST)


class DraftInvoiceNotesAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, draft_invoice_id):

        draft_invoice_notes_obj = DraftInvoiceNotes.objects.filter(draft_invoice_id = draft_invoice_id).values(
            user = F('created_by__first_name'),
            user_type = F('created_by__emp_type'),
            note = F('notes'),
            date_time = F('created_at')
        ).order_by('-id')

        return Response(draft_invoice_notes_obj, status=status.HTTP_200_OK)


    def post(self, request, draft_invoice_id):
        
        try:
            for data in request.data:
                notes = data.get('notes')
                if notes not in ['', None]:
                    drft_inv_obj = DraftInvoiceNotes.objects.create(draft_invoice_id = draft_invoice_id, notes = notes, created_by = request.user)
                    EmployeeNotifications.objects.create(project_id = drft_inv_obj.draft_invoice.project.id, description = notes, created_for = drft_inv_obj.draft_invoice.project.project_manager, created_by = request.user)
                else:
                    pass
            
            return Response({"message":"Draft Invoice Notes Create Successfully.!"}, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Comment Notes field is required!"}, status=status.HTTP_400_BAD_REQUEST)




        

