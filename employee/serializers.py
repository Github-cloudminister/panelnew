from django.core.validators import RegexValidator
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from employee.models import EmployeeProfile


class EmployeeProfileSerializer(serializers.ModelSerializer):

    date_of_joining = serializers.DateField(
        source='date_of_joinig',
    )
    zipcode_postalcode = serializers.CharField(
        source='zipcode'
    )
    
    country = serializers.CharField(
        source='country.country_name'
    )

    class Meta:
        model = EmployeeProfile
        fields = [
            "id", "first_name", "last_name", 'gender', "email", "emp_type", "contact_number", 'date_of_birth',
            "date_of_joining", "address1", "address2", "city", "state", "country", "zipcode_postalcode",
            "is_active",
        ]

class EmployeeRegisterSerializer(serializers.ModelSerializer):

    first_name = serializers.CharField(
        required=True,
        style={'input_type': 'text', 'placeholder': 'John'}
    )
    last_name = serializers.CharField(
        required=True,
        style={'input_type': 'text', 'placeholder': 'Smith'}
    )
    email = serializers.CharField(
        required=True,
        style={'input_type': 'email', 'placeholder': 'john@mail.com'}
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password', 'placeholder': '********'}
    )
    date_of_birth = serializers.DateField(
        required=True,
    )
    date_of_joining = serializers.DateField(
        required=True,
        source='date_of_joinig',
    )
    # contact_number = serializers.CharField(
    #     validators=[UniqueValidator(queryset=EmployeeProfile.objects.all()),
    #                 RegexValidator(regex=r'^\+?1?\d{9,13}$',
    #                         message="Contact number must be in the format of '+123456789'. Up to 13 digits allowed.")],
    #     required=True,
    #     style={'input_type': 'number', 'placeholder': '+911234567890'}
    # )
    zipcode_postalcode = serializers.CharField(
        source='zipcode',
        style={'input_type': 'text', 'placeholder': '110321'}
    )
    state = serializers.CharField(
        required=True,
        style={'input_type': 'text', 'placeholder': 'Gujarat'}
    )
    city = serializers.CharField(
        required=True,
        style={'input_type': 'text', 'placeholder': 'Ahmedabad'}
    )
    address1 = serializers.CharField(
        required=True,
        style={'input_type': 'text',
               'placeholder': 'ex:Flat no, Door no, plot no, etc.,'}
    )
    address2 = serializers.CharField(
        required=True,
        style={'input_type': 'text',
               'placeholder': 'ex:Building name, Area name, Place name, etc.,'}
    )

    class Meta:
        model = EmployeeProfile
        fields = [
            "id", "first_name", "last_name", "gender", "email", "password", "emp_type", "contact_number",
            "date_of_birth", "date_of_joining", "address1", "address2", "city", "state", "country",
            "zipcode_postalcode",
        ]

class EmployeeUpdateSerializer(serializers.ModelSerializer):

    zipcode_postalcode = serializers.CharField(
        source='zipcode'
    )
    date_of_birth = serializers.DateField(
        required=True,
    )
    # contact_number = serializers.CharField(
    #     validators=[UniqueValidator(queryset=EmployeeProfile.objects.all()),
    #                 RegexValidator(regex=r'^\+?1?\d{9,13}$',
    #                         message="Contact number must be in the format of '+123456789'. Up to 13 digits allowed.")],
    # )

    class Meta:
        model = EmployeeProfile
        fields = [
            "id", "first_name", "last_name", 'gender', "emp_type", 'date_of_birth', "contact_number",
            "address1", "address2", "city", "state", "country", "zipcode_postalcode"
        ]

class EmployeePasswordSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password', 'placeholder': '********'})

    class Meta:
        model = EmployeeProfile
        fields = ['id', 'password']

class GroupPermissionViewSerializer(serializers.ModelSerializer):
    
    permissions = serializers.SerializerMethodField()

    def get_permissions(self, perm):
        return perm.permissions.values('name')

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']

class GroupPermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']

class EmployeeWithPermission(serializers.ModelSerializer):

    employee_name = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()

    def get_groups(self, obj):
        return obj.groups.values('name')

    def get_employee_name(self, obj):
        return obj.first_name.capitalize() + " " + obj.last_name.capitalize()

    class Meta:
        model = EmployeeProfile
        fields = ['id', 'email', 'employee_name', 'groups']

class EmployeeAssignPermission(serializers.ModelSerializer):

    employee_name = serializers.SerializerMethodField()

    def get_employee_name(self, obj):
        return obj.first_name.capitalize() + " " + obj.last_name.capitalize()

    class Meta:
        model = EmployeeProfile
        fields = ['email', 'employee_name', 'groups']
        extra_kwargs = {
            'email': {
                'required': True,
            },
            'groups': {
                'required': True,
            },
            'employee_name': {
                'read_only': True,
            }
        }

class PermissionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Permission
        fields = '__all__'