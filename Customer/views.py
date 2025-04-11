from Logapp.views import customer_log
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.db.models.expressions import F
from knox.auth import TokenAuthentication
from Customer.models import *
from Customer.serializers import *
from Customer.permissions import *


class ClientDetailCustomerView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )

    def get(self, request, customer_id):

        customer_list = ClientContact.objects.filter(customer_id=customer_id, client_status=True)
        if customer_list:
            serializer = ClientContactSerializer(customer_list, many=True)
            return Response(serializer.data)
        else:
            return Response({'errors': 'No data found for provided Customer-ID..!'}, status=status.HTTP_404_NOT_FOUND)


class CustomerView(APIView):

    '''
        method to get the list of all Customer Organization objects.
    '''
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, CustomerPermission)
    serializer_class = CustomerSerializer

    def get(self, request):
        customer = request.GET.get('customer')
        customer_list = CustomerOrganization.objects.all().order_by("cust_org_name")
        if customer == "detail":
            customer_list = customer_list.only('id','cust_org_name','currency','sales_person_id').values(
                'id',
                'currency',
                'sales_person_id',
                'cpi_calculation_method',
                organization_name = F('cust_org_name'),
                bid_currency = F('currency'),
                invoice_currency = F('customer_invoice_currency'),
                country = F('cust_org_country'),
                company_detail_country = F('company_invoice_bank_detail__company_details__company_country')
            ).order_by("cust_org_name")
            return Response(customer_list, status=status.HTTP_200_OK)
        if request.user.emp_type == '6':
            customer_list = customer_list.filter(sales_person_id = request.user).order_by("cust_org_name")
        serializer = self.serializer_class(customer_list, many=True)
        return Response(serializer.data)

        '''
            method to Create the Customer Organization objects. 
        '''

    def post(self, request):
        if request.user.id != request.data['sales_person_id'] and request.user.emp_type in ['6']:
            return Response({'error':"You Can't Add Customer with Other Sales Person..!"},status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data.get('cust_org_country') != None:
                cust_data = serializer.save()
                if cust_data.cust_org_ship_to_address_1 == '':
                    cust_data.cust_org_ship_to_address_1 = cust_data.cust_org_address_1
                    cust_data.save()
                if cust_data.cust_org_ship_to_address_2 == '':
                    cust_data.cust_org_ship_to_address_2 = cust_data.cust_org_address_2
                    cust_data.save()
                if cust_data.cust_org_ship_to_city == '':
                    cust_data.cust_org_ship_to_city = cust_data.cust_org_city
                    cust_data.save()
                if cust_data.cust_org_ship_to_state == '':
                    cust_data.cust_org_ship_to_state = cust_data.cust_org_state
                    cust_data.save()
                if cust_data.cust_org_ship_to_country in ['', None]:
                    cust_data.cust_org_ship_to_country = cust_data.cust_org_country
                    cust_data.save()
                if cust_data.cust_org_ship_to_zip == '':
                    cust_data.cust_org_ship_to_zip = cust_data.cust_org_zip
                    cust_data.save()
                else:
                    cust_data.save()
                customer_log(serializer.data,'',cust_data.id,request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Customer Country field may not be blank..!'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerUpdateView(APIView):

    '''
        class to get a single instance of Customer Organization object and to update it.
    '''
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, CustomerUpdatePermission)
    serializer_class = CustomerUpdateSerializer

    def get_object(self, customer_id):

        try:
            return CustomerOrganization.objects.get(id=customer_id)
        except CustomerOrganization.DoesNotExist as e:
            return None

    def get(self, request, customer_id):

        instance = self.get_object(customer_id)
        customer = self.request.GET.get('customer')
        project_customer = self.request.GET.get('project-customer')
        if instance != None:
            if customer == 'detail':
                customer_obj = CustomerOrganization.objects.filter(id = instance.id).values(
                    organization_name = F('cust_org_name'),
                    address_1 = F('cust_org_address_1'),
                    address_2 = F('cust_org_address_2'),
                    city = F('cust_org_city'),
                    pincode = F('cust_org_zip'),
                    invoice_currency = F('customer_invoice_currency'),
                    country = F('cust_org_country'),
                    taxVAT_number = F('cust_org_TAXVATNumber'),
                    company_detail_country = F('company_invoice_bank_detail__company_details__company_country'),
                    ship_to_address_1 = F('cust_org_ship_to_address_1'),
                    ship_to_address_2 = F('cust_org_ship_to_address_2'),
                    ship_to_city = F('cust_org_ship_to_city'),
                    ship_to_pincode = F('cust_org_ship_to_zip'),
                    ship_to_country = F('cust_org_ship_to_country'),
                )
                return Response(customer_obj,status=status.HTTP_200_OK)
            if project_customer == "detail":
                customer_obj = CustomerOrganization.objects.only('id','cust_org_name').filter(id = instance.id).values('id',
                    organization_name = F('cust_org_name'),
                    invoice_currency = F('customer_invoice_currency'),
                    company_detail_country = F('company_invoice_bank_detail__company_details__company_country')
                )
                return Response(customer_obj,status=status.HTTP_200_OK)
            else:
                serializer = self.serializer_class(instance)
            return Response(serializer.data)
        else:
            return Response({'errors': 'No data found for provided Customer-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, customer_id):
        if request.user.id != request.data['sales_person_id'] and request.user.emp_type in ['6']:
            return Response({'error':"You Can't Add Customer with Other Sales Person..!"},status=status.HTTP_400_BAD_REQUEST)
        instance = self.get_object(customer_id)
        if instance != None:
            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid():
                if serializer.validated_data.get('cust_org_country') != None:
                    serializer.save()
                    customer_log('',serializer.data,instance.id,request.user)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Customer Country field may not be blank..!'}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'errors': 'No data found for provided Customer-ID..!'}, status=status.HTTP_404_NOT_FOUND)


class ClientContactView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, ClientContactPermission)
    serializer_class = ClientContactSerializer

    def get(self, request):

        client_list = ClientContact.objects.filter(client_status=True)
        serializer = self.serializer_class(client_list, many=True)
        return Response(serializer.data)

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientContactUpdateView(APIView):

    '''
        method to get the relevant object. 
    '''
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, ClientContactUpdatePermission)
    serializer_class = ClientContactSerializer

    def get_object(self, client_contact_id):

        try:
            return ClientContact.objects.get(id=client_contact_id, client_status=True)
        except ClientContact.DoesNotExist as e:
            return None

    def get(self, request, client_contact_id):

        instance = self.get_object(client_contact_id)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data)
        else:
            return Response({'errors': 'No data found for provided ClientContact-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, client_contact_id):

        data = request.data
        instance = self.get_object(client_contact_id)
        if instance != None:
            serializer = self.serializer_class(instance, data=data)
            if serializer.is_valid():
                serializer.save(modified_by=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'errors': 'No data found for provided ClientContact-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, client_contact_id):

        instance = self.get_object(client_contact_id)
        if instance != None:
            instance.client_status = False
            instance.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'errors': 'No data found for provided ClientContact-ID..!'}, status=status.HTTP_404_NOT_FOUND)


class CurrencyView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, CurrencyPermission)
    serializer_class = CurrencySerializer

    def get(self, request):

        client_list = Currency.objects.all()
        serializer = self.serializer_class(client_list, many=True)
        return Response(serializer.data)