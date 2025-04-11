# django imports
from django.db.utils import IntegrityError
import requests

# rest_framework libraries
from Logapp.views import projectgroupprescreener_log
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics

# third party libraries
from knox.auth import TokenAuthentication
from Supplier.models import SupplierOrgAuthKeyDetails
from SupplierAPI.disqo_supplier_api.create_or_update_project import DisqoAPIUpdateProjectFunc
from SupplierAPI.disqo_supplier_api.custom_functions import get_project_detail, get_quotas_details
from SupplierAPI.lucid_supplier_api.buyer_surveys import create_lucid_survey_Qualifications, update_lucid_survey_Qualifications
from SupplierAPI.theorem_reach_apis.update_survey_file import update_survey_func
from supplierdashboard.paginations import MyPageNumberPagination

# in app imports
from .models import *
from .serializers import *

class PrescreenerQuestionListView(generics.ListAPIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PreScreenerQuestionListSerializer
    pagination_class = MyPageNumberPagination

    def get_queryset(self):
        question_type = self.request.GET.get("question_type", "")
        question_text = self.request.GET.get("question_text","")
        
        try:
            project_group_obj = ProjectGroup.objects.get(project_group_number=self.kwargs['project_group_number'])
        except:
            return Response({'error':'No Project Group found with that number'}, status=status.HTTP_404_NOT_FOUND)
                
        # CT type toluna questions, excludeed due to not configured
        screener_list = TranslatedQuestion.objects.filter(
                apidbcountrylangmapping__lanugage_id__id=project_group_obj.project_group_language.id,
                apidbcountrylangmapping__country_id = project_group_obj.project_group_country,
                is_active = True
            ).exclude(
                Q(parent_question_type = 'CT') | Q(toluna_question_id__in = [1001033,1001018])
            ).order_by('translated_question_text')
        
        if question_text not in ['', None]:
            screener_list = screener_list.filter(parent_question__parent_question_text__icontains=question_text)
        if question_type not in ['', None]:
            if question_type == 'Custom':
                screener_list = screener_list.filter(parent_question_prescreener_type=question_type)
            elif question_type == 'Standard':
                screener_list = screener_list.filter(parent_question_prescreener_type=question_type)
            elif question_type == 'lucid':
                screener_list = screener_list.exclude(lucid_question_id__exact='')
            elif question_type == 'disq':
                screener_list = screener_list.exclude(disqo_question_key__exact='')
        return screener_list


class PrescreeneranswerView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            answers_data = TranslatedAnswer.objects.filter(
                translated_parent_question__id = kwargs['transalted_question_id'])
            serializer = PreScreenerAnswerListSerializer(answers_data,many= True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except:
            return Response({"error":"Invalid Question Id"}, status=status.HTTP_400_BAD_REQUEST)


class SurveyPreScreenerView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PreScreenerQuestionSerializer

    def get(self, request, project_group_number):

        survey_screener_list = ProjectGroupPrescreener.objects.filter(project_group_id__project_group_number=project_group_number,is_enable=True)

        if survey_screener_list:
            serialize = SurveyPrescreenerViewSerializer(survey_screener_list, many=True)
            return Response(serialize.data, status=status.HTTP_200_OK)
        else:
            return Response({'error':'No data found for provided Project Group Number'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, project_group_number):
        
        if TranslatedQuestion.objects.get(id=request.data['translated_question_id']).parent_question_type == 'CTZIP' and not any(ProjectGroupPrescreener.objects.filter(project_group_id__project_group_number=project_group_number,is_enable = True,translated_question_id__parent_question_type = 'ZIP')):
            return Response({'error':'First Need To Add ZipCode Question'}, status=status.HTTP_400_BAD_REQUEST)
        
        if TranslatedQuestion.objects.get(id=request.data['translated_question_id']).parent_question_type == 'FU' and any(ProjectGroupPrescreener.objects.filter(project_group_id__project_group_number=project_group_number,is_enable = True,translated_question_id__parent_question_type = 'FU')):
            return Response({'error':'File Upload Type Question Already Added'}, status=status.HTTP_400_BAD_REQUEST)
        
        if TranslatedQuestion.objects.get(id=request.data['translated_question_id']).parent_question_type == 'FU' and len(ProjectGroupPrescreener.objects.filter(project_group_id__project_group_number=project_group_number,is_enable = True)) == 0:
            return Response({'error':'Need To Add Any One Quetion Before Add File Upload Question'}, status=status.HTTP_400_BAD_REQUEST)
        
        if TranslatedQuestion.objects.get(id=request.data['translated_question_id']).parent_question_type == 'ZIP':
            return Response(status=status.HTTP_200_OK)
        
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            project_group_obj = ProjectGroup.objects.get(project_group_number = project_group_number)
            serializer.validated_data['project_group_id'] = project_group_obj
            serializer.save(created_by=request.user)
            projectgroupprescreener_log(serializer.data,'',serializer.data['id'],project_group_obj.id,request.user)
            try:
                projectgrp_supp_qs = ProjectGroupSupplier.objects.filter(project_group__project_group_number=project_group_number)
                if projectgrp_supp_qs:
                    for projectgrp_supp_obj in projectgrp_supp_qs:

                        # If the Supplier is DISQO API
                        if projectgrp_supp_obj.supplier_org.supplier_url_code in ["disqo", "Disqo"] and TranslatedQuestion.objects.get(id=request.data['translated_question_id']).disqo_question_id not in ['',None]:
                            DisqoAPIUpdateProjectFunc(projectgrp_supp_obj)

                        # *******If the Supplier is Lucid Buyer API **********
                        if projectgrp_supp_obj.supplier_org.supplier_url_code == 'lucid' and TranslatedQuestion.objects.get(id=request.data['translated_question_id']).lucid_question_id not in ['',None]:
                            create_lucid_survey_Qualifications(projectgrp_supp_obj,serializer)

                        # *********If the Supplier is TheormReach API ************
                        if projectgrp_supp_obj.supplier_org.supplier_url_code == 'theormReach':
                            update_survey_func(projectgrp_supp_obj)
                return Response({'success': 'Question Update Successfully..!'}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SurveyPreScreenerV2View(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PreScreenerQuestionSerializer

    def get(self, request, project_group_number):

        survey_screener_list = ProjectGroupPrescreener.objects.filter(project_group_id__project_group_number=project_group_number,is_enable=True)

        if survey_screener_list:
            serialize = SurveyPrescreenerV2Serializer(survey_screener_list, many=True)
            return Response(serialize.data, status=status.HTTP_200_OK)
        else:
            return Response({'error':'No data found for provided Project Group Number'}, status=status.HTTP_404_NOT_FOUND)

       
class SurveyDiquePreScreenerView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_group_number):
        try:
            authkey_detail_obj = SupplierOrgAuthKeyDetails.objects.get(supplierOrg__supplier_url_code__in=['disqo','DISQO'])
            clientId = authkey_detail_obj.client_id
            base_url = authkey_detail_obj.staging_base_url
            headers = {
                    'Content-Type': 'application/json',
                    'Authorization': authkey_detail_obj.authkey
                }
            resp = requests.get(f'{base_url}/v1/clients/{clientId}/projects/{project_group_number}/quotas/QUOTA-{project_group_number}',headers=headers)
            question_list = []
            if resp.status_code in [200, 201]:
                res_data = resp.json()['qualifications']['and']
                for question in res_data:
                    if 'range' in question:
                        question_obj = TranslatedQuestion.objects.get(disqo_question_key = question['range']['question'])
                        question_list.append({'question': question_obj.internal_question_text,'answers':question['range']['values'],'question_type':'range'})
                    if 'equals' in question:
                        question_obj = TranslatedQuestion.objects.get(disqo_question_key = question['equals']['question'])
                        if question['equals']['question'] == 'geopostalcode':
                            answer_obj = question['equals']['values']
                        else:
                            answer_obj = TranslatedAnswer.objects.filter(
                                disqo_question_key = question['equals']['question'],
                                disqo_answer_id__in = question['equals']['values']).values_list('answer_internal_name',flat=True)
                        question_list.append({'question': question_obj.internal_question_text,'answers':answer_obj,'question_type':'options'})
                return Response(data=question_list, status=status.HTTP_200_OK)
            else:
                return Response({'error':'No data found for provided Project Group Number'}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({'error':'No data found for provided Project Group Number'}, status=status.HTTP_400_BAD_REQUEST)


class SurveyLucidPreScreenerView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request,project_group_number):
        try:
            prjgrp_supplier_obj = ProjectGroupSupplier.objects.get(project_group__project_group_number = project_group_number, supplier_org__supplier_url_code = 'lucid')
            survey_base_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+f'/Demand/v1/SurveyQualifications/BySurveyNumber/{prjgrp_supplier_obj.lucidSupplier_survey_id}'

            headers = {'Authorization' : prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.api_key}

            response = requests.get(survey_base_url, headers=headers)
            if response.status_code in [200, 201]:
                question_list = []
                res_data = response.json()['Qualifications']
                for question in res_data:
                    question_obj = TranslatedQuestion.objects.get(lucid_question_id = question['QuestionID'])
                    if question['QuestionID'] not in [45,42]:
                        PreCodes = list(TranslatedAnswer.objects.filter(
                                lucid_answer_id__in = question['PreCodes'],lucid_question_id = question['QuestionID']).values_list('answer_internal_name',flat=True))
                    else:
                        PreCodes = question['PreCodes']
                    question_list.append({'question': question_obj.internal_question_text,'answers': PreCodes})

            return Response(data=question_list, status=status.HTTP_200_OK)
        except:
            return Response({'error':'No data found for provided Project Group Number'}, status=status.HTTP_400_BAD_REQUEST)


class SurveyPreScreenerUpdatesView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PreScreenerQuestionUpdateSerializer

    def get_object(self, prescreener_question_id):

        try:
            prescreener_obj = ProjectGroupPrescreener.objects.filter(id=prescreener_question_id)
            return prescreener_obj
        except:
            None

    def get(self, request, prescreener_question_id):

        instance = self.get_object(prescreener_question_id)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Given Pre Screener Question object not found..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, prescreener_question_id):
        project_group_number = request.data['project_group_number']
        translated_question_id = request.data['translated_question_id']
        allowed_options = request.data['allowed_options']
        allowed_min_range = request.data.get('allowed_min_range', 0)
        allowed_max_range = request.data.get('allowed_max_range', 100)
        sequence = request.data['sequence']

        try:
            instance = ProjectGroupPrescreener.objects.get(id = prescreener_question_id,project_group_id__project_group_number = project_group_number)
            if instance.translated_question_id.Internal_question_id == '112498':
                return Response(status=status.HTTP_200_OK)
            instance.allowedoptions.set(allowed_options)
            instance.sequence = sequence
            instance.allowedRangeMin = allowed_min_range
            instance.allowedRangeMax = allowed_max_range
            instance.is_enable = True
            instance.save()

            projectgrp_supp_qs = ProjectGroupSupplier.objects.select_related('project_group').filter(project_group__project_group_number=instance.project_group_id.project_group_number)
            if projectgrp_supp_qs:
                for projectgrp_supp_obj in projectgrp_supp_qs:

                    # If the Supplier is DISQO API
                    if projectgrp_supp_obj.supplier_org.supplier_url_code in ["disqo", "Disqo"]:
                        disqo_update_project = DisqoAPIUpdateProjectFunc(projectgrp_supp_obj)

                    # *******If the Supplier is Lucid Buyer API **********
                    if projectgrp_supp_obj.supplier_org.supplier_url_code == 'lucid':
                        update_lucid_survey_Qualifications(projectgrp_supp_obj,instance.id)


                    # *********If the Supplier is TheormReach API ************
                    if projectgrp_supp_obj.supplier_org.supplier_url_code == 'theormReach':
                        update_survey_func(projectgrp_supp_obj)

            #END:: Add Questions & it's Answers for every Supplier who is subscribed to this Survey/ProjectGroup
            return Response({"success":"Prescreener Questions Update successfully..!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, prescreener_question_id):
        try:
            prescreener_obj = ProjectGroupPrescreener.objects.get(id=prescreener_question_id)
            if prescreener_obj.translated_question_id.parent_question_type == 'ZIP' and any(ProjectGroupPrescreener.objects.filter(project_group_id=prescreener_obj.project_group_id,is_enable = True,translated_question_id__parent_question_type = 'CTZIP')):
                return Response({'error':'First Need To Remove ComputedTypeZip Question'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                prescreener_obj.is_enable = False
                prescreener_obj.allowed_zipcode_list = []
                prescreener_obj.save()
                project_group_supplier = ProjectGroupSupplier.objects.filter(project_group = prescreener_obj.project_group_id)
                supplier_exists = list(project_group_supplier.values_list('supplier_org__supplier_url_code',flat = True))
                
                if 'lucid' in supplier_exists:
                    prjgrp_supplier_obj = project_group_supplier.get(supplier_org__supplier_url_code = 'lucid')
                    headers = {'Authorization' : prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.api_key}
                    survey_update_base_url = prjgrp_supplier_obj.supplier_org.supplierorgauthkeydetails.production_base_url+f'/Demand/v1/SurveyQualifications/Update/{prjgrp_supplier_obj.lucidSupplier_survey_id}'
                    PreCodes = list(prescreener_obj.allowedoptions.values_list('lucid_answer_id',flat=True))
                    params = {
                        "Name": "STANDARD_RELATIONSHIP",
                        "QuestionID": prescreener_obj.translated_question_id.lucid_question_id,
                        "LogicalOperator": "OR",
                        "NumberOfRequiredConditions": 1,
                        "IsActive": False,
                        "PreCodes": list(filter(None, PreCodes)),
                        "MaxPunch": -1
                    }
                    requests.put(survey_update_base_url,json=params, headers=headers)

                if 'disqo' in supplier_exists:
                    prjgrp_supplier_obj = project_group_supplier.get(supplier_org__supplier_url_code = 'disqo')
                    authkey_detail_obj = SupplierOrgAuthKeyDetails.objects.get(supplierOrg__supplier_url_code__in=['disqo','DISQO'])
                    headers = {'Content-Type': 'application/json','Authorization': authkey_detail_obj.authkey}
                    clientId = authkey_detail_obj.client_id
                    base_url = authkey_detail_obj.staging_base_url
                    supplierId = authkey_detail_obj.supplier_id
                    dict_payload = get_project_detail(prjgrp_supplier_obj, supplierId)
                    dict_payload_2 = get_quotas_details(dict_payload)
                    quotas_id = dict_payload_2['id']
                    requests.put(
                            f'{base_url}/v1/clients/{clientId}/projects/{prjgrp_supplier_obj.project_group.project_group_number}/quotas/{quotas_id}',
                            json=dict_payload_2,
                            headers=headers)
                projectgroupprescreener_log('',f"Delete - {prescreener_obj.translated_question_id.translated_question_text}",prescreener_obj.id,prescreener_obj.project_group_id.id,request.user)
                return Response({'Disable':'Question removed successfully'}, status=status.HTTP_202_ACCEPTED)
        except:
                return Response({'error': 'Given PreScreener Question object not found..!'}, status=status.HTTP_404_NOT_FOUND)


class SurveyPreScreenerDeleteView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = PreScreenerQuestionUpdateSerializer

    def get_object(self, prescreener_question_id):

        try:
            del_obj = ProjectGroupPrescreener.objects.get(id=prescreener_question_id)
            return del_obj
        except:
            None

    def get(self, request, prescreener_question_id):

        instance = self.get_object(prescreener_question_id)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Given Pre Screener Question object not found..!'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, prescreener_question_id):

        instance = self.get_object(prescreener_question_id)
        if instance != None:
            instance.delete()
            return Response({'Deleted':'Object deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'Given Pre Screener Question object not found..!'}, status=status.HTTP_404_NOT_FOUND)


class SurveyPreScreenerApiView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SurveyPrescreenerApiViewSerializer

    def get(self, request, project_group_number):

        survey_screener_list = ProjectGroupPrescreener.objects.filter(project_group_id__project_group_number=project_group_number, is_enable = True)

        if survey_screener_list:
            serialize = self.serializer_class(survey_screener_list, many=True)
            return Response(serialize.data, status=status.HTTP_200_OK)
        else:
            return Response({'error':'No data found for provided Project Group Number'}, status=status.HTTP_404_NOT_FOUND)


class SupplierPrescreenerEnabledAPI(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, proj_grp_supplier):
        enabled_questions = request.data['enabled_questions'].split(',') if request.data.get('enabled_questions') not in (None,'') else None

        if enabled_questions:
            ProjectGroupSupplierPrescreenerEnabled.objects.filter(prj_grp_supplier_id=proj_grp_supplier).delete()

            prj_grp_supp_prescnr_list = [ProjectGroupSupplierPrescreenerEnabled(prj_grp_supplier_id=proj_grp_supplier, prj_grp_prescreener_id=question) for question in enabled_questions]
            
            try:
                ProjectGroupSupplierPrescreenerEnabled.objects.bulk_create(prj_grp_supp_prescnr_list)
            except IntegrityError:
                return Response(data={'message':'One of the enabled_questions not found, Please insert all the correct ones'}, status=status.HTTP_400_BAD_REQUEST)

            response = ProjectGroupSupplierPrescreenerEnabled.objects.values()
            return Response(data=response, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'message':'Please insert enabled_questions in the request body'})


    def get(self, request, proj_grp_supplier):

        response = ProjectGroupSupplierPrescreenerEnabled.objects.values()
        return Response(data=response)


class ProjectGroupPrescreenerCopyView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    def post(self, request, old_project_group_id,new_project_group_id):
        pgs_obj = ProjectGroupPrescreener.objects.filter(project_group_id__id=old_project_group_id, is_enable = True)
        try:
            pg_obj = ProjectGroup.objects.get(id=new_project_group_id)
        except:
            return Response({'message':'Invalid Survey Number'}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        for obj1 in pgs_obj:
            allowedoptions_list = obj1.allowedoptions.all()
            pgs_obj_new = ProjectGroupPrescreener.objects.create(
                project_group_id_id = new_project_group_id,
                translated_question_id = obj1.translated_question_id,
                allowedRangeMin = obj1.allowedRangeMin,
                allowedRangeMax = obj1.allowedRangeMax,
                sequence = obj1.sequence,
                created_by = request.user,
                old_projectgroup_prescreener_id = obj1.old_projectgroup_prescreener_id,
            )
            if allowedoptions_list:
                pgs_obj_new.allowedoptions.set(allowedoptions_list)
                pgs_obj_new.save()
            else:
                pass
        if project_zipcode := ZipCode.objects.filter(project_group_id__id=old_project_group_id):
            project_zipcode_list = []
            for zip in project_zipcode:
                project_zipcode_list.append(ZipCode(project_group_id = pg_obj, zip_code = zip.zip_code, uploaded_by = request.user))
            ZipCode.objects.bulk_create(project_zipcode_list)
        return Response({'message':'Data Created Successfully'}, status=status.HTTP_201_CREATED)
    

class PrescreenerSequenceUpdateApi(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def post(self, request, project_group_number):

        data = request.data

        for prescreener_id in data:

            try:
                prescreener_obj = ProjectGroupPrescreener.objects.get(id = prescreener_id['prescreener_question_id'],project_group_id__project_group_number = project_group_number,is_enable = True)
                prescreener_obj.sequence = prescreener_id['sequence']
                prescreener_obj.save()

            except Exception as e:
                return Response({'error':'No data found..!'}, status=status.HTTP_400_BAD_REQUEST)

        
        return Response({'success':'Sequence Update Successfully..!'}, status=status.HTTP_200_OK)

