from rest_framework import serializers
from Invoice.models import InvoiceRow
from Sales_Commission.models import *



class Sales_Commission_RowsSerializer(serializers.ModelSerializer):
    invoice_date = serializers.ReadOnlyField(source="invoice_row.invoice.invoice_date")
    project_number = serializers.ReadOnlyField(source="project.project_number")
    row_po_number = serializers.ReadOnlyField(source="invoice_row.row_po_number")
    class Meta:
        model = Sales_Commission_Rows
        fields = ['id','sales_commision','project','project_number','invoice_amount','row_po_number','invoice_date','commission_row_amount','invoice_row']

class Sales_CommissionSerializer(serializers.ModelSerializer):
    sales_commission_row_data = Sales_Commission_RowsSerializer(source='sales_commission_rows_set',many=True,read_only=True)

    class Meta:
        model = Sales_Commission
        fields = ['id','sales_person','commission_amount','total_commision_amount','currency','payment_date','status','sales_commission_row_data']

class salesCommisionInvoiceRowSerializer(serializers.ModelSerializer):
    sales_commission = serializers.SerializerMethodField()
    invoice_date = serializers.ReadOnlyField(source="invoice.invoice_date")
    project_no = serializers.ReadOnlyField(source="row_project_number.project_number")

    def get_sales_commission(self, instance):
        try:
            return instance.row_project_number.Sales_Commission_Rows
        except:
            return False
    class Meta:
        model = InvoiceRow
        fields = ["id","invoice", "project_group_number", "row_project_number",'project_no',"row_po_number","row_hsn_code","row_name","row_completes","row_cpi","row_total_amount","row_description", "sales_commission",'invoice_date']


class SalesCommissionRowsListSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField()

    def get_project(self,obj):
        return obj.project.project_number
    class Meta:
        model = Sales_Commission_Rows
        fields = ['id','sales_commision','project','commission_row_amount','invoice_amount','invoice_row']

class SalesCommissionListSerializer(serializers.ModelSerializer):
    sales_commission_row_data = SalesCommissionRowsListSerializer(source = 'sales_commission_rows_set', many=True)
    class Meta:
        model = Sales_Commission
        fields = ['id','sales_person','commission_amount','total_commision_amount','currency','payment_date','status','sales_commission_row_data']


