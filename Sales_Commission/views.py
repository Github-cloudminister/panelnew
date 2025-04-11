from django.db.models import F
from Sales_Commission.models import *
from Invoice.models import *
from Sales_Commission.serializers import *

#------Rest-Frame-Work library--------
from rest_framework import viewsets, generics, status
from rest_framework.response import Response
# from rest_framework import status
from rest_framework.views import APIView
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


# Create your views here.

class SalesCommissionListView(generics.ListCreateAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        sales_person = self.request.GET.get('sales_person')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        queryset = Sales_Commission.objects.all().values(
            'id',
            'payment_date',
            'status',
            'total_commision_amount',
            sales_person_name = F('sales_person__first_name'),
            currency_iso = F('currency__currency_iso')
            )
        if sales_person:
            queryset = queryset.filter(sales_person = sales_person)
        
        if start_date:
            queryset = queryset.filter(payment_date__gte = start_date)

        if end_date:
            queryset = queryset.filter(payment_date__lte = end_date)
        
        return Response(queryset)


class InvoiceRowViewSet(viewsets.ModelViewSet):
    queryset = InvoiceRow.objects.all()
    serializer_class = salesCommisionInvoiceRowSerializer 

    def list(self, request,*args, **kwargs):
        InvoiceRow_obj = InvoiceRow.objects.all()
        project_number = self.request.GET.get('project_number',None)
        invoice_po_number = self.request.GET.get('invoice_po_number',None)
        
        if project_number:
            invoice_row_obj = InvoiceRow_obj.filter(row_project_number__project_number = project_number)

        elif invoice_po_number:
            invoice_row_obj = InvoiceRow_obj.filter(row_po_number = invoice_po_number)
        
        else:
            return Response({"error":"Please select atleast one.!"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = salesCommisionInvoiceRowSerializer(invoice_row_obj,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)



# ---------------------------- Sales_Commission and Sales_Commission_Rows crud data -------------------------
class Sales_CommissionViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Sales_Commission.objects.all()
    serializer_class = Sales_CommissionSerializer

    def create(self, request,*args, **kwargs):
        if request.data["status"] in ['Cancel','Booked','Live','Paused','Closed','Archived'] :
            return Response({"message":"Project status should be Reconciled , Ready for invoice, Ready for Approved , Invoiced "}, status=status.HTTP_400_BAD_REQUEST)
        else:
            for Sales_Commission_Row in request.data["Sales_Commission_Rows"]:
                Sales_Commission_obj = Sales_Commission_Rows.objects.filter(project_id = Sales_Commission_Row['project'])
                if Sales_Commission_obj.exists():
                    return Response({"message":"Project already created"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    sales_commition = Sales_Commission.objects.create(
                        sales_person_id = request.data["sales_person"],
                        commission_amount = request.data["commission_amount"],
                        total_commision_amount= request.data["total_commision_amount"],
                        currency_id = request.data["currency"],
                        payment_date= request.data["payment_date"],
                        status= request.data["status"],
                    )
                    for Sales_Commission_Row in request.data["Sales_Commission_Rows"]:
                        Sales_Commission_Rows.objects.create(
                            sales_commision = sales_commition,
                            project_id = Sales_Commission_Row['project'],
                            commission_row_amount = Sales_Commission_Row['commission_row_amount'],
                            invoice_amount = Sales_Commission_Row['invoice_amount'],
                            invoice_row_id = Sales_Commission_Row['invoice_row']
                            )
                       
                        
                return Response({"message":"data created successfully"}, status=status.HTTP_201_CREATED)        
    
    def list(self, request,*args, **kwargs):
            sales_commission_obj = Sales_Commission.objects.all()
            if request.GET['status']:
                sales_commission_obj = sales_commission_obj.filter(status = request.GET['status'])
            if request.GET['sales_person_id']:
                sales_commission_obj = sales_commission_obj.filter(sales_person_id = request.GET['sales_person_id'])
            # sales_commission_rows_obj = Sales_Commission_Rows.objects.filter()
            serializer = Sales_CommissionSerializer(sales_commission_obj,many=True)
            return Response(serializer.data,status=status.HTTP_200_OK)       
        

class SalesCommissionUpdateView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Sales_Commission.objects.all()
    serializer_class = Sales_CommissionSerializer

    def get(self, request,*args, **kwargs):
        sales_commission_obj = Sales_Commission.objects.filter(id = kwargs['id'])
        serializer = Sales_CommissionSerializer(sales_commission_obj,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)


    def put(self, request,*args, **kwargs):
        sales_commition = Sales_Commission.objects.filter(id = kwargs['id']).update(
            sales_person = request.data["sales_person"],
            commission_amount = request.data["commission_amount"],
            total_commision_amount = request.data["total_commision_amount"],
            currency_id = request.data["currency"],
            payment_date = request.data["payment_date"],
            status = request.data["status"],
        )
        for Sales_Commission_Row in request.data["Sales_Commission_Rows"]:
            obj = Sales_Commission_Rows.objects.filter(id =Sales_Commission_Row['Sales_Commission_Row_id'],sales_commision_id=kwargs['id']).update(
                invoice_amount = Sales_Commission_Row['invoice_amount']
                )
        return Response({"message":"data updated successfully"}, status=status.HTTP_200_OK)


class SalesCommissionRowsDeleteApi(viewsets.ModelViewSet):

    def destroy(self, request,*args, **kwargs):
        try:
            sales_commition = Sales_Commission_Rows.objects.get(id=self.kwargs['id']).delete()
            return Response({"message":"data Deleted successfully"}, status=status.HTTP_200_OK)
        except:
            return Response({"message":"data not Found"}, status=status.HTTP_200_OK)   
    


