from io import BytesIO
from django.http import HttpResponse
from django.db.models import Q

# rest_framework imports
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet

# third_party module imports
from knox.auth import TokenAuthentication
import xlsxwriter
from Questions.filters import ParentQuestionsFilter

# in-project imports
from .serializers import *
from .models import *


class QuestionCategoryView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 
    serializer_class = QuestionCategorySerializer

    def get(self, request):

        qcat_list = QuestionCategory.objects.all()
        serializer = self.serializer_class(qcat_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ParentQuestionView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 
    serializer_class = ParentQuestionSerializer

    def get(self, request):
        question_type = request.GET.get('question_type',None)
        if question_type!=None:
            pquestion_list = ParentQuestion.objects.filter(parent_question_type = question_type)
        else:
            pquestion_list = ParentQuestion.objects.all()
        serializer = self.serializer_class(pquestion_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            quote = serializer.save(created_by=request.user)
            quote.parent_question_number = f'CST{100000 + quote.id}'
            quote.internal_parent_question_text = quote.parent_question_text
            quote.is_active = True
            quote.save()
            TranslatedQuestion.objects.filter(parent_question=quote).update(
                Internal_question_id = quote.parent_question_number,
                internal_question_text = quote.parent_question_text,
                apidbcountrylangmapping = quote.apidbcountrylangmapping)
            for answer in request.data['answrList']:
                answeobj = ParentAnswer.objects.create(
                    internal_question_id = quote.parent_question_number,
                    answer_internal_name = answer['parent_answer_text'],
                    exclusive = answer['isExclusive'],
                    numeric_min_range = answer['numeric_min_range'],
                    numeric_max_range = answer['numeric_max_range'],
                    parent_answer_text = answer['parent_answer_text'],
                    parent_question = quote,
                    sequence = answer['sequence'],
                    created_by = request.user
                )
                answeobj.parent_answer_id = f'CST{100000 + answeobj.id}'
                answeobj.save()
                TranslatedAnswer.objects.filter(parent_answer=answeobj).update(
                    internal_question_id = answeobj.internal_question_id,
                    internal_answer_id = f'CST{100000 + answeobj.id}',
                    translated_answer = answeobj.parent_answer_text,
                    answer_internal_name = answeobj.answer_internal_name
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ParentQuestionCreateCSVDownloadXLSX(ListAPIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = ParentQuestion.objects.all()
    serializer_class = ParentQuestionSerializer
    filterset_class = ParentQuestionsFilter

    def get(self, request):
        response_type = request.GET.get('response_type')
        
        if response_type == 'json':
            response = super().get(request)
            return response

        elif response_type == 'xlsx':
            queryset = self.filter_queryset(self.get_queryset())

            in_memory = BytesIO()
            workbook = xlsxwriter.Workbook(in_memory)
            worksheet = workbook.add_worksheet('Questions')
            head_columns = ['ID#', 'Number','Text','Type','Category','Prescreener Type','Created By']
            cell_format = workbook.add_format({'bold': True, 'italic':True, 'bg_color': 'yellow'})
            column_incr = 0
            for column in head_columns:
                worksheet.set_column(column_incr, column_incr, len(column)+10)
                worksheet.write(0, column_incr, column, cell_format)
                column_incr+=1
            worksheet.set_column(5, 5, 10)
            worksheet.set_column(4, 4, 20)
            worksheet.set_column(2, 2, 30)

            data_row_incr = 1
            for question in queryset:
                data_column_incr = 0
                worksheet.write(data_row_incr, data_column_incr, question.id)
                data_column_incr+=1
                worksheet.write(data_row_incr, data_column_incr, question.parent_question_number)
                data_column_incr+=1
                worksheet.write(data_row_incr, data_column_incr, question.parent_question_text)
                data_column_incr+=1
                worksheet.write(data_row_incr, data_column_incr, question.get_parent_question_type_display())
                data_column_incr+=1
                worksheet.write(data_row_incr, data_column_incr, question.parent_question_category.category)
                data_column_incr+=1
                worksheet.write(data_row_incr, data_column_incr, question.get_parent_question_prescreener_type_display())
                data_column_incr+=1
                worksheet.write(data_row_incr, data_column_incr, question.created_by.first_name if question.created_by else None)
                data_column_incr+=1
                data_row_incr+=1

            workbook.close()

            response = HttpResponse(in_memory.getvalue(), content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=Parent Questions API.xlsx'
            return response

        else:
            return Response(data={'message':'Please specify response_type to either json or xlsx'}, status=status.HTTP_400_BAD_REQUEST)
        


    def post(self, request):
        decoded_list = ((request.data['questions'].read().decode()).split(','))

        final_list = []
        saved_item = 0
        for item in range(len(decoded_list)):
            if '\n' in decoded_list[item] or '\r' in decoded_list[item]:
                sub_list = []
                sub_list = decoded_list[saved_item:item+1]
                saved_item = item+1
                final_list.append(sub_list)

        for item in range(len(final_list)):
            try:
                asdsad = final_list[item][-1].split('\n')
                final_list[item][-1] = asdsad[0].strip('\r')
                final_list[item+1].insert(0,asdsad[1])
            except IndexError:
                pass

        parent_que_obj_list = [ParentQuestion(parent_question_number=item[0],parent_question_text=item[1],parent_question_type=item[2],parent_question_category_id=item[3],parent_question_prescreener_type=item[4],created_by=request.user) for item in final_list[1:]]

        parent_question_list = ParentQuestion.objects.bulk_create(parent_que_obj_list)

        return Response(data={'message':'Parent Questions Created Successfully'}, status=status.HTTP_201_CREATED)



class ParentQuestionUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ParentQuestionUpdateSerializer

    def get_object(self, parent_question_id):

        try:
            return ParentQuestion.objects.get(id=parent_question_id)
        except ParentQuestion.DoesNotExist:
            return None

    def get(self, request, parent_question_id):

        instance = self.get_object(parent_question_id)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No data found for the provided Parent Question-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, parent_question_id):

        instance = self.get_object(parent_question_id)
        if instance != None:
            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid():
                serializer.save(modified_by=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No data found for the provided Parent Question-ID..!'}, status=status.HTTP_404_NOT_FOUND)


class ParentAnswerView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 
    serializer_class = ParentAnswerSerializer

    def get(self, request):

        panswer_list = ParentAnswer.objects.filter(parent_answer_status=True)
        serializer = self.serializer_class(panswer_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serial = serializer.save(created_by=request.user)
            parent_answer_obj = ParentAnswer.objects.get(id=serial.id)
            ques_type = serial.parent_question
            exclusive = serializer.validated_data.get('exclusive')

            if ques_type.parent_question_type != "NU" and ques_type.parent_question_type != "MS":
                serial.numeric_min_range = None
                serial.numeric_max_range = None
                serial.exclusive = False
                serial.save()
            elif ques_type.parent_question_type == "MS":
                serial.numeric_min_range = None
                serial.numeric_max_range = None
                serial.exclusive = exclusive
                serial.save()
            else:
                serial.exclusive = False
                serial.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ParentAnswerUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ParentAnswerUpdateSerializer

    def get_object(self, parent_answer_id):

        try:
            return ParentAnswer.objects.get(id=parent_answer_id, parent_answer_status=True)
        except ParentAnswer.DoesNotExist:
            return None

    def get(self, request, parent_answer_id):

        instance = self.get_object(parent_answer_id)
        if instance != None:
            serializer = self.serializer_class(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No data found for the provided Parent Answer-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, parent_answer_id):

        instance = self.get_object(parent_answer_id)
        if instance != None:
            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid():
                answer = serializer.save(modified_by=request.user)
                ques_type = answer.parent_question
                exclusive = serializer.validated_data.get("exclusive")
                
                if ques_type.parent_question_type == "MS":
                    answer.exclusive = exclusive
                    answer.save()
                else:
                    answer.exclusive = False
                    answer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No data found for the provided Parent Answer-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, panswer_id):

        instance = self.get_object(panswer_id)
        instance.parent_answer_status = False
        return Response(status=status.HTTP_204_NO_CONTENT)


class TranslatedQuestionView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 
    serializer_class = TranslatedQuestionSerializer

    def get(self, request):

        tquestion_list = TranslatedQuestion.objects.all()
        serializer = TranslatedQuestionNameSerializer(tquestion_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        request.data['lang_code'] = ClientDBCountryLanguageMapping.objects.get(id=request.data['apidbcountrylangmapping']).lanugage_id.id
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            p_question = serializer.validated_data.get('parent_question')
            trans_que = TranslatedQuestion.objects.filter(
                apidbcountrylangmapping=request.data['apidbcountrylangmapping'], parent_question=p_question)
            if not len(trans_que) > 0:
                serializer.save(created_by=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'error':'Given Question already exist in the mentioned Country language..!'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TranslatedQuestionUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = TranslatedQuestionUpdateSerializer

    def get_object(self, translated_question_id):

        try:
            return TranslatedQuestion.objects.get(id=translated_question_id)
        except TranslatedQuestion.DoesNotExist:
            return None

    def get(self, request, translated_question_id):

        instance = self.get_object(translated_question_id)
        if instance != None:
            serializer = TranslatedQuestionNameSerializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No data found for the provided Translated Question-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, translated_question_id):

        instance = self.get_object(translated_question_id)
        if instance != None:
            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid():
                serializer.save(modified_by=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No data found for the provided Translated Question-ID..!'}, status=status.HTTP_404_NOT_FOUND)


class TranslatedAnswerView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = TranslatedAnswerSerializer

    def get(self, request):

        tanswer_list = TranslatedAnswer.objects.filter(translated_answer_status=True)
        serializer = TranslatedAnswerNameSerializer(tanswer_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(): 
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TranslatedAnswerUpdateView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = TranslatedAnswerUpdateSerializer

    def get_object(self, translated_answer_id):

        try:
            return TranslatedAnswer.objects.get(id=translated_answer_id, translated_answer_status=True)
        except TranslatedAnswer.DoesNotExist:
            return None

    def get(self, request, translated_answer_id):

        instance = self.get_object(translated_answer_id)
        if instance != None:
            serializer = TranslatedAnswerNameSerializer(instance)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'No data found for the provided Translated Answer-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, translated_answer_id):

        instance = self.get_object(translated_answer_id)
        if instance != None:
            serializer = self.serializer_class(instance, data=request.data)
            if serializer.is_valid():
                serializer.save(modified_by=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'No data found for the provided Translated Answer-ID..!'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, translated_answer_id):

        instance = self.get_object(translated_answer_id)
        instance.translated_answer_status = False
        return Response(status=status.HTTP_204_NO_CONTENT)

class MyPagenumberPagination(PageNumberPagination):
    page_size = '25'

class QuestionAnswerView(ModelViewSet):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 
    pagination_class = MyPagenumberPagination
    serializer_class = QuestionAnswerSerializer

    def get_queryset(self):
        question_ids = self.request.GET.get('questionids',None)
        question_type = self.request.GET.get('question_type', None)
        parent_question_category_id = self.request.GET.get('parent_question_category', None)
        question_list = ParentQuestion.objects.filter(
            is_active=True).exclude(Q(parent_question_type = 'CT') | Q(toluna_question_id = '1001018')).order_by('id')
        if question_ids:
            question_list = question_list.filter(id__in = question_ids.split(',')).order_by('id')
        if question_type:
            if question_type == 'Custom':
                question_list = question_list.filter(parent_question_prescreener_type=question_type)
            elif question_type == 'Standard':
                question_list = question_list.filter(parent_question_prescreener_type=question_type)
            elif question_type == 'toluna':
                question_list = question_list.exclude(toluna_question_id__exact='')
            elif question_type == 'zamplia':
                question_list = question_list.exclude(zamplia_question_id__exact='')
            elif question_type == 'disq':
                question_list = question_list.exclude(disqo_question_key__exact='')
        if parent_question_category_id:
            question_list = question_list.filter(parent_question_category_id = parent_question_category_id).order_by('id')

        return question_list

class QuestionAnswerListView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 
    serializer_class = QuestionAnswerListSerializer

    def get(self, request, parent_question_id):

        parent_question_answer_list = ParentAnswer.objects.filter(parent_question__id=parent_question_id, parent_answer_status=True)
        if parent_question_answer_list:
            serializer = self.serializer_class(parent_question_answer_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error':'No data found for the provided Question-ID..!'}, status=status.HTTP_404_NOT_FOUND)


class TranslatedQuestionAnswerListView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 
    serializer_class = TranslatedQuestionAnswerListSerializer

    def get(self, request, translated_parent_question_id):

        translate_question_answer_list = TranslatedAnswer.objects.filter(translated_parent_question__id=translated_parent_question_id, translated_answer_status=True)
        if translate_question_answer_list:
            serializer = self.serializer_class(translate_question_answer_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error':'No data found for the provided Translated Question-ID..!'}, status=status.HTTP_404_NOT_FOUND)


class TranslatedListByParentQuestionListView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 
    serializer_class = TranslatedListByParentQuestionSerializer

    def get(self, request, parent_question_id):

        translate_question_list = TranslatedQuestion.objects.filter(parent_question__id=parent_question_id)
        if translate_question_list:
            serializer = self.serializer_class(translate_question_list, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'error':'No data found for the provided Parent Question-ID..!'}, status=status.HTTP_404_NOT_FOUND)


class TranslatedQuestionAnswerView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = TranslatedQuestionAnswerSerializer

    def get(self, request):

        tqanda_list = TranslatedQuestion.objects.all()
        serializer = self.serializer_class(tqanda_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)