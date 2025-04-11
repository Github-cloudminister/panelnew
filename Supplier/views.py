import json
from django.conf import settings
from django.db.models.functions import Cast,Coalesce,Concat
from django.db.models import Count, F, Value, Q, Sum, Case, When
# import requests
from uuid import uuid4

from Logapp.views import sub_supplier_log, supplier_enable_disable_log, supplier_log
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import generics

from knox.auth import TokenAuthentication
from Project.models import Language, ProjectGroupSubSupplier, ProjectGroupSupplier

from Supplier.serializers import *
from Supplier.models import *
from SupplierAPI.models import LucidCountryLanguageMapping
from Supplier.permissions import *

# ********** third-party libraries ***************
from hashlib import  blake2b
import requests
from SupplierInvoice.models import SupplierInvoice
from django.template.loader import render_to_string
from automated_email_notifications.email_configurations import sendEmailSendgripAPIIntegration


header = {'Static-Token':'SSPOMDq[FOL@@Qh98TT5qbr~Z73-j)8zWa2c='}


class SupplierContactDashboardResetPasswordView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierPermission)

    def post(self, request, supp_contact_id):
        supp_contact_obj = SupplierContact.objects.get(id=supp_contact_id)
        password = request.data['password']
        
        response = requests.post(settings.SUPPLIER_DASHBOARD_URL + 'user-resetPassword-panelviewpoint', json={'email':supp_contact_obj.supplier_email,'password':password}, headers=header)

        if response.status_code == 200:
            return Response({'message': 'Your resetting Password has been sent to Supplier Contact Successfully'}, status=status.HTTP_200_OK)
        elif response.status_code == 401:
            return Response({'message':'Static Token to access Supplier Dashboard is Incorrect'}, status=status.HTTP_401_UNAUTHORIZED)
        elif response.status_code == 404:
            return Response({'message':'No User Found with this Email ID'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'message':'Supplier Dashboard URL Not Found'}, status=status.HTTP_404_NOT_FOUND)



class SupplierPrjGrpSuppRespStats(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        supplier_id = request.GET.get('supplier_id')
        if not supplier_id:
            return Response({'message': 'supplier_id GET parameters is required'}, status=status.HTTP_208_ALREADY_REPORTED)
        prjgrpsupp_stats = ProjectGroupSupplier.objects.select_related('supplier_org', 'project_group__project__project_manager', 'project_group__project__project_customer', 'project_group__project_group_country', 'project_group__project_group_language', 'respondentdetailsrelationalfield__respondent').filter(supplier_org_id=supplier_id, supplier_status='Live').values('id').annotate(
            required_completes=F('completes'), 
            required_clicks=F('clicks'), 
            cpi=F('cpi'), 
            supplier_code=F('supplier_org__supplier_code'), 
            supplier_name=F('supplier_org__supplier_name'), 
            created_at=F('created_at'), 
            survey_no=F('project_group__project_group_number'), 
            survey_name=F('project_group__project_group_number'), 
            project_name=F('project_group__project__project_name'), 
            project_no=F('project_group__project__project_number'), 
            project_manager=Concat(F('project_group__project__project_manager__first_name'), Value(' '), F('project_group__project__project_manager__last_name')), 
            customer_name=F('project_group__project__project_customer__cust_org_name'), 
            country=F('project_group__project_group_country__country_name'), 
            language=F('project_group__project_group_language__language_name'), 
            total_visits=Count('respondentdetailsrelationalfield__respondent__resp_status', filter=Q(respondentdetailsrelationalfield__respondent__url_type='Live')),  
            completes=Count('respondentdetailsrelationalfield__respondent__resp_status', filter=Q(respondentdetailsrelationalfield__respondent__resp_status='4',respondentdetailsrelationalfield__respondent__url_type='Live')), 
            incompletes=Count('respondentdetailsrelationalfield__respondent__resp_status',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='3', respondentdetailsrelationalfield__respondent__url_type='Live')), 
            revenue=Coalesce(
                Sum(
                    'respondentdetailsrelationalfield__respondent__project_group_cpi', 
                    filter=Q(respondentdetailsrelationalfield__respondent__resp_status='4',respondentdetailsrelationalfield__respondent__url_type='Live')
                ), 0.0
            ), 
            expense=Coalesce(
                Sum(
                    'respondentdetailsrelationalfield__respondent__supplier_cpi', 
                    filter=Q(respondentdetailsrelationalfield__respondent__resp_status='4',respondentdetailsrelationalfield__respondent__url_type='Live')
                ), 0.0
            ), 
            terminates=Count('respondentdetailsrelationalfield__respondent__resp_status',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='5', respondentdetailsrelationalfield__respondent__url_type='Live')), 
            quota_full=Count('respondentdetailsrelationalfield__respondent__resp_status',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='6', respondentdetailsrelationalfield__respondent__url_type='Live')), 
            security_terminate=Count('respondentdetailsrelationalfield__respondent__resp_status',filter=Q(respondentdetailsrelationalfield__respondent__resp_status='7', respondentdetailsrelationalfield__respondent__url_type='Live')), 
            starts=Cast(
                F('incompletes')+F('completes')+F('terminates')+F('quota_full')+F('security_terminate'), 
                output_field=models.FloatField()
            ), 
            conversion=Case(
                When(
                    Q(starts=0)|Q(starts=None),
                    then=Cast(0.0, output_field=models.DecimalField(max_digits=7, decimal_places=2))
                ),
                default=Cast(
                    (F('completes')/F('starts'))*100, 
                    output_field=models.DecimalField(max_digits=7, decimal_places=2)
                )
            )
        )

        return Response(data=prjgrpsupp_stats)




class SupplierContactDashboardRegistrationView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierPermission)

    def post(self, request, supp_contact_id):
        supplier_dashboard = request.GET.get('supplier_dashboard')
        supp_contact_obj = SupplierContact.objects.get(id=supp_contact_id)
        serializer = SupplierContactSerializer(supp_contact_obj)
        if supplier_dashboard == 'register':

            if supp_contact_obj.supplier_dashboard_registration == True:
                return Response({'message': 'User is Already Registered on Supplier Dashboard'}, status=status.HTTP_208_ALREADY_REPORTED)

            final_dict_data = serializer.data
            
            data = {
                'user_type':supp_contact_obj.supplier_id.supplier_type,
                'company_name':supp_contact_obj.supplier_id.supplier_name
                } 
            final_dict_data.update(data)

            user_exists = EmployeeProfile.objects.filter(email = final_dict_data['email'].lower())
            if user_exists.exists():
                user_exists.update(is_active = True)
                supp_contact_obj.supplier_dashboard_registration = True
                supp_contact_obj.save()
                supplier_enable_disable_log('Enabled','',supp_contact_obj.supplier_id.id,request.user)
                return Response({'message': 'User Status Turned Active From Inactive'}, status=status.HTTP_208_ALREADY_REPORTED)
                
            else:
                user_create = EmployeeProfile.objects.create(
                    first_name = final_dict_data['first_name'],
                    last_name = final_dict_data['last_name'],
                    email = final_dict_data['email'].lower(),
                    contact_number = final_dict_data['contact_number'],
                    source_id = final_dict_data['supplier_id'],
                    user_type = '2',
                    emp_type = '10'
                )

                user_password_token = uuid4().hex
                exist_user_token = UserTokenVerifyPasswordReset.objects.filter(user = user_create).delete()
                user_token_obj = UserTokenVerifyPasswordReset.objects.create(user = user_create, user_token = user_password_token)
                
                supp_contact_obj.supplier_dashboard_registration = True
                supp_contact_obj.supplier_mail_sent = True
                supp_contact_obj.save()
                html_message = render_to_string('supplierdashboard/emailtemplates/new_user_set_password.html', {
                        'firstname': supp_contact_obj.supplier_firstname,
                        'username':final_dict_data['email'],
                        'password_set_url':f"{settings.SUPPLIER_DASHBOARD_FRONTEND_URL}#/authentication/set-password/{user_token_obj.user_token}"
                        })
                sendEmailSendgripAPIIntegration(to_emails=supp_contact_obj.supplier_email, subject='User Registration Mail', html_message=html_message)
                supplier_enable_disable_log('Enabled','',supp_contact_obj.supplier_id.id,request.user)
                return Response({'message': 'User has been Registered Successfully & The Password Setting Email has been sent'}, status=status.HTTP_201_CREATED)

        elif supplier_dashboard == 'deregister':
            if supp_contact_obj.supplier_dashboard_registration == False:
                return Response({'message': 'User is Already De-Registered on Supplier Dashboard'}, status=status.HTTP_208_ALREADY_REPORTED)

            final_dict_data = serializer.data
            supp_contact_obj.supplier_dashboard_registration = False
            supp_contact_obj.save()

            user_obj = EmployeeProfile.objects.filter(email = final_dict_data['email'].lower())
            user_obj.update(is_active = False)

            supplier_enable_disable_log('Disabled','',supp_contact_obj.supplier_id.id,request.user)
            return Response({'message': 'User Successfully De-Registered on Supplier Dashboard'}, status=status.HTTP_200_OK)

        else:
            return Response({'message':'Please pass supplier_dashboard URL Parameter & pass its value to either register or deregister'}, status=status.HTTP_400_BAD_REQUEST)



class SupplierDetailContactView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierPermission)

    def get(self, request, supplier_id):

        supplier_contact_list = SupplierContact.objects.filter(supplier_id=supplier_id, supplier_contact_status=True)
        if supplier_contact_list:
            serializer = SupplierContactSerializer(supplier_contact_list, many=True)
            return Response(serializer.data)
        else:
            return Response({'error': 'No data found for provided Supplier-ID..!'}, status=status.HTTP_404_NOT_FOUND)
        

class SubSupplierDetailContactView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierPermission)

    def get(self, request, sub_supplier_id):

        supplier_contact_list = SubSupplierContact.objects.filter(subsupplier_id=sub_supplier_id, subsupplier_contact_status=True)
        if supplier_contact_list:
            serializer = SubSupplierContactListSerializer(supplier_contact_list, many=True)
            return Response(serializer.data)
        else:
            return Response({'error': 'No data found for provided Supplier-ID..!'}, status=status.HTTP_404_NOT_FOUND)


class SupplierView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierPermission)
    serializer_class = SupplierSerializer

    def get(self, request):

        sup_type = request.GET.get('sup_type', '')
        supplier_data = request.GET.get('supplier')
        if supplier_data == 'detail':
            supplier_list = SupplierOrganisation.objects.only('id','supplier_name','supplier_status').all().values('id','supplier_name','supplier_status').order_by("supplier_name")
            return Response(supplier_list, status=status.HTTP_200_OK)
        if sup_type == '5':
            supplier_list = SubSupplierOrganisation.objects.filter(supplier_org_id__supplier_type = sup_type,sub_supplier_status = '1').order_by("sub_supplier_name")
            serializer = SubSupplierListSerializer(supplier_list, many=True)
            return Response(serializer.data)
        if sup_type != '':
            supplier_list = SupplierOrganisation.objects.filter(supplier_type = sup_type).order_by("supplier_name")
        else:
            supplier_list = SupplierOrganisation.objects.all().order_by("supplier_name")
        serializer = self.serializer_class(supplier_list, many=True)
        return Response(serializer.data)

    def post(self, request):
        if request.data['supplier_type'] not in ["1", "2", "3", "4"]:
            return Response({'error': 'Invalid supplier type..!'}, status=status.HTTP_400_BAD_REQUEST)

            
        if request.data['supplier_type'] == '3':
            try:
                supplier_rate_model = request.data.get('supplier_rate_model', None)
                supplier_rate = request.data.get('supplier_rate', None)
                if supplier_rate_model == None or supplier_rate == None:
                    return Response(status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
            except Exception as e:
                return Response(status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if serializer.validated_data.get('supplier_country') != None:
                instance = serializer.save(created_by=request.user)

                # ******** Create supplier_code *********
                key_value = 'LTauDqcX4PdeBANhj3fkfrN65QEjhJ' + str(instance.id)
                h = blake2b(digest_size=8)
                h.update(key_value.encode())

                # Save Supplier Code
                instance.supplier_code = h.hexdigest()

                if instance.supplier_type == "3":
                    routerurl = f"{settings.AFFILIATE_URL}?sc={instance.supplier_code}&country=<countryCode>&lang=<languageCode>&ruid=<Unique-User-ID>&rsid=<respondent-session-id>"
                    instance.supplier_routerurl = routerurl
                    country_list = Country.objects.all()
                    suppmapp_list = []
                    for country_obj in country_list:
                        suppmapp_list.append(SupplierCPIMapping(supplier_org=instance, country=country_obj, cpi=instance.supplier_rate))
                    SupplierCPIMapping.objects.bulk_create(suppmapp_list)

                # Save Instance
                instance.save()
                supplier_log(serializer.data,'',instance.id,request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Supplier Country not to be kept blank..!'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupplierUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierUpdatePermission)
    serializer_class = SupplierUpdateSerializer

    def get_object(self, supplier_id):

        try:
            return SupplierOrganisation.objects.get(id=supplier_id)
        except SupplierOrganisation.DoesNotExist:
            return None

    def get(self, request, supplier_id):

        instance = self.get_object(supplier_id)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data)
        else:
            return Response({'error': 'No data found for provided Supplier-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, supplier_id):

        instance = self.get_object(supplier_id)
        if instance != None:
            if instance.supplier_type == '3':
                try:
                    supplier_rate_model = request.data.get('supplier_rate_model', None)
                    supplier_rate = request.data.get('supplier_rate', None)
                    if supplier_rate_model == None or supplier_rate == None:
                        return Response(status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
                except Exception as e:
                    return Response(status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid():
                if serializer.validated_data.get('supplier_country') != None:

                    supplier_obj = serializer.save(modified_by=request.user)

                    if supplier_obj.supplier_type == "3":
                        suppmapp_cpi_obj = SupplierCPIMapping.objects.filter(supplier_org=supplier_obj).update(cpi=supplier_obj.supplier_rate)

                    # serializer.save(modified_by=request.user)
                    supplier_log('',serializer.data,instance.id,request.user)
                    return Response(serializer.data, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Supplier Country field may not be blank..!'}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'No data found for provided Supplier-ID..!'}, status=status.HTTP_404_NOT_FOUND)


class SupplierContactView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierContactPermission)
    serializer_class = SupplierContactSerializer

    def get(self, request):

        supplier_list = SupplierContact.objects.filter(supplier_contact_status=True)
        serializer = self.serializer_class(supplier_list, many=True)
        return Response(serializer.data)

    def post(self, request):
        
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            sup_contact_exits = SupplierContact.objects.filter(supplier_id = serializer.validated_data.get("supplier_id"), supplier_email = serializer.validated_data.get("supplier_email").lower())
            if sup_contact_exits.exists():
                return Response({"error":"This Email Already Exits in this Supplier.!"}, status=status.HTTP_400_BAD_REQUEST)

            supp_contact = serializer.save(created_by=request.user)
            supp_contact.supplier_email = serializer.validated_data.get("supplier_email").lower()
            supp_contact.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupplierContactUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierContactUpdatePermission)
    serializer_class = SupplierContactUpdateSerializer

    def get_object(self, supplier_contact_id):

        try:
            return SupplierContact.objects.get(id=supplier_contact_id, supplier_contact_status=True)
        except SupplierContact.DoesNotExist:
            return None

    def get(self, request, supplier_contact_id):

        instance = self.get_object(supplier_contact_id)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data)
        else:
            return Response({'error': 'No data found for provided SupplierContact-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, supplier_contact_id):

        data = request.data
        instance = self.get_object(supplier_contact_id)
        try:
            if request.data["contact_number"] == '':
                data = request.data
                data["contact_number"] = None
        except:
            data = request.data
            data["contact_number"] = None
            
        if instance != None:
            serializer = self.serializer_class(instance, data=data)
            if serializer.is_valid():
                serializer.save(modified_by=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No data found for provided SupplierContact-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, supplier_contact_id):

        instance = self.get_object(supplier_contact_id)
        instance.supplier_contact_status = False
        return Response(status=status.HTTP_204_NO_CONTENT)


class SupplierOrgAuthKeyDetailsView(generics.ListAPIView, generics.CreateAPIView):

    serializer_class = SupplierOrgAuthKeyDetailsSerializer
    queryset = SupplierOrgAuthKeyDetails.objects.all()



class SupplierInvoicingDetailsView(generics.ListCreateAPIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SupplierInvoicingDetailsSerializer
    queryset = SupplierInvoicingDetails.objects.all()


class SupplierInvoicingUpdateView(generics.RetrieveUpdateAPIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SupplierInvoicingDetailsSerializer
    queryset = SupplierInvoicingDetails.objects.all()

    def put(self, request, pk):
        response = super().update(request)
        bank_details = request.data.pop('bank_details')
        bank_details_obj = SupplierBankDetails.objects.filter(supplier_inv_detail_id=pk)
        if bank_details_obj:
            bank_details_obj.update(**bank_details)
        return response


class SupplierOrgAuthKeyDetailsUpdateView(generics.RetrieveUpdateAPIView):

    serializer_class = SupplierOrgAuthKeyDetailsSerializer
    queryset = SupplierOrgAuthKeyDetails.objects.all()


class LucidAPICountryLanguageSync(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        LucidCountryLanguageMapping.objects.all().delete()

        headers = {
            'Authorization': '72E92E75-D1CF-4190-974C-DA7E8F1F139C'
            }

        response = requests.get('https://sandbox.techops.engineering/Lookup/v1/BasicLookups/BundledLookups/CountryLanguages', headers=headers)

        responses_dict = {item['Name']:item for item in response.json()['AllCountryLanguages']}

        for item in response.json()['AllCountryLanguages']:
            if item['Name'].split('-')[1].replace(' ','') == 'RepublicoftheCongo':
                country_obj = Country.objects.get(country_name='Congo - Kinshasa')
                language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            elif item['Name'].split('-')[1].replace(' ','') == 'HongKong':
                country_obj = Country.objects.get(country_name='Hong Kong SAR China')
                if item['Name'].split('-')[0][:-1] == 'Chinese Traditional':
                    language_obj = Language.objects.get(language_name='Chinese')
                else:
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            elif item['Name'].split('-')[1].replace(' ','') == 'TaiwanProvinceOfChina':
                country_obj = Country.objects.get(country_name='Taiwan')
                language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            elif item['Name'].split('-')[1].replace(' ','') == 'Slovakia(SlovakRepublic)':
                country_obj = Country.objects.get(country_name='Slovakia')
                language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            elif item['Name'].split('-')[1].replace(' ','') == 'LibyanArabJamahiriya':
                country_obj = Country.objects.get(country_name='Libya')
                language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            elif item['Name'].split('-')[1].replace(' ','') == 'Myanmar':
                country_obj = Country.objects.get(country_name='Myanmar [Burma]')
                language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            elif item['Name'].split('-')[1].replace(' ','') == 'RepublicoftheCôted\'Ivoire':
                country_obj = Country.objects.get(country_name='Cote DIvoire')
                language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            elif item['Name'].split('-')[1].replace(' ','') in ('SãoToméandPríncipe','SaoTomeAndPrincipe'):
                country_obj = Country.objects.get(country_name='Sao Tome and Principe')
                language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            elif item['Name'].split('-')[1].replace(' ','') == 'DemocraticRepublicoftheCongo':
                country_obj = Country.objects.get(country_name='Congo - Brazzaville')
                language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            elif item['Name'].split('-')[1].replace(' ','') == 'Korea':
                country_obj = Country.objects.get(country_name='North Korea')
                language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            elif item['Name'].split('-')[1].replace(' ','') == 'Palestine':
                country_obj = Country.objects.get(country_name='Palestinian Territories')
                language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            elif item['Name'].split('-')[1].replace(' ','')[1:].isupper() != True and item['Name'].split('-')[1].replace(' ','')[1:].islower() != True:
                country_full_name = item['Name'].split('-')[1].replace(' ','')
                country_sliced_name = item['Name'].split('-')[1].replace(' ','')[1:]
                country_name_list = []
                country_name_list.extend(country_full_name)
                uppercase_frequency = 0
                for string in country_sliced_name:
                    if string.isupper() == True:
                        uppercase_frequency+=1
                        if uppercase_frequency > 2:
                            position = country_sliced_name.index(string)
                            country_name_list.insert(position+3,'^')
                        elif uppercase_frequency > 1:
                            position = country_sliced_name.index(string)
                            country_name_list.insert(position+2,'^')
                        else:
                            position = country_sliced_name.index(string)
                            country_name_list.insert(position+1,'^')
                final_country_name_str = ''.join(country_name_list).replace('^',' ')
                country_obj = Country.objects.get(country_name=final_country_name_str)
                if item['Name'].split('-')[0][:-1] in ('Chinese Simplified','Chinese Traditional'):
                    language_obj = Language.objects.get(language_name='Chinese')
                else:
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
            else:
                country_obj = Country.objects.get(country_name=(item['Name'].split('-'))[1].replace(' ','') if len(item['Name'].split('-')) == 2 else '-'.join(item['Name'].split('-')[1:]).replace(' ',''))
                if item['Name'].split('-')[0][:-1] in ('Chinese Traditional','Chinese Simplified'):
                    language_obj = Language.objects.get(language_name='Chinese')
                elif item['Name'].split('-')[0][:-1] == 'Luxembourg':
                    language_obj = Language.objects.get(language_name='Luxembourgish')
                elif item['Name'].split('-')[0][:-1] == 'Slovene':
                    language_obj = Language.objects.get(language_name='Slovenian')
                elif item['Name'].split('-')[0][:-1] == 'Gujrati':
                    language_obj = Language.objects.get(language_name='Gujarati')
                elif item['Name'].split('-')[0][:-1] == 'Bokmal':
                    language_obj = Language.objects.get(language_name='Norwegian Bokmal')
                elif item['Name'].split('-')[0][:-1] in ('Flemish','Dogri','Konkani','Maithili','Manipuri','Odia','Santali','Sesotho','Chinese Simplified','Cantonese'):
                    # These Languages do not exist in our DB
                    continue
                else:
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])

            country_lang_id = responses_dict[item['Name']]['Id']
            country_lang_code = responses_dict[item['Name']]['Code']
            country_lang_name = responses_dict[item['Name']]['Name']
            LucidCountryLanguageMapping.objects.create(lanugage_id=language_obj, country_id=country_obj, lucid_country_lang_id=country_lang_id, lucid_language_code=country_lang_code, lucid_language_name=country_lang_name)

        return Response({'message': 'Lucid Supplier\'s Country & Language Mapped Successfully in your Database'}, status=status.HTTP_201_CREATED)



class SupplierInvoiceApprovalEmailView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        supp_inv_ids = request.data.get('supp_inv_ids')
        supp_cntct_ids = request.data.get('supp_cntct_ids')

        supp_contact_qs = SupplierContact.objects.filter(id__in=supp_cntct_ids)
        supplier_emails = supp_contact_qs.values_list('supplier_email', flat=True)
        supp_invoice_qs = SupplierInvoice.objects.filter(id__in=supp_inv_ids)
        sum_invoice_amount = SupplierInvoice.objects.filter(id__in=supp_invoice_qs).aggregate(Sum('total_invoice_amount'))

        html_message = render_to_string('Supplier/supplier_payment_approval_email.html', {'supp_invoice_qs':supp_invoice_qs, 'sum_invoice_amount':sum_invoice_amount})

        sendEmail = sendEmailSendgripAPIIntegration(from_email = ('accounts@panelviewpoint.com', 'Invoice Approval'), to_emails=list(supplier_emails), cc_emails = 'ar@panelviewpoint.com' if settings.SERVER_TYPE == 'production' else 'pythonteam1@slickservices.in', subject=f'Invoice Approved: {supp_contact_qs[0].supplier_id.supplier_name} {datetime.now().date()}', html_message=html_message)

        if sendEmail.status_code not in [200, 201]:
            fail_reason = json.loads(sendEmail.content.decode())['message']
            return Response(data={'message':'Invoice Payment Reminder Email to Client Contacts not sent successfully', 'reason':fail_reason}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(data={'message':'Supplier Invoice Payment Approval Email Sent successfully to Supplier Contacts'})


class UserRegistrationReSendEmailPasswordLink(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierPermission)

    def post(self,request, supp_contact_id):
        supp_contact_obj = SupplierContact.objects.get(id=supp_contact_id)
        serializer = SupplierContactSerializer(supp_contact_obj)

        final_dict_data = serializer.data

        user_token = uuid4().hex
        user_obj = EmployeeProfile.objects.filter(email = supp_contact_obj.supplier_email)
        if user_obj.exists():
            exist_user_token = UserTokenVerifyPasswordReset.objects.filter(user = user_obj[0]).delete()
            user_token_obj = UserTokenVerifyPasswordReset.objects.create(user = user_obj[0], user_token = user_token)
            
            supp_contact_obj.supplier_dashboard_registration = True
            supp_contact_obj.supplier_mail_sent = True
            supp_contact_obj.save()
            html_message = render_to_string('supplierdashboard/emailtemplates/new_user_set_password.html', {
                    'firstname': supp_contact_obj.supplier_firstname,
                    'username':final_dict_data['email'],
                    'password_set_url':f"{settings.SUPPLIER_DASHBOARD_FRONTEND_URL}#/authentication/set-password/{user_token}"
                    })
            send_email = sendEmailSendgripAPIIntegration(to_emails=supp_contact_obj.supplier_email, subject='User Registration Mail', html_message=html_message)
            if send_email.status_code in [200, 201]:
                supp_contact_obj.supplier_mail_sent = True
                supp_contact_obj.save()
                return Response({"message":"Password Link Has Sent Been Email Successfully.! "}, status=status.HTTP_200_OK)
            else:
                supp_contact_obj.supplier_mail_sent = False
                supp_contact_obj.save()
                return Response({"error":f"We Can't Send Email Due to SendGrid Response Status-{send_email.status_code}"}, status=status.HTTP_400_BAD_REQUEST)
        else:
             return Response({'message':'No User Found with this Email ID'}, status=status.HTTP_400_BAD_REQUEST)

class SubSupplierView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierPermission)
    serializer_class = SubSupplierSerializer

    def get(self, request):

        sub_supplier_details = self.request.GET.get("sub_supplier","")
        if sub_supplier_details == "detail":
            supplier_list = SubSupplierOrganisation.objects.only("id","sub_supplier_name","sub_supplier_status").values("id","sub_supplier_name","sub_supplier_status").order_by("sub_supplier_name")
            return Response(supplier_list, status=status.HTTP_200_OK)
        
        if sub_supplier_details == "redirects-detail":
            supplier_list = SubSupplierOrganisation.objects.only("id","sub_supplier_name","sub_supplier_status","sub_supplier_completeurl","sub_supplier_terminateurl","sub_supplier_quotafullurl","sub_supplier_securityterminateurl","sub_supplier_postbackurl","sub_supplier_internal_terminate_redirect_url","sub_supplier_terminate_no_project_available").values("id","sub_supplier_name","sub_supplier_status","sub_supplier_completeurl","sub_supplier_terminateurl","sub_supplier_quotafullurl","sub_supplier_securityterminateurl","sub_supplier_postbackurl","sub_supplier_internal_terminate_redirect_url","sub_supplier_terminate_no_project_available").order_by("sub_supplier_name")
            return Response(supplier_list, status=status.HTTP_200_OK)
        
        else:
            supplier_list = SubSupplierOrganisation.objects.all().order_by("sub_supplier_name")
            serializer = self.serializer_class(supplier_list, many=True)
            return Response(serializer.data)
    
    def post(self, request):
        try:
            data = request.data
            data['supplier_org_id'] = SupplierOrganisation.objects.filter(supplier_type='5').first().id
            serializer = self.serializer_class(data=data)
            if serializer.is_valid():
                instance = serializer.save(created_by=request.user)
                key_value = 'LTauDqcX4PdeBANhj3fkfrN65QEjhJ' + str(instance.id)
                h = blake2b(digest_size=8)
                h.update(key_value.encode())
                instance.sub_supplier_code = h.hexdigest()
                instance.save()
                sub_supplier_log(serializer.data,'',instance.id,request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"error":"Panel Supplier Not Found..!"}, status=status.HTTP_400_BAD_REQUEST)

class SubSupplierUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierUpdatePermission)
    serializer_class = SubSupplierSerializer

    def get(self, request,subsupplier_id):
        try:
            subsupplier_contact_obj = SubSupplierOrganisation.objects.get(id=subsupplier_id)
            serializer = self.serializer_class(subsupplier_contact_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request,subsupplier_id):
        subsupplier_obj = SubSupplierOrganisation.objects.get(id=subsupplier_id)
        serializer = self.serializer_class(subsupplier_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            sub_supplier_log('',serializer.data,subsupplier_obj.id,request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubSupplierContactView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierContactPermission)
    serializer_class = SubSupplierContactSerializer

    def get(self, request):
        
        try:
            supplier_list = SubSupplierContact.objects.filter(subsupplier_contact_status=True)
            serializer = self.serializer_class(supplier_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            sup_contact_exits = SubSupplierContact.objects.filter(subsupplier_id = serializer.validated_data.get("subsupplier_id"), subsupplier_email = serializer.validated_data.get("subsupplier_email").lower())
            if sup_contact_exits.exists():
                return Response({"error":"This Email Already Exits in this Supplier.!"}, status=status.HTTP_400_BAD_REQUEST)
            sub_supp_contact = serializer.save(created_by=request.user)
            sub_supp_contact.subsupplier_email = serializer.validated_data.get("subsupplier_email").lower()
            sub_supp_contact.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubSupplierContactUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierContactPermission)
    serializer_class = SubSupplierContactSerializer

    def get(self, request,subsupplier_contact_id):
        try:
            subsupplier_contact_obj = SubSupplierContact.objects.get(subsupplier_id__id=subsupplier_contact_id)
            serializer = self.serializer_class(subsupplier_contact_obj)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request,subsupplier_contact_id):
        subsupplier_contact_obj = SubSupplierContact.objects.get(id=subsupplier_contact_id)
        serializer = self.serializer_class(subsupplier_contact_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupplierStatusUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierContactPermission)
    
    def post(self, request):
        supplierid = request.data.get('supplierid')
        supplier_status = request.data.get('supplier_status')
        SupplierOrganisation.objects.filter(id = supplierid).update(supplier_status = supplier_status)
        return Response({"message":"Supplier Status Updated..!"}, status=status.HTTP_200_OK)


class SubSupplierStatusUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, SupplierContactPermission)
    
    def post(self, request):
        subsupplierid = request.data.get('subsupplierid')
        sub_supplier_status = request.data.get('sub_supplier_status')
        SubSupplierOrganisation.objects.filter(id = subsupplierid).update(sub_supplier_status = sub_supplier_status)
        return Response({"message":"Sub Supplier Status Updated..!"}, status=status.HTTP_200_OK)
    
class SubSupplierStatusListView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request):
        try:
            projectgroupid = request.GET.get('projectgroupid','')
            projectgroupstatuslist = ProjectGroupSubSupplier.objects.filter(
                    project_group__id = projectgroupid).values(
                    'clicks','cpi',total_N = F('completes'),
                    sub_supplier = F('sub_supplier_org__id'),status = F('sub_supplier_status'),
                )
            return Response(projectgroupstatuslist, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something Want Wrong"}, status=status.HTTP_400_BAD_REQUEST)

class SubSupplierRedirectGetUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request,projectgroupid,subsupplierid):

        try:
            projectgroupsupplierobj = ProjectGroupSubSupplier.objects.filter(
                project_group__id = projectgroupid,sub_supplier_org__id = subsupplierid).values('sub_supplier_completeurl','sub_supplier_terminateurl','sub_supplier_quotafullurl','sub_supplier_securityterminateurl','sub_supplier_postbackurl','sub_supplier_internal_terminate_redirect_url').first()
            return Response(projectgroupsupplierobj, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something Want Wrong"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self,request,projectgroupid,subsupplierid):

        try:
            redirects = request.data
            ProjectGroupSubSupplier.objects.filter(
                project_group__id = projectgroupid,sub_supplier_org__id = subsupplierid).update(sub_supplier_completeurl = redirects['sub_supplier_completeurl'],sub_supplier_terminateurl = redirects['sub_supplier_terminateurl'],sub_supplier_quotafullurl = redirects['sub_supplier_quotafullurl'],sub_supplier_securityterminateurl = redirects['sub_supplier_securityterminateurl'],sub_supplier_postbackurl = redirects['sub_supplier_postbackurl'],sub_supplier_internal_terminate_redirect_url = redirects['sub_supplier_internal_terminate_redirect_url'])
            return Response({"message":"Sub Supplier Redirects Updated..!"}, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Something Want Wrong"}, status=status.HTTP_400_BAD_REQUEST)