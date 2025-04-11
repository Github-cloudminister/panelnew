from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from knox.auth import TokenAuthentication

# in-project imports
from CompanyBankDetails.models import *
from CompanyBankDetails.serializers import *

# Create your views here.
class CompanyInvoiceDataView(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CompanyInvoiceBankDetailSerializer
    queryset = CompanyInvoiceBankDetail.objects.all()
    lookup_field = 'id'


class CompanyDetailsDataView(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = CompanyDetailSerializer
    queryset = CompanyDetails.objects.all()
    lookup_field = 'id'