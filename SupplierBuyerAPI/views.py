import datetime, hashlib, uuid
from ClientSupplierAPIIntegration.TolunaClientAPI.models import ClientDBCountryLanguageMapping
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from ClientSupplierAPIIntegration.TolunaClientAPI.views import CustomerAuthPermission
from Prescreener.models import ProjectGroupPrescreener
from Project.models import ProjectGroup, ProjectGroupSubSupplier, ProjectGroupSupplier
from Questions.models import TranslatedQuestion
from Supplier.models import SubSupplierOrganisation, SupplierOrganisation
from SupplierBuyerAPI.models import SubSupplierBuyerAPIModel, SupplierBuyerAPIModel, SupplierBuyerProjectGroup
from SupplierBuyerAPI.permissions import SupplierOrgSecretKeyPermission
from SupplierBuyerAPI.serializers import PrescreenerQuestionAnswerSerializers, TranslatedQuestionsSerializer
from django.db.models import Q, Count, F,Value
import concurrent.futures
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
from dateutil.relativedelta import relativedelta
from django.db.models.functions import Replace
from django.conf import settings

max_workers = 10 if settings.SERVER_TYPE == 'localhost' else 50

def get_Supplier_code(header):

	try:
		if 'Authentication' in header:
			suppliercode = SupplierOrganisation.objects.get(supplier_buyer_apid__secret_key = header['Authentication']).supplier_code
			return suppliercode
		elif 'Authorization' in header:
			suppliercode = SubSupplierOrganisation.objects.get(sub_supplier_buyer_apid__secret_key = header['Authorization']).sub_supplier_code
			return suppliercode
	except:
		return False


class SupplierBuyerEnableDisable(APIView):

	authentication_classes = (TokenAuthentication,)
	permission_classes = (IsAuthenticated,)

	def get(self,request,id):
		try:
			supplierbuyerobj = SupplierBuyerAPIModel.objects.get(supplier_org_id__id = id)
			return Response({"secret_key" : supplierbuyerobj.secret_key}, status=status.HTTP_200_OK)
		except:
			return Response({"error" : "Invalid Supplier..!"}, status=status.HTTP_400_BAD_REQUEST)
	
	def post(self,request,id,supplier_type):

		try:
			uuid4_str = uuid.uuid4().hex
			secret_key = hashlib.md5(uuid4_str.encode()).hexdigest()
			if supplier_type == 1:
				supplierbuyerobj =  SupplierBuyerAPIModel.objects.create(
						supplier_org_id_id = id, 
						buyer_api_enable = True,
						secret_key = secret_key,
						request_api_url = "abcd",
				)
			elif supplier_type == 2:
				supplierbuyerobj =  SubSupplierBuyerAPIModel.objects.create(
						sub_supplier_org_id_id = id, 
						buyer_api_enable = True,
						secret_key = secret_key,
						request_api_url = "abcd",
				)
			else:
				return Response({"error" : "Invalid Supplier"}, status=status.HTTP_400_BAD_REQUEST)
			
			return Response({"secret_key" : supplierbuyerobj.secret_key}, status=status.HTTP_200_OK)
		except:
			return Response({"error" : "Supplier Already Exists"}, status=status.HTTP_400_BAD_REQUEST)
		
	def put(self,request,id,supplier_type):

		try:
			uuid4_str = uuid.uuid4().hex
			secret_key = hashlib.md5(uuid4_str.encode()).hexdigest()
			if supplier_type == 1:
				supplierbuyerobj = SupplierBuyerAPIModel.objects.get(supplier_org_id__id = id)
			elif supplier_type == 2:
				supplierbuyerobj = SubSupplierBuyerAPIModel.objects.get(supplier_org_id__id = id)
			else:
				return Response({"error" : "Invalid Supplier"}, status=status.HTTP_400_BAD_REQUEST)
			supplierbuyerobj.secret_key = secret_key
			supplierbuyerobj.save()
			return Response({"secret_key" : supplierbuyerobj.secret_key}, status=status.HTTP_200_OK)
		except:
			return Response({"error" : "Invalid Supplier..!"}, status=status.HTTP_400_BAD_REQUEST)
	
	def patch(self,request,id,supplier_type):

		try:
			if supplier_type == 1:
				supplierbuyerobj = SupplierBuyerAPIModel.objects.get(supplier_org_id__id = id)
			elif supplier_type == 2:
				supplierbuyerobj = SupplierBuyerAPIModel.objects.get(supplier_org_id__id = id)
			else:
				return Response({"error" : 'Invalid Supplier..!'}, status=status.HTTP_400_BAD_REQUEST)
			supplierbuyerobj.buyer_api_enable = False
			supplierbuyerobj.save()
			return Response({"secret_key" : supplierbuyerobj.buyer_api_enable}, status=status.HTTP_200_OK)
		except:
			return Response({"error" : "Invalid Supplier..!"}, status=status.HTTP_400_BAD_REQUEST)


class GetSupplierBuyerCountryLangAPI(APIView):
	permission_classes = (SupplierOrgSecretKeyPermission,)

	def get(self,request,*args,**kwargs):
		try:
			supplier_project_list = ClientDBCountryLanguageMapping.objects.values(
				CountryLanguageId= F('id'),CountryLanguageCode = F('client_language_name'),
				CountryLanguageName = F('client_language_description')).order_by('id')

			return Response(supplier_project_list, status=status.HTTP_200_OK)
		except:
			return Response({"error" : "Invalid Supplier..!"}, status=status.HTTP_400_BAD_REQUEST)
	

class GetQualificationsAPI(APIView):
	permission_classes = (SupplierOrgSecretKeyPermission,)

	def get(self,request,*args,**kwargs):
		try:
			CultureID = request.data.get('CultureID')
			if CultureID:
				question_answer = TranslatedQuestion.objects.filter(
					is_active=True,apidbcountrylangmapping__id = CultureID).exclude(
						parent_question_type = 'CTZIP').order_by('Internal_question_id')

			serializer = TranslatedQuestionsSerializer(question_answer,many=True)
			return Response(serializer.data, status=status.HTTP_200_OK)
		except:
			return Response({"error":"Invalid Supplier..!"}, status=status.HTTP_400_BAD_REQUEST)


class GetSurveyQuotasAPI(APIView):
	permission_classes = (SupplierOrgSecretKeyPermission,)

	def get(self,request,*args,**kwargs):
		try:
			if get_Supplier_code(request.headers):
				prescreener = ProjectGroupPrescreener.objects.filter(
					is_enable = True,translated_question_id__is_active = True,
					project_group_id__project_group_number = self.kwargs.get('project_group_number',''))
				serializer = PrescreenerQuestionAnswerSerializers(prescreener,many = True)
				return Response(serializer.data, status=status.HTTP_200_OK)
			else:
				return Response({"error" : "Invalid Supplier..!"}, status=status.HTTP_400_BAD_REQUEST)
		except:
			return Response({"error" : "Invalid Supplier..!"}, status=status.HTTP_400_BAD_REQUEST)


class GetSurveyStatistics(APIView):
	permission_classes = (SupplierOrgSecretKeyPermission,)

	def get(self,request,*args,**kwargs):
		try:
			suppliercode = get_Supplier_code(request.headers)
			if 'Authentication' in request.headers:
				project_grp_supp = ProjectGroupSupplier.objects.filter(
					supplier_org__supplier_code = suppliercode,
					project_group_id__project_group_number = self.kwargs.get('project_group_number',''))
			elif 'Authorization' in request.headers:
				project_grp_supp = ProjectGroupSubSupplier.objects.filter(
					sub_supplier_org__sub_supplier_code = suppliercode,
					project_group_id__project_group_number = self.kwargs.get('project_group_number',''))

			project_grp_supp = project_grp_supp.values(
					'cpi',
					total_visits = F('clicks'),
					visits_remaining = F('clicks') - Count('respondentdetailsrelationalfield',filter=Q(respondentdetailsrelationalfield__respondent__url_type='Live')),

					total_completes = F('completes'),
					
					completes_remaining = F('completes') - Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status = "4", respondentdetailsrelationalfield__respondent__url_type='Live')),
					
					incompletes = Count('respondentdetailsrelationalfield', filter = Q(respondentdetailsrelationalfield__respondent__resp_status__in=['3'], respondentdetailsrelationalfield__respondent__url_type='Live')),
					
					quota_full = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=['6'], respondentdetailsrelationalfield__respondent__url_type='Live')),

					security_terminate = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=['7'], respondentdetailsrelationalfield__respondent__url_type='Live')),

					terminates = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=['5'], respondentdetailsrelationalfield__respondent__url_type='Live')),
					
				)
			return Response(project_grp_supp, status=status.HTTP_200_OK)
		except:
			return Response({"error" : "Invalid Supplier..!"}, status=status.HTTP_400_BAD_REQUEST)


class SupplierBuyerSurveyGetAPI(APIView):
	permission_classes = (SupplierOrgSecretKeyPermission,)

	def get(self,request,*args,**kwargs):
		try:
			suppliercode = get_Supplier_code(request.headers)
			CultureID = ClientDBCountryLanguageMapping.objects.filter(id = request.data.get('CultureID',0)).values('country_id','lanugage_id').first()
			if 'Authentication' in request.headers:
				projectgrouplist = ProjectGroupSupplier.objects.filter(
					supplier_org__supplier_code = suppliercode,
					supplier_status = 'Live',project_group__project_group_status = 'Live',
					project_group__project__project_status = 'Live',
					project_group__project_group_country_id = CultureID['country_id'],
					project_group__project_group_language_id = CultureID['lanugage_id']
					).annotate(
						SurveyURL = Replace('supplier_survey_url',Value('PID=XXXXX'), Value('router=4&PID=XXXXX'))
					).values(
						SurveyID = F('project_group__project_group_number'),
						LOI = F('project_group__project_group_loi'),
						IR = F('project_group__project_group_incidence'),
						CPI = F('cpi'),
						Completes = F('completes'),
						Clicks = F('clicks'),
						SurveyRedirect=F('SurveyURL'),
						QuestionsAndAnswers = F('project_group__supplierbuyerprojectgroup__qualification')
					)
			elif 'Authorization' in request.headers:
				projectgrouplist = ProjectGroupSubSupplier.objects.filter(
					sub_supplier_org__sub_supplier_code = suppliercode,
					sub_supplier_status = 'Live',project_group__project_group_status = 'Live',
					project_group__project__project_status = 'Live',
					project_group__project_group_country_id = CultureID['country_id'],
					project_group__project_group_language_id = CultureID['lanugage_id']
					).annotate(
						SurveyURL = Replace('sub_supplier_survey_url',Value('PID=XXXXX'), Value('router=5&PID=XXXXX'))
					).values(
						SurveyID = F('project_group__project_group_number'),
						LOI = F('project_group__project_group_loi'),
						IR = F('project_group__project_group_incidence'),
						CPI = F('cpi'),
						Completes = F('completes'),
						Clicks = F('clicks'),
						SurveyRedirect=F('SurveyURL'),
						QuestionsAndAnswers = F('project_group__supplierbuyerprojectgroup__qualification'),
					)
			return Response(projectgrouplist, status=status.HTTP_200_OK)
		except:
			return Response({"error" : "Invalid Supplier..!"}, status=status.HTTP_400_BAD_REQUEST)


class GetFetchSurveyURLAPI(APIView):
	permission_classes = (SupplierOrgSecretKeyPermission,)

	def get(self,request,project_group_number):
		try:
			suppliercode = get_Supplier_code(request.headers)
			QA = request.data
			sc_op = True
			responsedata = ''
			for key, values in QA.items():
				qobj = ProjectGroupPrescreener.objects.get(
					project_group_id__project_group_number = project_group_number,translated_question_id__Internal_question_id = str(key))
				if qobj.translated_question_id.parent_question_type in ['DT','NU']:

					dob = datetime.datetime.strptime(values,"%m-%d-%Y")
					current_year = datetime.datetime.now()
					entered_value = relativedelta(current_year, dob).years
		
					allowedRangeMin = qobj.allowedRangeMin.split(",")
					allowedRangeMax = qobj.allowedRangeMax.split(",")

					for min, max in zip(allowedRangeMin, allowedRangeMax):
						if int(entered_value) >= int(min) and int(entered_value) <= int(max):
							sc_op = False
							responsedata = f'{responsedata}&{qobj.translated_question_id.Internal_question_id}={values}'
					if sc_op == True:
						break
				elif qobj.translated_question_id.parent_question_type == 'ZIP':
					if qobj.allowed_zipcode_list != [] and values in qobj.allowed_zipcode_list:
						responsedata = f'{responsedata}&{qobj.translated_question_id.Internal_question_id}={values}'
						sc_op = False
					elif qobj.allowed_zipcode_list == []:
						responsedata = f'{responsedata}&{qobj.translated_question_id.Internal_question_id}={values}'
						sc_op = False
					else:
						sc_op = True
						break
				elif qobj.translated_question_id.parent_question_type in ['MS']:
					values = values if type(values) == list else [values]
					if bool(set(values + list(qobj.allowedoptions.values_list('id',flat=True)))):
						answer = ','.join(list(qobj.allowedoptions.filter(internal_answer_id__in = values).values_list('internal_answer_id',flat=True)))
						responsedata = f'{responsedata}&{qobj.translated_question_id.Internal_question_id}={answer}'
						sc_op = False
					else:
						sc_op = True
						break
				elif qobj.translated_question_id.parent_question_type in ['SS','CTZIP']:
					if bool(set([values] + list(qobj.allowedoptions.values_list('id',flat=True)))):
						responsedata = f'{responsedata}&{qobj.translated_question_id.Internal_question_id}={qobj.allowedoptions.get(internal_answer_id = values).internal_answer_id}'
						sc_op = False
					else:
						sc_op = True
						break
				elif qobj.translated_question_id.parent_question_type == 'OE' and values:
					pass
			
			if suppliercode and not sc_op and 'Authentication' in request.headers:
				projectgrouplist = ProjectGroupSupplier.objects.get(supplier_org__supplier_code = suppliercode,
					project_group__project_group_number = project_group_number)
				surveyurl = f'{projectgrouplist.supplier_survey_url}&router=4{responsedata}'
				return Response({"SurveyURL" : surveyurl}, status=status.HTTP_200_OK)
			elif suppliercode and not sc_op and 'Authorization' in request.headers:
				projectgrouplist = ProjectGroupSubSupplier.objects.get(sub_supplier_org__sub_supplier_code = suppliercode,
					project_group__project_group_number = project_group_number)
				surveyurl = f'{projectgrouplist.sub_supplier_survey_url}&router=5{responsedata}'
				return Response({"SurveyURL" : surveyurl}, status=status.HTTP_200_OK)
			else:
				return Response({"error" : "User is Not Qualified For This Survey"}, status=status.HTTP_400_BAD_REQUEST)
		except:
			return Response({"error" : "Qulifications Not Properly Submitted"}, status=status.HTTP_400_BAD_REQUEST)


class SupplierBuyerProjectGroupCreateView(APIView):

	def post(self,request,*args,**kwargs):
		try:
			project_group_number_list = list(ProjectGroup.objects.filter(project_group_status = 'Live').values_list('project_group_number',flat=True))
			def surveybuyer_parellel_surveys_storing_func(survey):
				prescreenerobj = ProjectGroupPrescreener.objects.filter(
					project_group_id__project_group_number = survey,
					is_enable = True,
					translated_question_id__is_active = True
				).exclude(translated_question_id__parent_question_type = 'CTZIP')
				if len(prescreenerobj) != 0:
					serilizer = PrescreenerQuestionAnswerSerializers(prescreenerobj,many=True)
					try:
						SupplierBuyerProjectGroup.objects.update_or_create(
							project_group = prescreenerobj.first().project_group_id,
							defaults = {'qualification' : serilizer.data}
						)
					except:
						pass
			with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
				yield_results = list(executor.map(surveybuyer_parellel_surveys_storing_func, project_group_number_list))
				
			return Response({"message":"Success"}, status=status.HTTP_200_OK)
		except:
			return Response({"error" : "Invalid Supplier..!"}, status=status.HTTP_200_OK)