from rest_framework import permissions


class SupplierPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["add_supplierorganisation",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False


class SupplierUpdatePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["change_supplierorganisation",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False


class SupplierContactPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["add_suppliercontact",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False


class SupplierContactUpdatePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["change_suppliercontact",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False