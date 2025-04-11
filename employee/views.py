# ****************** Django's Libraries *******************
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import login
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission
from django.db.models import F, Sum, Case, When, DecimalField, Count, Q
from django.utils import timezone
# ******************** Serializers and Models *****************

from Bid.models import Bid
from Invoice.models import DraftInvoice, InvoiceRow
from Logapp.views import employee_login_Log
import Project
from Project.models import ProjectGroup, ProjectGroupSupplier, Project
from Surveyentry.models import RespondentDetail, RespondentDetailsRelationalfield
from Surveyentry.custom_function import get_object_or_none
from employee.models import EmployeeProfile, EmployeeTarget
from employee.permissions import EmployeePermission, UpdateEmployeeProfile
from employee.serializers import EmployeeAssignPermission, EmployeePasswordSerializer, EmployeeProfileSerializer, EmployeeRegisterSerializer, EmployeeUpdateSerializer, EmployeeWithPermission, GroupPermissionSerializer, GroupPermissionViewSerializer, PermissionSerializer

# ****************** Rest Libraries **********************
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import IsAuthenticated

# ******************* knox ***************************
from knox.auth import TokenAuthentication
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView

# ******************* third party libraries ***************************
import random
import string
from datetime import date, timedelta

class EmployeeListView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        emps = EmployeeProfile.objects.filter(is_superuser = False, user_type = '1').exclude(emp_type = '10')
        if request.GET.get('type') not in ['',None]:
            emps = emps.filter(emp_type = request.GET.get('type'))
        
        if request.GET.get('emp') == 'detail':
            emps = emps.values('id','first_name','last_name','emp_type')
            return Response(emps,status=status.HTTP_200_OK)
        
        emps = emps.values("id","first_name","last_name","gender","email","emp_type","contact_number","date_of_birth","address1","address2","city","state","is_active",country_name = F('country__country_name'))
        return Response(emps,status=status.HTTP_200_OK)

class EmployeeRegisterApiView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, EmployeePermission)
    serializer_class = EmployeeRegisterSerializer

    def post(self, request, *args, **kwargs):

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                if not(serializer.validated_data.get('date_of_joinig') >= date.today()):
                    if not(serializer.validated_data.get('date_of_birth') >= date.today()):
                        if serializer.validated_data.get('country') != None:
                            user = serializer.save(created_by=request.user)
                            groups = Group.objects.all()
                            permissions_list = ["add_employeeprofile", "change_employeeprofile", "delete_employeeprofile"]
                            if serializer.validated_data.get('emp_type') in ["7","9"]:
                                user.groups.set(groups)
                            else:
                                user.groups.set(groups.exclude(permissions__codename__in=permissions_list))
                            user.date_of_birth = serializer.validated_data['date_of_birth']
                            user.date_of_joinig = serializer.validated_data['date_of_joinig']
                            user.password = make_password(
                                self.request.data["password"])
                            user.is_staff = True
                            user.save()
                            # check with creating new employee
                            token = AuthToken.objects.create(user)[1]
                            return Response({'success': 'You are registered successfully..!', 'token': token}, status=status.HTTP_201_CREATED)
                        else:
                            return Response({'error': 'Country field may not be blank..!'}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({'error': 'Date of Birth should be less than current date..!'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'error': 'Joining Date should be less than current date..!'}, status=status.HTTP_400_BAD_REQUEST)
            except:
                return Response({'error': 'Email already exists..!'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EmployeeUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (UpdateEmployeeProfile, IsAuthenticated,)
    serializer_class = EmployeeUpdateSerializer

    def get_object(self, emp_id):

        try:
            return EmployeeProfile.objects.get(id=emp_id)
        except EmployeeProfile.DoesNotExist:
            return None

    def get(self, request, emp_id):

        instance = self.get_object(emp_id)
        if instance != None:
            if not(instance.is_admin == True and instance.is_superuser == True):
                serializer = self.serializer_class(instance)
                return Response(serializer.data)
            else:
                return Response({'error': 'No access to Retrieve this Employee..!'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Given Employee Object not found..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, emp_id):

        instance = self.get_object(emp_id)
        if instance != None:
            if not(instance.is_admin == True and instance.is_superuser == True):
                serializer = self.serializer_class(instance, data=request.data)
                if serializer.is_valid(raise_exception=True):
                    if not(serializer.validated_data.get('date_of_birth') >= date.today()):
                        if serializer.validated_data.get('country') != None:
                            user = serializer.save()
                            groups = Group.objects.all()
                            permissions_list = ["add_employeeprofile", "change_employeeprofile", "delete_employeeprofile"]
                            if serializer.validated_data.get('emp_type') == "7":
                                user.groups.set(groups)
                            else:
                                user.groups.set(groups.exclude(permissions__codename__in=permissions_list))
                            user.date_of_birth = serializer.validated_data['date_of_birth']
                            user.save()
                            return Response(serializer.data, status=status.HTTP_200_OK)
                        else:
                            return Response({'error': 'Country field may not be blank..!'}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response({'error': 'Date of Birth should be less than current date..!'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'No access to Modify this Employee..!'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Given Employee Object not found..!'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, emp_id):

        instance = self.get_object(emp_id)
        if instance != None:
            if instance == request.user:
                if not(instance.is_admin == True and instance.is_superuser == True):
                    # instance.is_staff = False
                    secret_key = ''.join(random.sample(
                        string.ascii_lowercase + string.ascii_uppercase + string.digits, 6))

                    instance.delete()
                    return Response({'message': 'Employee Deleted successfully..!', 'token': secret_key})
                else:
                    return Response({'error': 'No access to Delete this Employee..!'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'error': 'This action is restricted for you..!'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Given Employee Object not found..!'}, status=status.HTTP_404_NOT_FOUND)

class ResetPasswordView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (UpdateEmployeeProfile, IsAuthenticated)

    def get_object(self, emp_id):
        
        try:
            return EmployeeProfile.objects.get(id=emp_id)
        except EmployeeProfile.DoesNotExist:
            return None

    def get(self, request, emp_id):

        instance = self.get_object(emp_id)
        if instance != None:
            if not(instance.is_admin == True and instance.is_superuser == True):
                serializer = EmployeeProfileSerializer(instance)
                return Response(serializer.data)
            else:
                return Response({'error': 'No access to Retrieve this Employee..!'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Given Employee Object not found..!'}, status=status.HTTP_404_NOT_FOUND)

    serializer_class = EmployeePasswordSerializer

    def put(self, request, emp_id):

        instance = self.get_object(emp_id)
        if instance != None:
            if request.user.emp_type == '7': #instance == request.user:
                if not(instance.is_admin == True and instance.is_superuser == True):
                    serializer = self.serializer_class(
                        instance, data=request.data)
                    if serializer.is_valid():
                        user = serializer.save()
                        user.password = make_password(
                            self.request.data["password"])
                        user.save()
                        return Response({'success': 'password changed successfully..!'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'No access to Modify this Employee..!'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'error': 'This is not your Profile..!'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'Given Employee Object not found..!'}, status=status.HTTP_404_NOT_FOUND)

class LoginApiView(KnoxLoginView):

    permission_classes = (permissions.AllowAny,)
    serializer_class = AuthTokenSerializer

    def post(self, request, format=None):

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        employee_login_Log(request.user)
        temp_list=super(LoginApiView, self).post(request, format=None)
        temp_list.data['id'] = user.id
        temp_list.data['first_name'] = user.first_name
        temp_list.data['last_name'] = user.last_name
        temp_list.data['user_type'] = user.emp_type

        return Response({"Data":temp_list.data})

class GroupPermissionView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, EmployeePermission)
    serializer_class = GroupPermissionSerializer

    def get(self, request):

        grp_list = Group.objects.all()
        serialize = GroupPermissionViewSerializer(grp_list, many=True)
        return Response(serialize.data)

class PermissionView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PermissionSerializer

    def get(self, request):

        perm_list = Permission.objects.all()
        serialize = self.serializer_class(perm_list, many=True)
        return Response(serialize.data)

    def post(self, request):

        serialize = self.serializer_class(data=request.data)
        if serialize.is_valid():
            serialize.save()
            return Response(serialize.data, status=status.HTTP_201_CREATED)
        return Response(serialize.errors, status=status.HTTP_400_BAD_REQUEST)

class EmployeeWithPermissionView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, EmployeePermission)
    serializer_class = EmployeeAssignPermission

    def get_object(self, email):

        try:
            return EmployeeProfile.objects.get(email=email)
        except ObjectDoesNotExist:
            return None

    def get(self, request):

        emp_list = EmployeeProfile.objects.all()
        serialize = EmployeeWithPermission(emp_list, many=True)
        return Response(serialize.data)
        
    def put(self, request):

        instace = self.get_object(request.data["email"])
        if instace != None:
            serialize = self.serializer_class(instace,data=request.data)
            if serialize.is_valid():
                serialize.save()
                return Response(serialize.data, status=status.HTTP_201_CREATED)
            return Response(serialize.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Given email not found..!'}, status=status.HTTP_404_NOT_FOUND)

class SingleEmployeePermissionView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, EmployeePermission)
    serializer_class = EmployeeWithPermission

    def get_object(self, emp_id):

        try:
            return EmployeeProfile.objects.get(id=emp_id)
        except ObjectDoesNotExist:
            return None

    def get(self, request, emp_id):

        instance = self.get_object(emp_id)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data)
        else:
            return Response({'error': 'No data found for the provided employee-ID..!'}, status=status.HTTP_404_NOT_FOUND)

class RespondentDetailRelationalfieldView(APIView):

    def post(self, request):
        resp_obj = RespondentDetail.objects.all()

        if resp_obj.count() > 0:
            for resp in resp_obj:

                try:
                    project_group_supp = ProjectGroupSupplier.objects.get(project_group__project_group_number = resp.project_group_number, supplier_org__id = resp.source)
                except ObjectDoesNotExist:
                    project_group_supp = None

                try:
                    project_group_obj = ProjectGroup.objects.get(project_group_number = resp.project_group_number)
                except:
                    project_group_obj = None

                try:
                    project_obj = Project.objects.get(project_number = resp.project_number)
                except:
                    project_obj = None
                try:
                    supplier_org_obj = project_group_supp.supplier_org
                except:
                    supplier_org_obj = None

                resp_relationalfield_obj, resp_relationalfield_obj_created = RespondentDetailsRelationalfield.objects.update_or_create(
                    respondent = resp, defaults={
                        'respondent': resp,
                        'source': supplier_org_obj,
                        'project_group': project_group_obj,
                        'project': project_obj,
                        'project_group_supplier': project_group_supp,
                    }
                )
            return Response({'detail': 'RespondentDetailRelationfield created or updated successfully..!'}, status=status.HTTP_200_OK)
        return Response({'detail': 'RespondentDetailRelationalfield already exist..!'}, status=status.HTTP_200_OK)

class DisableUserView(APIView):
    def get(self, request, emp_id):
        emp_obj = get_object_or_none(EmployeeProfile, id=emp_id)
        if emp_obj != None:
            if emp_obj.is_active == False:
                return Response({'error': 'Employee already disabled..!'}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'id': emp_obj.id, 'first_name': emp_obj.first_name, 'last_name': emp_obj.last_name}, status=status.HTTP_200_OK)
        return Response({'error': 'Employee does not exist..!'}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, emp_id):

        emp_obj = EmployeeProfile.objects.get(id=emp_id)
        if emp_obj.is_active == 0:
            emp_obj = EmployeeProfile.objects.filter(is_superuser = False,id=emp_id).update(is_active=True)
            return Response({'msg': 'Employee Disable successfully..!'}, status=status.HTTP_200_OK)
        elif emp_obj.is_active == 1:
            emp_obj = EmployeeProfile.objects.filter(is_superuser = False,id=emp_id).update(is_active=False)
            return Response({'msg': 'Employee Enable successfully..!'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Employee does not exist..!'}, status=status.HTTP_400_BAD_REQUEST)


class EmpBirthday(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        emp_obj = EmployeeProfile.objects.filter(
            date_of_birth__day=date.today().day,
            date_of_birth__month=date.today().month,
            user_type = '1',is_active=True
        )
        self_birthday = emp_obj.filter(id=request.user.id).values("first_name","last_name").first()
        emp_list_birthday = emp_obj.exclude(id=request.user.id).values("first_name","last_name")
        return Response({"self_birthday":self_birthday,"emp_list_birthday":emp_list_birthday}, status=status.HTTP_200_OK)

class EmployeeTrgateAdd(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            target_month = request.GET.get('target_month')
            target_year = request.GET.get('target_year')
            employee_target = EmployeeTarget.objects.filter(target_month=target_month, target_year=target_year).values("user_id","target_ammount")
            return Response(employee_target, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request):
        try:
            if request.user.email in ['narendra@panelviewpoint.com','unnati@panelviewpoint.com']:
                target_month = request.data['target_month']
                target_year = request.data['target_year']
                conversion = request.data['conversion']
                employee_target = request.data['employee_target']
                
                for i in employee_target:
                    emp_obj = EmployeeProfile.objects.get(id=i['employeeid'])
                    EmployeeTarget.objects.update_or_create(
                        target_month=target_month,
                        target_year=target_year,
                        user=emp_obj,
                        defaults={
                            "target_ammount": i['target_ammount'],
                            "conversion" : conversion
                        }
                    )
            else:
                return Response({"error":"Do Not Have Access to Update Targat"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message":"Employee Targat Updated"}, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)
        

class EmployeeLast6MonthTargetStatus(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            Invoicerowdata = InvoiceRow.objects.filter(
                row_project_number__project_manager_id=request.user
            ).exclude(invoice__invoice_status='4').values(
                year = F('invoice__created_at__year'),
                month = F('invoice__created_at__month')
            ).annotate(
                achieved_target = (Sum(
                    Case(
                        When(invoice__invoice_currency__currency_iso='USD', then=F('row_total_amount') * F('row_project_number__project_manager__employeetarget__conversion')),
                        default=F('row_total_amount'),
                        output_field=DecimalField(),
                    )
                )*100)/F('row_project_number__project_manager__employeetarget__target_ammount')
            ).order_by('-year','-month').distinct()[0:6]
            return Response(Invoicerowdata, status=status.HTTP_200_OK)
        except:  
            return Response({"error":"Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)

class EmpUserDailyVisits(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            today = timezone.now().date()
            seven_days_ago = today - timedelta(days=7)
            respdata = RespondentDetail.objects.filter(
                end_time_day__gte=seven_days_ago,end_time_day__lte=today,
                respondentdetailsrelationalfield__project__project_manager=request.user
                ).values(
                    date = F('end_time_day')).annotate(
                        visit = Count('id'),
                        incomplete = Count('id', filter=Q(resp_status = '3')),
                        completes = Count('id', filter=Q(resp_status = '4')),
                        terminate = Count('id', filter=Q(resp_status__in = ['5','2','7'])),
                    ).order_by('date')
            return Response(respdata, status=status.HTTP_200_OK)
        except:
            return Response({"message":"Something want wrong"}, status=status.HTTP_400_BAD_REQUEST)

class UserAssignedBid(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        bid = Bid.objects.filter(
            start_date__month = 2,
            start_date__year = timezone.now().year,
            project_manager = request.user
        ).aggregate(
            assigned_bid = Count('id'),
            project_created = Count('project',distinct=True)
        )
        return Response(bid, status=status.HTTP_200_OK)

class EmpCurrentMonthStatus(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            current_month = date.today().month
            current_year = date.today().year
            userid = request.user.id
            conversion = EmployeeTarget.objects.filter(target_month = current_month,target_year = current_year).values_list('conversion',flat=True).first() or 86
            invoice_rows = InvoiceRow.objects.filter(
                    row_project_number__project_manager_id=userid,
                    invoice__invoice_date__year = current_year,
                    invoice__invoice_date__month = current_month
                ).exclude(
                    invoice__invoice_status='4'
                    )
            emp_current_month_targate = invoice_rows.aggregate(
                    achieved_target_in_INR = Sum(
                        Case(
                            When(invoice__invoice_currency__currency_iso='USD', then=F('row_total_amount') * conversion),
                            default=F('row_total_amount'),
                            output_field=DecimalField(),
                        )
                    )
                )
            draft_invoice = DraftInvoice.objects.filter(
                project__project_manager_id=userid,
                created_at__year = current_year,
                created_at__month = current_month,
                BA_approved=True,
                ).exclude(project__project_status = 'Invoiced').aggregate(
                    lock_targate_in_INR = Sum(
                        Case(
                            When(bid_currency__currency_iso='USD', then=F('bid_total') * conversion),
                            default=F('bid_total'),
                            output_field=DecimalField(),
                        )
                    )
                )
            emptargate = EmployeeTarget.objects.filter(
                user_id = userid,target_month = current_month,target_year = current_year).values('target_ammount')

            emp_current_month_targate['lock_targate_in_INR'] = draft_invoice['lock_targate_in_INR']

            emp_current_month_targate['emptargate_in_pr'] = ((emp_current_month_targate['achieved_target_in_INR']*100)/emptargate[0]['target_ammount']) if emptargate else 0

            emp_current_month_targate['emptargate_in_pr_remain'] = (100 - emp_current_month_targate['emptargate_in_pr']) if emptargate else 0

            emp_current_month_targate['project_number_list'] = invoice_rows.values_list('row_project_number__project_number',flat=True)
            
            return Response(emp_current_month_targate, status=status.HTTP_200_OK)
        except:
            return Response({'error':'No Data Found'}, status=status.HTTP_400_BAD_REQUEST)