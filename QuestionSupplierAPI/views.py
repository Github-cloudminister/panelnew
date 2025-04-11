# ************ rest-framework ***************
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication

# ********** in-project imports **************
from Project.models import *
from Prescreener.models import *
from Surveyentry.models import *
from QuestionSupplierAPI.serializers import *

# ********** third-party libraries **************
import json


class QuestionsMappingDetailView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = RetrieveQuestionAnswersSerializer
    
    def get(self, request):
        data = request.GET
        try:
            quesmapp_obj = QuestionsMapping.objects.get(parent_que_id_id=data.get('parent_que_id'),supplier_org_id=data.get('supplier_id'))
        except QuestionsMapping.DoesNotExist:
            try:
                parent_que_obj = ParentQuestion.objects.get(id=data.get('parent_que_id'))
                response_dict = {}
                answers_list = []
                response_dict['id'] = ''
                response_dict['parent_que_id'] = parent_que_obj.id
                response_dict['supplier_org'] = data.get('supplier_id')
                response_dict['parent_que_text'] = parent_que_obj.parent_question_text
                response_dict['supplier_api_que_key'] = ''
                for answer in parent_que_obj.parentanswer_set.all():
                    answers_list.append({'id':'','parent_ans_id':answer.id,'parent_ans_text':answer.parent_answer_text,'supplier_api_ans_key':'', 'supplier_api_ans_parameter':''})
                response_dict['answersmapping_set'] = answers_list
                return Response(response_dict, status=status.HTTP_200_OK)
            except ParentQuestion.DoesNotExist:
                return Response({'detail':'No Parent Question Record found for this Question'}, status=status.HTTP_200_OK)
        serializer = self.serializer_class(instance=quesmapp_obj, context={'supplier_id': data.get('supplier_id')})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        serializer_resp = serializer.save()
        if serializer_resp == False:
            try:
                ques_mapping_qs = QuestionsMapping.objects.filter(parent_que_id=data['parent_que_id'],supplier_org=data['supplier_org'])
                ques_mapping_qs.update(parent_que_id=data['parent_que_id'],supplier_org=data['supplier_org'],supplier_api_que_key=data['supplier_api_que_key'], supplier_api_que_parameter=data.get('supplier_api_que_parameter'))
                ques_mapping_qs[0].answersmapping_set.all().delete()
                for answer in data['answersmapping_set']:
                    try:
                        AnswersMapping.objects.create(ques_mapping_id=ques_mapping_qs[0],supplier_org_id=data['supplier_org'],parent_ans_id_id=answer['parent_ans_id'],supplier_api_ans_key=answer['supplier_api_ans_key'], supplier_api_ans_parameter=data.get('supplier_api_ans_parameter'))
                    except:
                        pass
                return Response({'detail':'QuestionMapping Updated Successfully'}, status=status.HTTP_200_OK)
            except IntegrityError:
                return Response({'error':'Same Questions/Answers cannot be updated for the same Supplier Organization'},status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail':'QuestionMapping and its related AnswersMapping created Successfully'},status=status.HTTP_201_CREATED)


class SupplierOrgMappedQuestionsView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SupplierOrgMappedQuestionSerializer
    
    def get(self, request):
        try:
            supplier_org_obj = SupplierOrganisation.objects.get(pk=request.GET['supplier_id'])
        except SupplierOrganisation.DoesNotExist:
            return Response({'detail':'No Record found for this Supplier Organization'}, status=status.HTTP_200_OK)
        serializer = self.serializer_class(instance=supplier_org_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)