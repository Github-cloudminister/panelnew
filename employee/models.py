from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.contrib.auth.models import Group

from datetime import datetime, date


class Country(models.Model):

    # Fields
    country_code = models.CharField(max_length=3)
    country_name = models.CharField(max_length=80)
    theorem_country_id = models.CharField(max_length=250, null=True, blank=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-modified_at',)

    def __str__(self):
        return '{}'.format(self.country_name)


class EmployeeProfileManager(BaseUserManager):

    """ Manager for employee profiles """

    # Methods
    def create_user(self, email, password=None):
        """ Create a new employee profile """

        if not email:
            raise ValueError("User must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)
        return user

    def create_superuser(self, email, password):
        """ Create and save a new superuser with given credentials """

        user = self.create_user(email, password)
        user.is_admin = True
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class EmployeeProfile(AbstractBaseUser, PermissionsMixin):

    """ Database model for employees in the system """

    # choices
    emp_type = (
        ("1", "Project Manager"),
        ("2", "Bidding Manager"),
        ("3", "Senior Project Manager"),
        ("4", "Accountant Executive"),
        ("5", "Panel Manager"),
        ("6", "Sales Executive"),
        ("7", "Leadership"),
        ("8", "Affiliate Manager"),
        ("9", "Management Team"),
        ("10", "Enginex Supplier"),
        ("11", "Business Analyst"),
        ("12", "Tech Team"),
    )

    gender_choices = (
        ('1', 'Male'),
        ('2', 'Female'),
    )

    user_type_choices = (
        ('1', 'Internal'),
        ('2', 'External'),
    )
    
    # Fields
    email = models.EmailField(null=False, unique=True)
    first_name = models.CharField(max_length=50, null=False)
    last_name = models.CharField(max_length=50, null=False)
    password = models.CharField(max_length=100, null=False)
    gender = models.CharField(
        max_length=1, choices=gender_choices, default="1")
    emp_type = models.CharField(
        choices=emp_type, default="7", max_length=2)
    contact_number = models.CharField(max_length=15, null=True)
    date_of_birth = models.DateField(auto_now_add=True)
    date_of_joinig = models.DateField(auto_now_add=True, editable=True)
    address1 = models.CharField(max_length=100, null=False)
    address2 = models.CharField(max_length=100, null=False)
    city = models.CharField(max_length=50, null=False)
    state = models.CharField(max_length=20)
    country = models.ForeignKey(Country, null=True, on_delete=models.SET_NULL)
    zipcode = models.CharField(max_length=10,
                               validators=[RegexValidator(regex=r'^\d{4,10}$',
                                                          message="Zipcode/Postalcode invalid")])
    created_at = models.DateTimeField(auto_now_add=True, editable=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, related_name='created_by_employee')
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    user_type = models.CharField(max_length=1, choices=user_type_choices,default='1')
    source_id = models.CharField(max_length=5, null=True, blank=True) 

    objects = EmployeeProfileManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_lable):
        return True

    def full_name(self):
        return self.first_name + " " + self.last_name
    class Meta:
        ordering = ('-id',)

    def __str__(self):
        """ Return string representation of the employee """

        return '{} {}'.format(self.first_name.capitalize(), self.last_name.capitalize())
    


class UserTokenVerifyPasswordReset(models.Model):
    
    user = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='usertoken_passwdreset_qs')
    user_token = models.CharField(max_length=200)


class EmployeeTarget(models.Model):
    
    user = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE)
    target_ammount = models.DecimalField(max_digits=10, decimal_places=2)
    target_month = models.IntegerField()
    target_year = models.IntegerField()
    conversion = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)