from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from ClientSupplierInvoicePayment.models import ClientPaymentReceipt, ClientPaymentReceiptInvoiceLinking
from ClientSupplierInvoicePayment.serializers import ClientPaymentReceiptSerializer
from Invoice.models import Invoice


# Create your views here.


class ClientPaymentReceiptRetrieveAPI(generics.RetrieveUpdateAPIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ClientPaymentReceiptSerializer
    queryset = ClientPaymentReceipt.objects.all()

    def get_object(self, id):

        try:
            return ClientPaymentReceipt.objects.get(id=id)
        except ClientPaymentReceipt.DoesNotExist:
            return None
        
    def get(self, request, id):

        instance = self.get_object(id)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data)
        else:
            return Response({'error': 'No data found for the provided ProjectGroup-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, id):

        instance = self.get_object(id)
        if instance != None:
            # instance.payment_receipt_amount = 
            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid():
                client_payment_obj = serializer.save()
            # return Response(serializer.data)
        receipt_inv_link = request.data.get('receiptinvoicelinking')

        invoices_not_sent = []
        try:
            for item in receipt_inv_link:
                invoice_obj = Invoice.objects.get(id=item['invoice'])
                currency = invoice_obj.invoice_currency
                instance.currency = currency
                instance.save()
                if invoice_obj.invoice_status == '2':
                    invoice_obj.invoice_status = '3'
                    invoice_obj.save()
                    ClientPaymentReceiptInvoiceLinking.objects.create(client_payment_receipt_id=instance.id, invoice=invoice_obj, payment_received_amount=item['payment_received_amount'], tds_amount=item['tds_amount'])
                else:
                    ClientPaymentReceiptInvoiceLinking.objects.filter(client_payment_receipt_id=instance.id, invoice=invoice_obj).update(payment_received_amount=item['payment_received_amount'], tds_amount=item['tds_amount'])
                    invoices_not_sent.append(invoice_obj.id)
        except Invoice.DoesNotExist:
            return Response({'error': 'One or more invoice is not found, please insert correct invoice ID'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        return Response({'message': 'Client Payment Receipt & their Invoice Links whose Invoice IDs Sent created successfully', 'Payment Receipt Links not created of following Invoice IDs due to Invoices not Sent':set(invoices_not_sent)}, status=status.HTTP_201_CREATED)


class ClientPaymentReceiptCreateListAPI(generics.ListCreateAPIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ClientPaymentReceiptSerializer
    queryset = ClientPaymentReceipt.objects.all()


    def get_queryset(self):

        customer = self.request.GET.get('customer')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        query_set = ClientPaymentReceipt.objects.all()

        if customer not in ['',None]:
            query_set = query_set.filter(customer_org = customer)

        if start_date not in ['',None]:
            query_set = query_set.filter(payment_receipt_date__gte = start_date)

        if end_date not in ['',None]:
            query_set = query_set.filter(payment_receipt_date__lte = end_date)

        return query_set


    def post(self, request):
        aa= super().post(request)

        receipt_inv_link = request.data.get('receiptinvoicelinking')


        if not receipt_inv_link:
            return Response({'error': 'ClientPaymentReceipt Invoice Linking rows cannot be blank'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        invoices_not_sent = []
        try:
            for item in receipt_inv_link:
                invoice_obj = Invoice.objects.get(id=item['invoice'])
                currency = invoice_obj.invoice_currency
                ClientPaymentReceipt.objects.filter(id=aa.data['id']).update(currency = currency)

                if invoice_obj.invoice_status == '2':
                    invoice_obj.invoice_status = '3'
                    invoice_obj.save()
                    ClientPaymentReceiptInvoiceLinking.objects.create(client_payment_receipt_id=aa.data['id'], invoice=invoice_obj, payment_received_amount=item['payment_received_amount'], tds_amount=item['tds_amount'])
                else:
                    invoices_not_sent.append(invoice_obj.id)
        except Invoice.DoesNotExist:
            return Response({'error': 'One or more invoice is not found, please insert correct invoice ID'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        return Response({'message': 'Client Payment Receipt & their Invoice Links whose Invoice IDs Sent created successfully', 'Payment Receipt Links not created of following Invoice IDs due to Invoices not Sent':set(invoices_not_sent)}, status=status.HTTP_201_CREATED)
