from rest_framework import permissions


class UpdateEmployeeProfile(permissions.BasePermission):

    """ Allow employee to edit their own profile """

    def has_object_permission(self, request, view, obj):
        """ Check employee is trying to edit their own profile """

        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.id == request.user.id


class EmployeePermission(permissions.BasePermission):
    message = 'You have not permission to add employee..!'

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        code_name = ["add_employeeprofile", 'add_permission', 'change_permission', 'add_group', 'change_group']
        user_permission = request.user.groups.filter(permissions__codename__in=code_name)
        if len(user_permission) > 0:
            return True
        else:
            return False