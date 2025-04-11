import uuid
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from knox.auth import TokenAuthentication

# ********* in-project imports **********
from SupplierAPI.models import *
from Project.models import *
from Supplier.models import *
from Supplier.serializers import *
from SupplierAPI.serializers import *
from Project.serializers import *

# ********* import custom permissions **********
from SupplierAPI.permissions import *
from django.conf import settings

# ********* import disqoAPI functions **********
from SupplierAPI.disqo_supplier_api.custom_functions import *
from SupplierAPI.disqo_supplier_api.create_or_update_project import *
from SupplierAPI.disqo_supplier_api.get_or_retrieve_project import *
from SupplierAPI.suppliers_authDetails_file import supplier_authDetails_func
from SupplierAPI.lucid_supplier_api.buyer_surveys import *
from SupplierAPI.theorem_reach_apis.create_survey_file import *
from SupplierAPI.theorem_reach_apis.update_survey_file import *
from SupplierBuyerAPI.models import SupplierBuyerAPIModel


# Create your views here.


class APISupplierOrganisationView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = APISupplierOrganisationSerailizer
    queryset = SupplierOrganisation.objects.filter(supplier_type__in=["2","3"],supplier_status = '1')
    lookup_field = 'id'

class APISupplierOrganisationUpdateView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = UpdateAPISupplierOrganisationSerailizer
    queryset = SupplierOrganisation.objects.filter(supplier_type__in=["2","3"])
    lookup_field = 'id'

    
    @staticmethod
    def supp_buyer_create_func(data, instance):
        obj, created = SupplierBuyerAPIModel.objects.update_or_create(
                    supplier_org_id=instance,
                    defaults={'buyer_api_enable': data.get('buyer_api_enable',False), 'request_api_url':settings.OFFERWALL_BACKEND_BASE_URL},
                    )
        if created:
            uuid4_str = uuid.uuid4().hex
            secret_key = hashlib.md5(uuid4_str.encode()).hexdigest()
            obj.secret_key = secret_key
            obj.save()

    
    
    def update(self, request, *args, **kwargs):
        data = request.data
        instance = self.get_object()
        if instance.supplier_type == '3':
            try:
                supplier_rate_type = request.data.get('supplier_rate_type', None)
                supplier_rate_value = request.data.get('supplier_rate_value', None)
                if supplier_rate_type == None or supplier_rate_value == None:
                    return Response(status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
            except:
                return Response(status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

        serializer = self.get_serializer(instance, data=request.data)
        if serializer.is_valid(raise_exception=True):
            apisupplier_org_obj = serializer.save()
            apisupplier_org_obj.modified_by=request.user
            apisupplier_org_obj.save()

            # SupplierBuyerAPIModel Table Enabled/Disabled
            self.supp_buyer_create_func(data, instance)

            # API Supplier Auth Keys Store in SupplierOrgAuthKeyDetails Table
            data.update({'supplierOrg':apisupplier_org_obj.id})
            supplierOrg_authKey_resp = requests.put(settings.SURVEY_URL+settings.APP_PATH+f'api-supplier/authkey-details/{apisupplier_org_obj.supplierorgauthkeydetails.id}', json=data)
            if supplierOrg_authKey_resp.status_code != 200:
                return Response({'error':'API Supplier Auth Details Not Updated Successfully'}, status=status.HTTP_200_OK)


            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectGroupAPISupplierView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = ProjectGroupAPISupplierSerializer
    queryset = ProjectGroupSupplier.objects.filter(supplier_org__supplier_type="2")


    def create(self, request, *args, **kwargs):
        if True:
            supplier_exists = ProjectGroupSupplier.objects.filter(supplier_org=self.request.data['supplier_org'], project_group = self.request.data['project_group']).exists()
            if not(supplier_exists):
                data = request.data
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)

                supp_org = serializer.validated_data.get('supplier_org')
                project_group = serializer.validated_data.get('project_group')
                if supp_org.supplier_type not in ['2']:
                    return Response({'error': 'You do not have access to add this supplier..!'}, status=status.HTTP_400_BAD_REQUEST)
                
                # ************* BEGIN::Check Supplier url code and Check validation for loi and incidence ****************
                if supp_org.supplier_url_code in ["disqo", "Disqo"]:
                    loi = project_group.project_group_loi
                    incidence = project_group.project_group_incidence
                    if (loi > 30 or incidence < 10):
                        return Response({'error': 'You are not allowed to add disqo supplier due to lower incidence or high loi'}, status=status.HTTP_400_BAD_REQUEST)
                # ************* END::Check Supplier url code and Check validation for loi and incidence ****************
                # IF not DisqoAPI Supplier, Do not allow creating the Supplier if the CPI is more than the ProjectGroup/Survey CPI
                else:
                    if serializer.validated_data.get('cpi') > project_group.project_group_cpi:
                        return Response({'error': 'You are not allowed to add this supplier due to CPI being higher than the ProjectGroup/Survey CPI'}, status=status.HTTP_400_BAD_REQUEST)
                
                projectgrp_supp_obj = serializer.save()

                projectgrp_supp_obj.supplier_survey_url = projectgrp_supp_obj.project_group.project_group_surveyurl+"&source="+str(projectgrp_supp_obj.supplier_org.id) # +"&PID=XXXXX"
                projectgrp_supp_obj.supplier_completeurl = projectgrp_supp_obj.supplier_org.supplier_completeurl
                projectgrp_supp_obj.supplier_terminateurl = projectgrp_supp_obj.supplier_org.supplier_terminateurl 
                projectgrp_supp_obj.supplier_quotafullurl = projectgrp_supp_obj.supplier_org.supplier_quotafullurl 
                projectgrp_supp_obj.supplier_securityterminateurl = projectgrp_supp_obj.supplier_org.supplier_securityterminateurl
                projectgrp_supp_obj.supplier_internal_terminate_redirect_url = projectgrp_supp_obj.supplier_org.supplier_internal_terminate_redirect_url
                projectgrp_supp_obj.supplier_terminate_no_project_available = projectgrp_supp_obj.supplier_org.supplier_terminate_no_project_available
                projectgrp_supp_obj.supplier_postbackurl = projectgrp_supp_obj.supplier_org.supplier_postbackurl
                projectgrp_supp_obj.save(force_update=True)


                # ************* Check Supplier url code and Create Project in Lucid Buyer API ****************

                if projectgrp_supp_obj.supplier_org.supplier_url_code == 'lucid':
                    response = create_lucid_survey(projectgrp_supp_obj)
                    if response.status_code not in [201,200]:
                        ProjectGroupSupplier.objects.filter(pk=projectgrp_supp_obj.pk).delete()
                        return Response({'error':f"Lucid BuyerAPI Survey Not Created Successfully due to {response.json()['message']}"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        projectgrp_supp_obj.lucidSupplier_survey_id = response.json()['Survey']['SurveyNumber']
                        projectgrp_supp_obj.save()


                # ************* Check Supplier url code and Create Project in TheormReach API ****************

                if projectgrp_supp_obj.supplier_org.supplier_url_code == 'theormReach':
                    theorem_country_id = projectgrp_supp_obj.project_group.project_group_country.theorem_country_id
                    if theorem_country_id in [None, ""]:
                        ProjectGroupSupplier.objects.filter(pk=projectgrp_supp_obj.pk).delete()
                        return Response({'error': 'This country is not allowed at TheoremReach end.'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    func_response = create_theormReach_survey_func(projectgrp_supp_obj)
                    if func_response['status_code'] not in [200, 201]:
                        ProjectGroupSupplier.objects.filter(pk=projectgrp_supp_obj.pk).delete()
                        return Response({'error':f"TheoremReach BuyerAPI Survey Not Created Successfully due to {func_response['json_response']['errors']}"})

                # ************* Check Supplier url code and Create Project in Disqo API ****************
                if projectgrp_supp_obj.supplier_org.supplier_url_code in ["disqo", "Disqo"]:
                    disqo_retrieve_project = DisqoAPIRetrieveProjectFunc(projectgrp_supp_obj)
                    if disqo_retrieve_project.status_code in [200, 201]:
                        disqo_update_project = DisqoAPIUpdateProjectFunc(projectgrp_supp_obj)
                        return disqo_update_project
                    else:
                        disqo_create_project = DisqoAPICreateProjectFunc(projectgrp_supp_obj)
                        return disqo_create_project
                
                # ************* Check Supplier url code and Create Project in Disqo API ****************

                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            else:
                return Response(status=status.HTTP_208_ALREADY_REPORTED)


class ProjectGroupAPISupplierUpdateView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = ProjectGroupAPISupplierUpdateSerializer
    queryset = ProjectGroupSupplier.objects.filter(supplier_org__supplier_type="2")
    lookup_field = 'id'


    def update(self, request, *args, **kwargs):
        data = request.data
        
        instance = self.get_object()
        # Storing the Pre-Updated Value
        cpi_before_update = instance.cpi
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)

        projectgrp_supp_obj = serializer.save()
        projectgrp_supp_obj.supplier_completeurl = projectgrp_supp_obj.supplier_org.supplier_completeurl
        projectgrp_supp_obj.supplier_terminateurl = projectgrp_supp_obj.supplier_org.supplier_terminateurl 
        projectgrp_supp_obj.supplier_quotafullurl = projectgrp_supp_obj.supplier_org.supplier_quotafullurl 
        projectgrp_supp_obj.supplier_securityterminateurl = projectgrp_supp_obj.supplier_org.supplier_securityterminateurl
        projectgrp_supp_obj.supplier_internal_terminate_redirect_url = projectgrp_supp_obj.supplier_org.supplier_internal_terminate_redirect_url
        projectgrp_supp_obj.supplier_terminate_no_project_available = projectgrp_supp_obj.supplier_org.supplier_terminate_no_project_available
        projectgrp_supp_obj.supplier_postbackurl = projectgrp_supp_obj.supplier_org.supplier_postbackurl
        projectgrp_supp_obj.save(force_update=True)

        # Pause the Supplier Status & Reset the CPI to the Older Value if Supplier CPI greater than the Survey CPI
        if serializer.validated_data.get('cpi') > projectgrp_supp_obj.project_group.project_group_cpi:
            projectgrp_supp_obj.supplier_status = 'Paused'
            projectgrp_supp_obj.cpi = cpi_before_update
            projectgrp_supp_obj.save()


        # ************* BEGIN::Check Supplier url code and Update Project in Lucid Buyer API ****************
        if projectgrp_supp_obj.supplier_org.supplier_url_code == 'lucid':
            response = update_lucid_survey(projectgrp_supp_obj)
            if response.status_code != 200:
                return Response({'error':f"Lucid BuyerAPI Survey Not Updated Successfully due to {response.json()['message']}"})

        
        # ************* BEGIN::Check Supplier url code and Update Project in TheormReach API ****************
        if projectgrp_supp_obj.supplier_org.supplier_url_code == 'theormReach':
            theorem_country_id = projectgrp_supp_obj.project_group.project_group_country.theorem_country_id
            if theorem_country_id in [None, ""]:
                return Response({'error': 'This country is not allowed at TheoremReach end.'}, status=status.HTTP_400_BAD_REQUEST)

            func_response = update_survey_func(projectgrp_supp_obj)
            if func_response['status_code'] not in [200, 201]:
                return Response({'error':f"TheoremReach BuyerAPI Survey Not Updated Successfully due to {func_response['json_response']['errors']}"})


        # ************* BEGIN::Check Supplier url code and Update Project in Disqo API ****************
        if projectgrp_supp_obj.supplier_org.supplier_url_code in ["disqo", "Disqo"]:
            loi = projectgrp_supp_obj.project_group.project_group_loi
            incidence = projectgrp_supp_obj.project_group.project_group_incidence
            if (loi > 30 or incidence < 10):
                projectgrp_supp_obj.cpi = instance.cpi
                projectgrp_supp_obj.save(force_update=True)
                return Response({'error': 'You are not allowed to update disqo supplier due to lower incidence or high loi'}, status=status.HTTP_400_BAD_REQUEST)
            disqo_update_project = DisqoAPIUpdateProjectFunc(projectgrp_supp_obj)

            # Don't Allow the Update if the Supplier CPI is more than the Project/Survey CPI
            if disqo_update_project.status_code == 406:
                projectgrp_supp_obj.cpi = cpi_before_update
                projectgrp_supp_obj.save()
            return disqo_update_project
        
        # ************* END::Check Supplier url code and Update Project in Disqo API ****************
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectGroupAPISupplierStatusUpdateView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = ProjectGroupAPISupplierUpdateSerializer
    queryset = ProjectGroupSupplier.objects.filter(supplier_org__supplier_type="2")
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data)
        serializer.is_valid(raise_exception=True)

        # Not Allowed to Change the Status if not Live Or Paused
        if serializer.validated_data['supplier_status'] not in ('Live','Paused'):
            return Response(data={'message':'You are not allowed to change the status except for "Live" or "Paused"'}, status=status.HTTP_406_NOT_ACCEPTABLE)

        # Not Allowed to Change the Status to Live if the Supplier CPI greater than its ProjectGroup/Survey CPI
        if serializer.validated_data['supplier_status'] == 'Live':
            if self.get_object().cpi > self.get_object().project_group.project_group_cpi:
                return Response(data={'message':'You are not allowed to change the status to Live as the Supplier CPI is greater than its ProjectGroup/Survey CPI'}, status=status.HTTP_406_NOT_ACCEPTABLE)
            
        projectgrp_supp_obj = serializer.save()

        # This Supplier's Immediate Parent and its Grandparent must also go Live if this Supplier goes Live
        if projectgrp_supp_obj.supplier_status == 'Live':
            projectgrp_supp_obj.project_group.project_group_status = 'Live'
            projectgrp_supp_obj.project_group.save()
            projectgrp_supp_obj.project_group.project.project_status = 'Live'
            projectgrp_supp_obj.project_group.project.save()


        # *************Check Supplier url code and Update Project in Lucid Buyer API ****************
        if projectgrp_supp_obj.supplier_org.supplier_url_code == 'lucid':
            func_response = update_lucid_survey(projectgrp_supp_obj)
            if func_response.status_code not in [200, 201]:
                return Response({'error':f"Lucid BuyerAPI Survey Status Not Updated Successfully due to {func_response.json()['message']}"})

        # *************Check Supplier url code and Update Project in TheormReach API ****************
        if projectgrp_supp_obj.supplier_org.supplier_url_code == 'theormReach':
            func_response = update_theorem_status(projectgrp_supp_obj)
            if func_response['status_code'] not in [200, 201] or func_response['json_response'].get('errors'):
                return Response({'error':f"TheoremReach BuyerAPI Survey Status Not Updated Successfully due to {func_response['json_response']['errors']}"})

        # ************* Check Supplier url code and Create Project in Disqo API ****************
        if projectgrp_supp_obj.supplier_org.supplier_url_code in ["disqo", "Disqo"]:
            disqo_update_project_status = DisqoAPIUpdateProjectStatusFunc(projectgrp_supp_obj)
            return disqo_update_project_status
        
        # ************* Check Supplier url code and Create Project in Disqo API ****************
        return Response(serializer.data, status=status.HTTP_200_OK)


class APISupplierRespondentDetailView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = APISupplierRespondentDetailSerializer

    def get(self, request, supplier_id, project_group_num):
        
        supplier_respondent_data = RespondentDetail.objects.filter(
            source=supplier_id, project_group_number=project_group_num).exclude(source=0)
        
        serializer = self.serializer_class(supplier_respondent_data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class APISupplierWithStatView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = APISupplierWithStatsSerializer

    def get(self, request, project_group_num):
        supplier_type = request.GET.get('supplier_type')

        if supplier_type != None:
            grp_supp_list = ProjectGroupSupplier.objects.filter(project_group__project_group_number=project_group_num, supplier_org__supplier_type=supplier_type)
        else:
            grp_supp_list = ProjectGroupSupplier.objects.filter(project_group__project_group_number=project_group_num, supplier_org__supplier_type="2")

        
        if grp_supp_list.count() > 0:
            resp_detail_obj = RespondentDetail.objects.filter(project_group_number=project_group_num, url_type="Live")
            serializer = self.serializer_class(grp_supp_list, context={"resp_detail_obj":resp_detail_obj}, many=True)
            return Response(serializer.data)
        else:
            return Response({'error': "No data found for the provided ProjectGroup-Number..!"}, status=status.HTTP_404_NOT_FOUND)


class APISupplierWithTermReportView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = APISupplierWithReportTermSerializer

    def get(self, request, project_group_num):

        grp_supp_list = ProjectGroupSupplier.objects.filter(project_group__project_group_number=project_group_num, supplier_org__supplier_type="2")
        if grp_supp_list.count() > 0:
            resp_detail_obj = RespondentDetail.objects.filter(project_group_number=project_group_num, url_type="Live")
            serializer = self.serializer_class(grp_supp_list, context={"resp_detail_obj":resp_detail_obj}, many=True)
            return Response(serializer.data)
        else:
            return Response({'error': "No data found for the provided ProjectGroup-Number..!"}, status=status.HTTP_404_NOT_FOUND)