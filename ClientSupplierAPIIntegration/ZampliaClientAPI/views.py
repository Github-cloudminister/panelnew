import requests
from django.conf import settings

#Restframework import
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.views import APIView

#App import
from ClientSupplierAPIIntegration.TolunaClientAPI.models import ClientLayer, ClientQuota, ClientSubQuota, ClientSurveyPrescreenerQuestions
from Prescreener.models import ProjectGroupPrescreener
from Project.models import ProjectGroup
from knox.auth import TokenAuthentication
from Questions.models import TranslatedAnswer, TranslatedQuestion


class ClientDBZampliaQuotaUpdate(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        survey_number = request.data['survey_number']
        prescreener_question_dict = {}
        added_question = []
        zamplia_base_url = settings.STAGING_URL
        headers = {'Accept' : 'application/json','ZAMP-KEY' : settings.STAGING_KEY}

        prjgrp_obj = ProjectGroup.objects.get(project_group_number = survey_number)
        client_quotas = requests.get(f'{zamplia_base_url}/Surveys/GetSurveyQuotas?SurveyId={survey_number}', headers=headers)
        client_qualifications = requests.get(f'{zamplia_base_url}/Surveys/GetSurveyQualifications?SurveyId={survey_number}', headers=headers)
        if client_quotas.status_code not in [200,201] and client_qualifications.status_code not in [200,201]:
            return
        client_quotas = client_quotas.json()['result']['data']
        client_qualifications = client_qualifications.json()['result']['data']
        for quota in client_quotas:
            client_quota_obj, created = ClientQuota.objects.update_or_create(
            quota_id=quota['QuotaId'],
            defaults={
                'completes_required':quota['TotalQuotaCount'],
                'completes_remaining':quota['TotalQuotaCount'],
                'quota_json_data':quota})
            client_layer_obj, created = ClientLayer.objects.update_or_create(
                layer_id=quota['QuotaId'],
                client_quota=client_quota_obj)
            client_subquota_obj, created = ClientSubQuota.objects.update_or_create(
                subquota_id=quota['QuotaId'],
                client_layer=client_layer_obj,
                defaults={
                    'target_completes':quota['TotalQuotaCount']})
            
            for que_ans in quota['QuotaQualifications']:
                allowed_Range_Min = ""
                allowed_Range_Max = ""

                try:
                    ques_mapping_obj = TranslatedQuestion.objects.get(zamplia_question_id=que_ans['QuestionId'])
                    
                    ques_ans_obj, created = ClientSurveyPrescreenerQuestions.objects.update_or_create(
                        client_subquota=client_subquota_obj,
                        client_question_mapping=ques_mapping_obj,
                        defaults = {
                            "allowedRangeMin" : allowed_Range_Min,
                            "allowedRangeMax" : allowed_Range_Max,
                            "client_name" : "Zamplia"
                            })
                    
                    if ques_mapping_obj.parent_question_type == 'NU':
                        answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj).values_list('id',flat=True))
                        for anscode in que_ans['AnswerCodes']:
                            if allowed_Range_Min not in ["", None]:
                                    allowed_Range_Min = f"{allowed_Range_Min},{anscode.split('-')[0]}"
                                    allowed_Range_Max = f"{allowed_Range_Max},{anscode.split('-')[1]}"
                            else:
                                allowed_Range_Min = anscode.split('-')[0]
                                allowed_Range_Max = anscode.split('-')[1]
                    else:
                        allowed_Range_Min = "0"
                        allowed_Range_Min = "100"
                        answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj, 
                        zamplia_answer_id__in = que_ans['AnswerCodes']).values_list('id',flat=True))

                    ques_ans_obj.client_answer_mappings.clear()
                    ques_ans_obj.client_answer_mappings.add(*answer_qs)
                    ques_ans_obj.allowedRangeMin = allowed_Range_Min
                    ques_ans_obj.allowedRangeMax = allowed_Range_Max
                    ques_ans_obj.save()
                except:
                    continue
        
        for qualification in client_qualifications:
                
                allowedRangeMin = ""
                allowedRangeMax = ""
                allowedZipList = []
                try:
                    ques_mapping_obj = TranslatedQuestion.objects.get(zamplia_question_id=qualification['QuestionID'])
                    
                    if qualification['QuestionID'] in [2,'2']:
                        allowedZipList = qualification['AnswerCodes']

                    if ques_mapping_obj.parent_question_type == 'NU':
                        answer_qs = list(TranslatedAnswer.objects.filter(translated_parent_question = ques_mapping_obj).values_list('id',flat=True))
                        for anscode in qualification['AnswerCodes']:
                            if allowedRangeMin not in ["", None]:
                                    allowedRangeMin = f"{allowedRangeMin},{anscode.split('-')[0]}"
                                    allowedRangeMax = f"{allowedRangeMax},{anscode.split('-')[1]}"
                            else:
                                allowedRangeMin = anscode.split('-')[0]
                                allowedRangeMax = anscode.split('-')[1]
                    else:
                        allowedRangeMin = "0"
                        allowedRangeMax = "100"
                        answer_qs = list(TranslatedAnswer.objects.filter( 
                        zamplia_answer_id__in = qualification['AnswerCodes']).values_list('id',flat=True))
                    
                    if ques_mapping_obj in added_question:
                            # When question is already added in dict and we just need to update the Answer options and min-max ranges
                            prescreener_question_dict[ques_mapping_obj]['allowedoptions']+=answer_qs
                            if allowedRangeMin not in prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']:
                                prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMin']},{allowedRangeMin}"
                                prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']=f"{prescreener_question_dict[ques_mapping_obj]['allowedRangeMax']},{allowedRangeMax}"
                    else:
                        # When the question is added first time. 
                        added_question.append(ques_mapping_obj)
                        prescreener_question_dict[ques_mapping_obj] = {
                            "allowedoptions" : answer_qs,
                            "allowedRangeMin" : allowedRangeMin,
                            "allowedRangeMax" : allowedRangeMax,
                        }
                except:
                    continue

        seq = 4
        ProjectGroupPrescreener.objects.filter(project_group_id = prjgrp_obj).update(is_enable = False)
        for question_key, values in prescreener_question_dict.items():
            if question_key == '1001538':
                values.update({'sequence' : 1})
            elif question_key == '1001007':
                values.update({'sequence' : 2})
            elif question_key == '1001042':
                values.update({'sequence' : 3})
            else:
                values.update({'sequence' : seq})
                seq+=1
            ques_answer_obj, created = ProjectGroupPrescreener.objects.update_or_create(
                            project_group_id = prjgrp_obj,
                            translated_question_id = question_key,
                            defaults = {
                            "allowedRangeMin" : values['allowedRangeMin'],
                            "allowedRangeMax" : values['allowedRangeMax'],
                            "sequence" : values['sequence'],
                            "is_enable" : True
                            }
                        )
            if question_key.Internal_question_id == '112498':
                ques_answer_obj.allowed_zipcode_list = allowedZipList
                ques_answer_obj.save()
            ques_answer_obj.allowedoptions.clear()
            ques_answer_obj.allowedoptions.add(*values['allowedoptions'])
        return Response({"message":"Survey Quota Updated Successfully"}, status=status.HTTP_200_OK)
