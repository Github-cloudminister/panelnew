from rest_framework import serializers
from django.db.models import Sum
from Invoice.models import *
from Project.models import *
from Customer.models import *
from Surveyentry.models import *


class projectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id','project_number','project_name']

class InvoiceListSerializer(serializers.ModelSerializer):

    invoice_customer = serializers.SerializerMethodField(
        source='invoice_customer'
    )
    invoice_contact = serializers.SerializerMethodField(
            source='invoice_contact'
    )
    
    customer_currency = serializers.SerializerMethodField()
    invoice_project = projectListSerializer(many=True)
    
    def get_customer_currency(self, instance_obj):
        return instance_obj.invoice_customer.currency.id

    def get_invoice_customer(self, instance_obj):
        return instance_obj.invoice_customer.cust_org_name

    def get_invoice_contact(self, instance_obj):
        return instance_obj.invoice_contact.client_firstname + " " + instance_obj.invoice_contact.client_lastname

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "invoice_description", "invoice_po_number", "invoice_status",
            "invoice_total_amount", 'invoice_subtotal_amount', "invoice_customer", "invoice_contact", 'invoice_date', 
            'invoice_due_date', 'invoice_ship_to_address_enable', 'invoice_tax',
            'invoice_IGST_value', 'invoice_SGST_value', 'invoice_CGST_value', 
            'invoice_TDS_percentage', 'invoice_TDS_amount', 'customer_currency', 'invoice_project', 'invoice_currency', 'invoice_show_conversion_rate', 
            'invoice_conversion_rate', 'invoice_total_amount_in_USD', 'company_invoice_bank_detail'
        ]
        read_only_fields = fields


class CustomerOrganizationReconciledProjectSerializer(serializers.ModelSerializer):

    project_client_contact = serializers.CharField(source='project_client_contact_person')

    project_sales_person = serializers.SerializerMethodField(
        source='project_sales_person'
    )

    def get_project_sales_person(self, instance_obj):
        return instance_obj.project_sales_person.first_name + " " + instance_obj.project_sales_person.last_name
    
    class Meta:
        model = Project
        fields = [
                'id', 'project_customer', 'project_client_contact', 'project_number', 'project_name', 
                'project_type', 'project_revenue_month', 'project_revenue_year', 'project_sales_person',
        ]


class ProjectGroupInvoiceSerializer(serializers.ModelSerializer):

    project_group_completes = serializers.SerializerMethodField()
    project_group_total_amount = serializers.SerializerMethodField()
    project_number = serializers.CharField(source = 'project.project_number')
    po_number = serializers.CharField(source = 'project.project_po_number')

    def get_project_group_completes(self, obj):
        project_group_completes = RespondentDetail.objects.filter(project_group_number = obj.project_group_number, resp_status__in=["4","9"]).count(),
        return project_group_completes[0]

    def get_project_group_total_amount(self, obj):
        project_group_total_revenue = RespondentDetail.objects.filter(resp_status__in=["4","9"], project_group_number = obj.project_group_number).aggregate(Sum('project_group_cpi'))['project_group_cpi__sum']
        if project_group_total_revenue == None:
            project_group_total_revenue = 0
        return project_group_total_revenue

    class Meta:
        model = ProjectGroup
        fields = ['project_number','po_number','project_group_number','project_group_name','project_group_cpi', 'project_group_completes', 'project_group_total_amount']


class InvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "invoice_project", "invoice_description", "invoice_po_number", "invoice_status",
            "invoice_total_amount", 'invoice_subtotal_amount', "invoice_customer", "invoice_contact", 'invoice_date', 
            'invoice_due_date', 'invoice_ship_to_address_enable', 'invoice_tax',
            'invoice_IGST_value', 'invoice_SGST_value', 'invoice_CGST_value',
            'invoice_TDS_percentage', 'invoice_TDS_amount', 'invoice_show_stamp', 'invoice_currency', 'invoice_show_conversion_rate', 
            'invoice_conversion_rate', 'invoice_total_amount_in_USD', 'discount','subtotal_after_discount', 'company_invoice_bank_detail'
        ]
        extra_kwargs = {
            'invoice_number': {
                'read_only': True,
            },
            'invoice_project': {
                'read_only': True,
            },
            'invoice_description':{
                'required': False,
                'allow_null':True,
            },
            'invoice_po_number':{
                'required': False,
                'allow_null':True,
            },              
            'invoice_show_conversion_rate':{
                'required': False,
                'allow_null':True,
            },
            'invoice_conversion_rate':{
                'required': False,
                'allow_null':True,
            },
            'invoice_total_amount_in_USD':{
                'required': False,
                'allow_null':True,
            }, 
            'company_invoice_bank_detail':{
                'read_only': True,
                'allow_null': False,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                }
            }                   
        }


class InvoiceGetDataSerializer(serializers.ModelSerializer):

    invoice_rows = serializers.SerializerMethodField()

    def get_invoice_rows(self, obj):
        invoice_row_obj = InvoiceRow.objects.filter(invoice = obj)
        invoice_rows = []

        for invoice_row in invoice_row_obj:
            invoice_row_dict = {}

            invoice_row_dict['invoice_row_id']=invoice_row.id
            try:
                invoice_row_dict['project_group_number'] = invoice_row.project_group_number.project_group_number
            except:
                invoice_row_dict['project_group_number'] = ''
            # 'project_group_number': invoice_row.project_group_number.project_group_number,
            invoice_row_dict['row_name'] = invoice_row.row_name
            invoice_row_dict['row_completes'] = invoice_row.row_completes
            invoice_row_dict['row_cpi'] = invoice_row.row_cpi
            invoice_row_dict['row_total_amount'] = invoice_row.row_total_amount
            invoice_row_dict['row_description'] = invoice_row.row_description
            invoice_row_dict['row_hsn_code'] = invoice_row.row_hsn_code
            invoice_row_dict['row_po_number'] = invoice_row.row_po_number
            try:
                invoice_row_dict['project_number'] = invoice_row.row_project_number.project_number
            except:
                invoice_row_dict['project_number'] = ''

            invoice_rows.append(invoice_row_dict)

        return invoice_rows

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'invoice_description','invoice_po_number', 'invoice_customer',
            'invoice_contact', 'invoice_status', 'invoice_total_amount', 'invoice_subtotal_amount', 'invoice_date', 
            'invoice_due_date', 'invoice_ship_to_address_enable', 'invoice_tax', 
            'invoice_IGST_value', 'invoice_SGST_value', 'invoice_CGST_value', 
            'invoice_TDS_percentage', 'invoice_TDS_amount', 'invoice_rows' , 'invoice_show_stamp', 'invoice_currency', 'invoice_show_conversion_rate', 
            'invoice_conversion_rate', 'invoice_total_amount_in_USD','discount','subtotal_after_discount', 'company_invoice_bank_detail'
        ]
        extra_kwargs = {
            'invoice_number': {
                'read_only': True,
            },
            'invoice_customer': {
                'read_only': True,
            },
            'invoice_po_number': {
                'read_only': True,
            },
        }


class InvoiceUpdateStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'invoice_status',]
        extra_kwargs = {
            'invoice_number': {
                'read_only': True,
            },
        }


class InvoiceUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "invoice_description", "invoice_po_number", "invoice_status",
            "invoice_total_amount", 'invoice_subtotal_amount', "invoice_customer", "invoice_contact", 'invoice_date', 
            'invoice_due_date', 'invoice_ship_to_address_enable', 'invoice_tax',
            'invoice_IGST_value', 'invoice_SGST_value', 'invoice_CGST_value',
            'invoice_TDS_percentage', 'invoice_TDS_amount', 'invoice_show_stamp', 'invoice_currency', 'invoice_show_conversion_rate', 
            'invoice_conversion_rate', 'invoice_total_amount_in_USD','discount','subtotal_after_discount', 'company_invoice_bank_detail'
        ]
        read_only_fields = ['company_invoice_bank_detail']
        extra_kwargs = {
            'invoice_number': {
                'read_only': True,
            },
            # 'invoice_customer': {
            #     'read_only': True,
            # },
            'invoice_description':{
                'required': False,
                'allow_null':True,
            },
            'invoice_show_conversion_rate':{
                'required': False,
                'allow_null':True,
            },
            'invoice_conversion_rate':{
                'required': False,
                'allow_null':True,
            },
            'invoice_total_amount_in_USD':{
                'required': False,
                'allow_null':True,
            },
            'invoice_po_number':{
                'required': False,
                'allow_null':True,
            }
        }


class InvoiceRowUpdateSerializer(serializers.ModelSerializer):

    row_project_number = serializers.CharField(source='row_project_number.project_number', read_only=True)

    class Meta:
        model = InvoiceRow
        fields = ['id', 'row_description','row_completes', 'row_cpi','row_total_amount','row_project_number','row_po_number','row_hsn_code']

        extra_kwargs = {
            'row_po_number': {
                'required': False,
            },
            'row_hsn_code': {
                'required': False,
            }
        }

class InvoicePdfGetDataSerializer(serializers.ModelSerializer):
    invoice_customer = serializers.SerializerMethodField()
    invoice_contact = serializers.SerializerMethodField()
    invoice_rows = serializers.SerializerMethodField()
    customer_address = serializers.SerializerMethodField()
    shiping_address = serializers.SerializerMethodField()
    TAXnumber = serializers.SerializerMethodField()
    tax_choice = serializers.SerializerMethodField()
    customer_currency = serializers.SerializerMethodField()
    invoice_currency = serializers.SerializerMethodField()
    company_invoice_bank_detail = serializers.SerializerMethodField()
    
    def get_customer_currency(self, obj):
        currency_obj = obj.invoice_customer.currency
        customer_currency_data = {
            'iso':currency_obj.currency_iso,
            'id': currency_obj.id
        }
        return customer_currency_data

    def get_invoice_currency(self, obj):
        currency_obj = obj.invoice_currency
        currency_data = {
            'iso':currency_obj.currency_iso,
            'name': currency_obj.currency_name
        }
        return currency_data

    def get_tax_choice(self, obj):
        return obj.invoice_tax

    def get_TAXnumber(self, obj):
        vat_num = obj.invoice_customer.cust_org_TAXVATNumber
        return vat_num

    def get_invoice_customer(self, obj):
        return obj.invoice_customer.cust_org_name
    
    def get_invoice_contact(self, obj):
        return obj.invoice_contact.client_firstname + " " + obj.invoice_contact.client_lastname

    def get_invoice_rows(self, obj):
        invoice_row_obj = InvoiceRow.objects.filter(invoice = obj)

        invoice_rows = [{
            'invoice_row_id': invoice_row.id,
            'row_completes': invoice_row.row_completes,
            'row_cpi': invoice_row.row_cpi,
            'row_total_amount': invoice_row.row_total_amount,
            'row_description': invoice_row.row_description,
            'row_po_number': invoice_row.row_po_number
        } for invoice_row in invoice_row_obj]
        return invoice_rows

    def get_customer_address(self, obj):
        customer_address = {'address':[
                obj.invoice_customer.cust_org_address_1,
                obj.invoice_customer.cust_org_address_2,
            ],
            'city': obj.invoice_customer.cust_org_city,
            'state': obj.invoice_customer.cust_org_state,
            'country': obj.invoice_customer.cust_org_country, 
            'zip_code': obj.invoice_customer.cust_org_zip
        }
        return customer_address

    def get_shiping_address(self, obj):
        shiping_address = {'address':[
                obj.invoice_customer.cust_org_ship_to_address_1,
                obj.invoice_customer.cust_org_ship_to_address_2,
            ],
            'city': obj.invoice_customer.cust_org_ship_to_city,
            'state': obj.invoice_customer.cust_org_ship_to_state,
            'country': obj.invoice_customer.cust_org_ship_to_country, 
            'zip_code': obj.invoice_customer.cust_org_ship_to_zip
        }
        return shiping_address

    def get_company_invoice_bank_detail(self, obj):
        company_invoice_bank_detail = obj.company_invoice_bank_detail
        
        company_invoice_bank_details = {
            'account_number': company_invoice_bank_detail.account_number,
            'ifsc_code': company_invoice_bank_detail.ifsc_code,
            'bank_name': company_invoice_bank_detail.bank_name,
            'bank_address': company_invoice_bank_detail.bank_address,
            'swift_code': company_invoice_bank_detail.swift_code,
            'account_type': company_invoice_bank_detail.get_account_type_display(),
            'company_name': company_invoice_bank_detail.company_details.company_name,
            'company_contact_number': company_invoice_bank_detail.company_details.company_contact_number,
            'company_address1': company_invoice_bank_detail.company_details.company_address1,
            'company_address2': company_invoice_bank_detail.company_details.company_address2,
            'company_city': company_invoice_bank_detail.company_details.company_city,
            'company_state': company_invoice_bank_detail.company_details.company_state,
            'company_country': company_invoice_bank_detail.company_details.company_country.country_name,
            'company_country_code': company_invoice_bank_detail.company_details.company_country.country_code,
            'company_zipcode': company_invoice_bank_detail.company_details.company_zipcode,
            'company_email': company_invoice_bank_detail.company_details.company_email,
            'company_website': company_invoice_bank_detail.company_details.company_website,
            'company_tax_number': company_invoice_bank_detail.company_details.company_tax_number,
            'company_cin_number': company_invoice_bank_detail.company_details.company_cin_number,
            'company_pan_number': company_invoice_bank_detail.company_details.company_pan_number,
            'company_iban_number': company_invoice_bank_detail.company_iban_number,
            'company_routing_number': company_invoice_bank_detail.company_routing_number,
        }

        return company_invoice_bank_details

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'invoice_description','invoice_po_number', 'invoice_customer',
            'invoice_contact', 'invoice_status', 'invoice_total_amount', 'invoice_date', 
            'invoice_due_date', 'invoice_ship_to_address_enable', 'invoice_tax', 
            'invoice_IGST_value', 'invoice_SGST_value', 'invoice_CGST_value', 
            'invoice_TDS_percentage', 'invoice_TDS_amount', 'invoice_rows', 
            'TAXnumber', 'invoice_subtotal_amount',
            'customer_address','shiping_address', 'tax_choice', 'customer_currency', 'invoice_currency', 'invoice_show_stamp','invoice_show_conversion_rate','invoice_total_amount_in_USD','invoice_conversion_rate','discount','subtotal_after_discount', 'company_invoice_bank_detail'
        ]
        extra_kwargs = {
            'invoice_number': {
                'read_only': True,
            },
            'invoice_customer': {
                'read_only': True,
            },
            'invoice_po_number': {
                'read_only': True,
            },
        }


class InvoiceRowSerilaizer(serializers.ModelSerializer):

    row_project_number = serializers.CharField(source='row_project_number.project_number', read_only=True, allow_null=True)

    class Meta:
        model = InvoiceRow
        fields = ['invoice','row_description','row_completes','row_cpi', 'row_total_amount','row_project_number','row_po_number','row_hsn_code']

        extra_kwargs = {
            'row_po_number': {
                'required': True,
            },
            'row_hsn_code': {
                'read_only': True,
            }
        }


class InvoiceExcelSerializer(serializers.ModelSerializer):
    invoice_status = serializers.CharField(source='get_invoice_status_display')
    invoice_customer = serializers.CharField(source='invoice_customer.cust_org_name')
    invoice_contact = serializers.CharField(source='get_invoice_contact_full_name')
    invoice_currency = serializers.CharField(source='invoice_currency.currency_iso')
    invoice_project = serializers.SerializerMethodField()
    invoice_date = serializers.DateField(format="%d-%m-%Y", read_only=True)
    invoice_due_date = serializers.DateField(format="%d-%m-%Y", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "invoice_status", "invoice_number", "invoice_project", "invoice_description", "invoice_customer", "invoice_contact", "invoice_date", "invoice_due_date", "invoice_currency", "invoice_total_amount", "invoice_po_number",
        ]

    def get_invoice_project(self, obj):
        return ','.join(obj.invoice_project.all().values_list('project_number', flat=True))



class InvoiceNestedProjectSerializer(serializers.ModelSerializer):
    invoice_status = serializers.SerializerMethodField()
    invoice_currency = serializers.CharField(source = 'invoice_currency.currency_iso')

    class Meta:
        model = Invoice
        fields = ['invoice_status','invoice_number','invoice_date','invoice_due_date','invoice_total_amount','invoice_currency']

    def get_invoice_status(self, instance_obj):
        return instance_obj.get_invoice_status_display()


class InvoiceByProjectXLSXSerializer(serializers.ModelSerializer):
    project_customer = serializers.CharField(source = 'project_customer.cust_org_name')
    invoice_set = InvoiceNestedProjectSerializer(many=True)


    class Meta:
        model = Project
        fields = ['project_number','project_name','id','project_customer','invoice_set']


    
class DraftInvoiceRowSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DraftInvoiceRow
        fields = ['id', 'draft_invoice', 'po_number', 'description', 'bid_cpi','cpi', 'completes', 'total','bid_total']


class DraftInvoiceRowListSerializer(serializers.ModelSerializer):
    project_number = serializers.CharField(source = 'draft_invoice.project.project_number')
    project_group_cpi = serializers.FloatField(source = 'cpi')
    project_group_completes = serializers.IntegerField(source = 'completes')
    project_group_total_amount = serializers.FloatField(source = 'total')
    
    class Meta:
        model = DraftInvoiceRow
        fields = ['project_number', 'po_number', 'description', 'project_group_cpi', 'project_group_completes', 'project_group_total_amount']


class DraftInvoiceRowListSerializer(serializers.ModelSerializer):
    project_number = serializers.CharField(source = 'draft_invoice.project.project_number')
    project_group_cpi = serializers.FloatField(source = 'cpi')
    project_group_completes = serializers.IntegerField(source = 'completes')
    project_group_total_amount = serializers.FloatField(source = 'total')
    
    class Meta:
        model = DraftInvoiceRow
        fields = ['project_number', 'po_number', 'description', 'project_group_cpi', 'project_group_completes', 'project_group_total_amount']



class DraftInvoiceRowsListByProjectSerializer(serializers.ModelSerializer):
    draft_invoice_row_id = serializers.IntegerField(source = 'id')
    draft_invoice_id = serializers.IntegerField(source = 'draft_invoice.id')
    project_id = serializers.IntegerField(source = 'draft_invoice.project.id')
    project_number = serializers.CharField(source = 'draft_invoice.project.project_number')
    
    class Meta:
        model = DraftInvoiceRow
        fields = ['draft_invoice_row_id', 'draft_invoice_id', 'po_number', 'description', 'bid_cpi','cpi', 'completes', 'total','project_id','project_number']



class DraftInvoiceSerializer(serializers.ModelSerializer):
    invoice_rows = DraftInvoiceRowSerializer(many=True, source='draftinvoicerow_set', required=False)
    project_status = serializers.CharField(source='project.project_status', read_only=True)
    customer_name = serializers.CharField(source='invoice_to_customer.cust_org_name', read_only=True)
    project_number = serializers.CharField(source='project.project_number', read_only=True)
    reconciliation_date = serializers.DateTimeField(source='created_at', format="%d-%m-%Y", read_only=True)
    company_country = serializers.CharField(source="invoice_to_customer.company_invoice_bank_detail.company_details.company_country.id",read_only=True)
    invoice_total = serializers.SerializerMethodField()

    def get_invoice_total(self, obj):
        # invoice_total = round(obj.invoice_total, 5) 
        return round(obj.invoice_total, 2)

    class Meta:
        model = DraftInvoice
        fields = ['id', 'project', 'project_number', 'reconciliation_date', 'customer_name', 'project_status', 'draft_approved', 'BA_approved', 'Accountant_approved', 'approval_note', 'confirm_email_file','invoice_total','bid_total','invoice_rows','invoice_to_customer','notes_from_pm','conversion_rate','cpi_calculation_method','invoice_currency','company_country','bid_currency']

        extra_kwargs = {
            'draft_approved':{
                'read_only':True
            },
            'invoice_to_customer':{
                'required':True
            },
            'notes_from_pm':{
                'required':True
            },
            'conversion_rate':{
                'required':False
            },
            'cpi_calculation_method':{
                'required':False
            },
            'invoice_currency':{
                'required':True
            }
        }

    def create(self, validated_data):
        draft_invoice_rows = validated_data.pop('draftinvoicerow_set')
        instance = super().create(validated_data)
        DraftInvoiceRow.objects.filter(draft_invoice=instance).delete()
        draft_invoice_total = 0
        draft_invoice_bid_total = 0
        for draft_invoice_dtl in draft_invoice_rows:
            DraftInvoiceRow.objects.create(draft_invoice=instance, **draft_invoice_dtl)
            draft_invoice_total+=draft_invoice_dtl['total']
            draft_invoice_bid_total+=draft_invoice_dtl['bid_total']
        instance.created_by = self.context['user']
        instance.invoice_total = draft_invoice_total
        instance.bid_total = draft_invoice_bid_total
        instance.save()
        return instance

    def update(self, instance, validated_data):
        draft_invoice_rows = validated_data.pop('draftinvoicerow_set')
        instance = super().update(instance, validated_data)
        DraftInvoiceRow.objects.filter(draft_invoice=instance).delete()
        draft_invoice_total = 0
        draft_invoice_bid_total = 0
        for draft_invoice_dtl in draft_invoice_rows:
            draft_invoice_dtl.pop('draft_invoice','')
            DraftInvoiceRow.objects.create(draft_invoice=instance, **draft_invoice_dtl)
            draft_invoice_total+=draft_invoice_dtl['total']
            draft_invoice_bid_total +=draft_invoice_dtl['bid_total']
        instance.modified_by = self.context['user']
        instance.invoice_total = draft_invoice_total
        instance.bid_total = draft_invoice_bid_total
        instance.save()
        return instance


class DraftInvoicesByCustomerIDSerializer(serializers.ModelSerializer):

    draft_invoice_id = serializers.CharField(source='id')
    project_id = serializers.CharField(source='project')

    class Meta:
        model = DraftInvoice
        fields = ['draft_invoice_id', 'project_id','draft_approved']


class DraftInvoicesAndRowsByIDsSerializer(serializers.ModelSerializer):
    draft_invoice_rows = DraftInvoiceRowSerializer(many=True, source='draftinvoicerow_set')
    draft_invoice_id = serializers.CharField(source='id')
    project_id = serializers.CharField(source='project')

    class Meta:
        model = DraftInvoice
        fields = ['draft_invoice_id', 'project_id','draft_approved','draft_invoice_rows','conversion_rate']


class DraftInvoiceUpdateFileUploadSerializer(serializers.ModelSerializer):

    project_status = serializers.CharField(source='project.project_status', read_only=True)

    class Meta:
        model = DraftInvoice
        fields = ['id', 'project_status', 'confirm_email_file']

        extra_kwargs = {
            'id':{
                'read_only':True
            },
            'confirm_email_file':{
                'required':True
            }
        }



class InvoicePaymentReminderEmailViewSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvoicePaymentReminderEmail
        fields = ['invoices','customer', 'added_by','id']

        extra_kwargs = {
            'id':{
                'read_only':True
            }
        }

class DestroyInvoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "invoice_status",
        ]
        read_only_fields = fields
