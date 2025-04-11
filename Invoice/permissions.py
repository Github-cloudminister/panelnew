from rest_framework import permissions

class UpdateInvoice(permissions.BasePermission):
    message = "You have not permission to update Invoice..!"

    def has_object_permission(self, request, view, obj):
        invoice_status = obj.invoice_status
        if invoice_status == "2":
            return False
        else:
            return True