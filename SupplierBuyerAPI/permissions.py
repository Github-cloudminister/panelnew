from rest_framework.permissions import BasePermission,SAFE_METHODS
from django.core.exceptions import ObjectDoesNotExist
from Supplier.models import SubSupplierOrganisation, SupplierOrganisation


class SupplierOrgSecretKeyPermission(BasePermission):
    #Authentication for Supplier verification
    #Authorization for Sub Supplier verification

    def has_permission(self, request, view):
        if 'Authentication' in request.headers:
            try:
                SupplierOrganisation.objects.get(supplier_buyer_apid__secret_key=request.headers['authentication'])
                return True
            except ObjectDoesNotExist:
                return False
        elif 'Authorization' in request.headers:
            try:
                SubSupplierOrganisation.objects.get(sub_supplier_buyer_apid__secret_key=request.headers['Authorization'])
                return True
            except ObjectDoesNotExist:
                return False
        else:
            return False