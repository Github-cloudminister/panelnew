from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from QuestionSupplierAPI.models import *


class AnswersMappingDetailSerializer(ModelSerializer):

    parent_ans_id = serializers.IntegerField(source='parent_ans_id.id')
    parent_ans_text = serializers.CharField(source='parent_ans_id.parent_answer_text', required=False)

    class Meta:
        model = AnswersMapping
        fields = [
            'id', 'parent_ans_id', 'supplier_api_ans_key','parent_ans_text','supplier_api_ans_parameter'
        ]


class RetrieveQuestionAnswersSerializer(ModelSerializer):

    answersmapping_set = AnswersMappingDetailSerializer(many=True)
    parent_que_id = serializers.IntegerField(source='parent_que_id.id')
    parent_que_text = serializers.CharField(source='parent_que_id.parent_question_text', required=False)
    supplier_org = serializers.SerializerMethodField()

    class Meta:
        model = QuestionsMapping
        fields = [
            'id', 'parent_que_id', 'supplier_org', 'supplier_api_que_key','parent_que_text','supplier_api_que_parameter','answersmapping_set'
        ]

    def get_supplier_org(self, intance):
        supplier_id = self.context.get('supplier_id')
        return supplier_id
        

    def create(self, validated_data):
        answers = validated_data.pop('answersmapping_set')
        try:
            que_map_obj = QuestionsMapping.objects.create(parent_que_id_id=validated_data['parent_que_id']['id'],supplier_org_id=self.initial_data['supplier_org'],supplier_api_que_key=validated_data['supplier_api_que_key'],supplier_api_que_parameter=validated_data.get('supplier_api_que_parameter') if validated_data.get('supplier_api_que_parameter') else None)
            for answer in answers:
                try:
                    AnswersMapping.objects.create(ques_mapping_id=que_map_obj,supplier_org_id=self.initial_data['supplier_org'],parent_ans_id_id=answer['parent_ans_id']['id'],supplier_api_ans_key=answer['supplier_api_ans_key'], supplier_api_ans_parameter=answer['supplier_api_ans_parameter'])
                except:
                    #Just in case supplier api ans key not pased. Need to fix this later. dated: DEc 14, 2021
                    pass
        except IntegrityError:
            return False
        return que_map_obj


class SupplierOrgMappedQuestionSerializer(ModelSerializer):

    questionsmapping_set = RetrieveQuestionAnswersSerializer(many=True)

    class Meta:
        model = SupplierOrganisation
        fields = ['supplier_name','questionsmapping_set']
