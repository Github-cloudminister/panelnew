from rest_framework import permissions


class CountryPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["add_country",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False

class CountryUpdatePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["change_country",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False

class LanguagePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        code_name = ["add_language",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False

class LanguageUpdatePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        code_name = ["change_language",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False


class ProjectPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["add_project",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False

class ProjectUpdatePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["change_project",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False

class ProjectGroupPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["add_projectgroup",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False

class ProjectGroupUpdatePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["change_projectgroup",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False

class ProjectGroupSupplierPermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["add_projectgroupsupplier",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False

class ProjectGroupSupplierUpdatePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["change_projectgroupsupplier",]
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False