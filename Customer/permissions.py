from rest_framework import permissions


class CustomerPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["add_customerorganization",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False


class CustomerUpdatePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["change_customerorganization",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False


class ClientContactPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["add_clientcontact",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False


class ClientContactUpdatePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["change_clientcontact",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False


class CurrencyPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["add_currency",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False


class CurrencyUpdatePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["change_currency",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False