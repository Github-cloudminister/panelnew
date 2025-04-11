from django.db.models import Sum, Min
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from knox.auth import TokenAuthentication
from feasibility.serializers import *
from feasibility.models import *
from Questions.models import *
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
# Create your views here.


class feasibilityWeightageView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = FeasibilityQuestionAnswerMappingSerializer
    lookup_field = 'id'

    def get_queryset(self):
        question = self.request.GET.get('question')
        if question:
            return FeasibilityQuestionAnswerMapping.objects.filter(question = question)
        else:
            return FeasibilityQuestionAnswerMapping.objects.all()

    def create(self, request, *args, **kwargs):
        data=request.data
        for d in data:
            try:
                feasibility_question_obj = FeasibilityQuestionAnswerMapping.objects.get(id=d['id'])
                feasibility_question_obj.feasibilityweightage = d['feasibilityweightage']
                feasibility_question_obj.feasibilitycpiweightage = d['feasibilitycpiweightage']
                feasibility_question_obj.save() 

            except:
                serializer = self.get_serializer(data=d)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
        
        return Response(status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        data = request.data
        for d in data:
            try:
                d.pop('question')
            except:
                pass
            
            try:
                d.pop('answer')
            except:
                pass
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=d)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
        return Response(status=status.HTTP_202_ACCEPTED)

class MyPagenumberPagination(PageNumberPagination):
    page_size = '25'

class feasibilityCPIRateView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = feasibilityCPIRateSerializer
    queryset = BaseCPI.objects.all()
    pagination_class = MyPagenumberPagination


    def create(self, request, *args, **kwargs):
        csv_file = request.FILES['csvfile']
        if not csv_file.name.endswith('.csv'):
            return Response({'error': 'Please upload a csv file format..!'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            df = pd.read_csv(csv_file, header=0,)
    
            if set(["incidenceMin", "incidenceMax", "loiMin", "loiMax", "cpi", "studyType"]).issubset(df.columns):
                if not df.empty:
                    for index, row in df.iterrows():
                        basecpi_obj, created = BaseCPI.objects.get_or_create(
                            study_type = round(row['studyType']),
                            min_loi = row['loiMin'],
                            max_loi = row['loiMax'],
                            min_incidence = row['incidenceMin'],
                            max_incidence = row['incidenceMax'],
                        )
                        basecpi_obj.cpi = cpi = row['cpi']
                        basecpi_obj.save()

                    return Response({'msg': 'Feasibility Rate created or updated successfully..!'}, status=status.HTTP_200_OK)
                return Response({'error': "No data found in provided file...!"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': "Invalid format of csv file so download the sample file..!"}, status=status.HTTP_400_BAD_REQUEST)


class feasibilityBaseWeightageView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = feasibilityWeightageSerializer
    queryset = BaseFeasibilityWeightage.objects.all()
    pagination_class = MyPagenumberPagination


    def create(self, request, *args, **kwargs):
        csv_file = request.FILES['csvfile']
        if not csv_file.name.endswith('.csv'):
            return Response({'error': 'Please upload a csv file format..!'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            df = pd.read_csv(csv_file, header=0,)
    
            if set(["incidenceMin", "incidenceMax", "loiMin", "loiMax", "feasibilityWeightage"]).issubset(df.columns):
                if not df.empty:
                    for index, row in df.iterrows():
                        basefeasibility_obj, created = BaseFeasibilityWeightage.objects.get_or_create(
                            min_loi = row['loiMin'],
                            max_loi = row['loiMax'],
                            min_incidence = row['incidenceMin'],
                            max_incidence = row['incidenceMax'],
                        )
                        basefeasibility_obj.feasibilityWeightage = feasibilityWeightage = row['feasibilityWeightage']
                        basefeasibility_obj.save()
                    return Response({'msg': 'Feasibility Rate created or updated successfully..!'}, status=status.HTTP_200_OK)
                return Response({'error': "No data found in provided file...!"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'error': "Invalid format of csv file so download the sample file..!"}, status=status.HTTP_400_BAD_REQUEST)


class feasibilityQustionAnswerValueView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = FeasibilityQuestionAnswerMappingSerializer

    def create(self, request, *args, **kwargs):
        data = request.data
        study_type = data['study_type']
        
        if int(study_type) == 1: 
            #Genpop
            feasibility = 2800
        else:
            #B2B
            feasibility = 15000
        
        try:
            Base_Feasibility_Weightage = BaseFeasibilityWeightage.objects.get(min_loi__lte=data['loi'], max_loi__gte=data['loi'], min_incidence__lte=data['incidence'], max_incidence__gte=data['incidence']).feasibilityWeightage
        except:
            Base_Feasibility_Weightage = 100
        
        feasibility = (int(feasibility)*int(Base_Feasibility_Weightage))/100
        try:
            base_cpi = BaseCPI.objects.get(min_loi__lte=data['loi'], max_loi__gte=data['loi'], min_incidence__lte=data['incidence'], max_incidence__gte=data['incidence'], study_type=data['study_type']).cpi
        except ObjectDoesNotExist:
            base_cpi = 0
        for d in data['question_data']:
            question_id = d['question']
            answer_id_list = d['answers'].split(',')

            feasibility_weightage_total = FeasibilityQuestionAnswerMapping.objects.filter(question__id = question_id, answer__id__in = answer_id_list).aggregate(Min('feasibilitycpiweightage'), feasibilityweightage_sum=Sum('feasibilityweightage'))

            if feasibility_weightage_total['feasibilitycpiweightage__min'] is not None:
                base_cpi = base_cpi+float(feasibility_weightage_total['feasibilitycpiweightage__min'])

            if feasibility_weightage_total['feasibilityweightage_sum'] and feasibility_weightage_total['feasibilityweightage_sum'] > 0:
                feasibility = (feasibility * feasibility_weightage_total['feasibilityweightage_sum'])/100
            
        return Response({'feasibility':round(feasibility,0), 'cpi':base_cpi},status=status.HTTP_200_OK)


class feasibilityQuestionAnswerView(ModelViewSet):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,) 
    serializer_class = feasibilityQuestionAnswerSerializer
    queryset = ParentQuestion.objects.filter(id__in = FeasibilityQuestionAnswerMapping.objects.values_list('question'))