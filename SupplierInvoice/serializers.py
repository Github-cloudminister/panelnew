# ********* Django Libraries **********
from django.db.models import *
from django.db.models.functions import *

# ********* REST API Libraries **********
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

# ********* in-project imports **********
from SupplierInvoice.models import *
from Surveyentry.models import RespondentDetailsRelationalfield


class SupplierInvoiceListSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source='supplier_org.supplier_name')
    currency_iso = serializers.ReadOnlyField(source='currency.currency_iso')
    inv_status_display = serializers.SerializerMethodField()
    company = serializers.ReadOnlyField(source = "company.company_name")
    total_payable_amount = serializers.ReadOnlyField(source = "supplierinvoicepayment.total_payable_amount")

    class Meta:
        model = SupplierInvoice
        fields = ['id', 'supplier_org', 'company','supplier_name', 'invoice_number','invoice_status', 'inv_status_display', 'invoice_date', 'due_date', 'conversion_rate','total_invoice_amount','currency','currency_iso', 'taxable_value', 'tax_amount','total_from_invoice_amount','total_payable_amount']

    def get_inv_status_display(self, obj):
        return obj.get_invoice_status_display()


class SupplierInvoiceSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source='supplier_org.supplier_name')

    class Meta:
        model = SupplierInvoice
        fields = ['id', 'supplier_org', 'supplier_name', 'invoice_number', 'invoice_date']
        validators = [
            UniqueTogetherValidator(
                queryset=SupplierInvoice.objects.all(),
                fields=['supplier_org', 'invoice_number'],
                message="The fields supplier_org, invoice_number must make a unique set."
            )
        ]

class SupplierInvoiceStatsSerializer(serializers.ModelSerializer):
    supplier_id = serializers.ReadOnlyField(source='source.id')
    supplier_name = serializers.ReadOnlyField(source='source.supplier_name')
    project_name = serializers.ReadOnlyField(source='project.project_name')
    project_number = serializers.ReadOnlyField(source='project.project_number')

    stats = serializers.SerializerMethodField()
    class Meta:
        model = RespondentDetailsRelationalfield
        fields = ['supplier_id', 'supplier_name', 'project_name', 'project_number','stats']

    def get_stats(self, obj):
        resp_detail_obj = RespondentDetailsRelationalfield.objects.filter(id=obj.id).aggregate(completes = Count('respondent'), cpi=Avg('respondent__supplier_cpi'), expense = Sum('respondent__supplier_cpi'))
        return resp_detail_obj



class SupplierInvoiceRowRetrieveUpdateSerializer(serializers.ModelSerializer):
    project_number = serializers.ReadOnlyField(source='project.project_number')

    class Meta:
        model = SupplierInvoiceRow
        fields = ['id', 'project_number', 'invoice_received','invoiced_completes','invoiced_cpi','total_amount','cpi','completes']


class SupplierInvoiceRetrieveUpdateSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source='supplier_org.supplier_name')
    supplier_cpi_calculation_method = serializers.ReadOnlyField(source='supplier_org.cpi_calculation_method')
    inv_status_display = serializers.SerializerMethodField()
    supplier_inv_rows = SupplierInvoiceRowRetrieveUpdateSerializer(many=True,required=False, source='supplierinvoicerow_set')
    company_name = serializers.SerializerMethodField()

    def get_company_name(self, obj):
        
        if obj.company in ['', None]:
            return ""
        else:
            return obj.company.company_name

    class Meta:
        model = SupplierInvoice
        fields = ['id', 'supplier_org','company','company_name', 'supplier_name', 'invoice_number', 'invoice_date', 'due_date', 'conversion_rate','total_invoice_amount','currency', 'invoice_status','inv_status_display','supplier_inv_rows', 'taxable_value', 'tax_amount','supplier_invoice_file','total_from_invoice_amount','supplier_cpi_calculation_method','clarification']
    
    extra_kwargs = {
        'company_name':{
            'read_ony':True
        }
    }

    def get_inv_status_display(self, obj):
        return obj.get_invoice_status_display()


    def update(self, instance, validated_data):
        if validated_data.get('supplier_org'):
            validated_data.pop('supplier_org')
        suppinv_row_serialzed_list = validated_data.pop('supplierinvoicerow_set')
        suppinv_row_list = self.context['request'].data.pop('supplier_inv_rows')
        
        supplier_inv_qs = SupplierInvoice.objects.filter(id=instance.id)
        supplier_inv_qs.update(**validated_data)

        for suppinv_row_serlzed_dict, suppinv_row_dict in zip(suppinv_row_serialzed_list, suppinv_row_list):
            SupplierInvoiceRow.objects.filter(id=suppinv_row_dict['id']).update(supplier_invoice = supplier_inv_qs.first(), **suppinv_row_serlzed_dict)

        return supplier_inv_qs[0]


class SupplierInvoiceRowListSerializer(serializers.ModelSerializer):
    project_number = serializers.ReadOnlyField(source='project.project_number')

    class Meta:
        model = SupplierInvoiceRow
        fields = ['id','supplier_org', 'project_number', 'invoice_received','cpi','completes']