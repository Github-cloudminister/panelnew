from django.urls import path
from knox import views as knox_views
from employee.views import *


app_name = "employee"

urlpatterns = [

    path('', LoginApiView.as_view(), name="login"),

    path('list', EmployeeListView.as_view(), name="employee_list"),

    path('signup', EmployeeRegisterApiView.as_view(), name="employee_register"),

    path('reset-password/<int:emp_id>', ResetPasswordView.as_view(), name="reset_password"),

    path('<int:emp_id>', EmployeeUpdateView.as_view(), name="employee_update"),

    path('logout/', knox_views.LogoutView.as_view(), name='knox_logout'),

    path('logoutall/', knox_views.LogoutAllView.as_view(), name='knox_logoutall'),

    path('group', GroupPermissionView.as_view(), name="group"),

    path('emp-permission', EmployeeWithPermissionView.as_view(), name="emp_perm"),

    path('emp-permission/<int:emp_id>', SingleEmployeePermissionView.as_view(), name="emp_perm"),

    path('respondent-relationalfield/create', RespondentDetailRelationalfieldView.as_view()),

    path('disable-user/<int:emp_id>', DisableUserView.as_view(), name="diable_user"),
    
    path('empbirthday', EmpBirthday.as_view()),

    path('employee-target-add', EmployeeTrgateAdd.as_view()),

    path('employee-last-6-month-target-status', EmployeeLast6MonthTargetStatus.as_view()),

    path('emp-user-daily-visits',EmpUserDailyVisits.as_view()), #last 7 days emp user stats

    path('user-assigned-bid',UserAssignedBid.as_view()), #this month user assigned bid

    path('emp-current-month-status',EmpCurrentMonthStatus.as_view()), #emp current month
]