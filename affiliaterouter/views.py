import hashlib
import random,json
from django.db import IntegrityError
import geoip2
#================= restframework library ====================
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
#================= project library or models ====================
from Logapp.views import routerexception_log
from Project.models import *
from affiliaterouter.serializers import *
from affiliaterouter.permissions import *
from affiliaterouter.custom_functions import *
#================= third-party libraries ====================
from knox.auth import TokenAuthentication
import base64
from hashlib import blake2b
import uuid,requests


class QuestionsDataTableCrud(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self,request):
        parent_que_ids = request.data.get('parent_que_ids').split(',') if request.data.get('parent_que_ids') else None
        if parent_que_ids:
            list(AffiliateRouterQuestions.objects.update_or_create(translated_question=TranslatedQuestion.objects.get(Internal_question_id=ques_id)) for ques_id in parent_que_ids)
            questions_data_qs = AffiliateRouterQuestions.objects.values()
            return Response(data=questions_data_qs, status=status.HTTP_201_CREATED)
        else:
            return Response(data={'message':'Please pass parent_que_ids in the body'}, status=status.HTTP_406_NOT_ACCEPTABLE)

    
    def get(self,request):
        affiliate_ques_ids = request.GET.get('affiliate_ques_ids').split(',') if request.GET.get('affiliate_ques_ids') else None
        questions_data_qs = AffiliateRouterQuestions.objects.values()
        if affiliate_ques_ids:
            questions_data_qs = questions_data_qs.filter(id__in=affiliate_ques_ids)

        return Response(data=questions_data_qs)


    def delete(self,request):
        affiliate_ques_id = request.GET.get('affiliate_ques_id')
        if affiliate_ques_id:
            affiliate_ques_qs = AffiliateRouterQuestions.objects.filter(id=affiliate_ques_id)
            if affiliate_ques_qs:
                affiliate_ques_qs.delete()
            else:
                return Response(data={'message':'AffiliateRouter Question Not Found'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            AffiliateRouterQuestions.objects.all().delete()

        return Response(data={'message':'AffiliateRouter Question/s Deleted Successfully'}, status=status.HTTP_204_NO_CONTENT)


class identifyCountry(APIView):
    def get_client_ip(self,request):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get(self, request,*args, **kwargs):
        if settings.SERVER_TYPE == 'localhost':
            ip_address = '49.36.87.161'
        else:
            ip_address = self.get_client_ip(request)
        client = geoip2.webservice.Client('275599', 'fgjd0IOKJkfEvpHr')
        API_response = client.country(ip_address)
        country = API_response.country.iso_code
        return Response(data={'country':country}, status=status.HTTP_200_OK)


class AffiliateRouterQuestionsAnswers(APIView):

    # Custom function
    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    # Custom function
    @staticmethod
    def generateVisitorId():
        unique_string = uuid.uuid4().hex
        h2=blake2b(digest_size=23)
        h2.update(unique_string.encode())
        genareted_visitor_id = h2.hexdigest()
        return genareted_visitor_id

    def get(self, request):
        country_code = request.GET.get('country')
        source = request.GET.get('sc', settings.AFFILIATE_SUPPLIER_CODE)
        subsource = request.GET.get('ssc','')
        ip_address = '49.36.87.161' if settings.SERVER_TYPE == 'localhost' else self.get_client_ip(self.request)
        generated_visitor_rsid = self.generateVisitorId()
        rsid = request.GET.get('rsid', base64.b64encode(generated_visitor_rsid.encode()[:22])[:23].decode())
        generated_visitor_ruid = self.generateVisitorId()
        ruid = request.GET.get('ruid', base64.b64encode(generated_visitor_ruid.encode()[:22])[:23].decode())

        if not country_code:
            try:
                if settings.SERVER_TYPE == 'localhost':
                    ip_address = '49.36.87.161'
                else:
                    ip_address = self.get_client_ip(request)
                client = geoip2.webservice.Client('275599', 'fgjd0IOKJkfEvpHr')
                API_response = client.country(ip_address)
                country_code = API_response.country.iso_code
            except:
                return Response(data={'message':'Please specify the country code'})
        
        country_obj = Country.objects.get(country_code=country_code)

        visitor_obj,created = Visitors.objects.get_or_create(
            ruid=ruid,
            source = source,
            subsource = subsource,
            defaults = {
            "ip_address" : ip_address,
            "genareted_visitor_id" : generated_visitor_ruid,
            "user_agent" : request.META.get('HTTP_USER_AGENT'),
            "rsid" : rsid,
            "country" : country_obj,
            }
        )

        TotalVisitorsRouts.objects.create(
            visitor = visitor_obj,
            entry_url = request.build_absolute_uri()
            )   

        string = ''
        for key, value in request.GET.items():
            if 'country' == key or 'sc' == key or 'ruid' == key:
                continue
            else:
                string+=f'{key}={value}&'
		
        VisitorURLParameters.objects.update_or_create(
            visitor = visitor_obj,
            defaults = {
                "url_extra_params" : string[:-1],
                "rsid" : rsid,
                "entry_url" : request.build_absolute_uri()
            }
        )

        question_data = AffiliateRouterQuestionsData.objects.filter(visitor=visitor_obj,visitor__source = source,visitor__subsource = subsource).values_list('parent_question__Internal_question_id',flat=True)
        questions_list = AffiliateRouterQuestions.objects.filter(translated_question__is_active = True,translated_question__apidbcountrylangmapping__country_id__country_code = country_code
        ).exclude(translated_question__Internal_question_id__in = list(question_data)).order_by('sequence')
        
        serializer = AffiliateRouterQuestionsAnswersSerializer(instance=questions_list, many=True)
        response_list = list(serializer.data)
        number_of_questions = len(response_list)
        response_list.append({'generated_visitor_id':visitor_obj.genareted_visitor_id, 'number_of_questions':number_of_questions})

        return Response(data=response_list)


    def post(self, request):
        request_data = request.data

        # This is Mandatorily to be taken from the User
        language = request_data.get('language')

        # Do not allow the User going forward if the number of answers do not match the displayed number of Questions on screen
        if request_data['number_of_questions'] != len(request_data['responses']) or not language:
            return Response(data={'message':'Please pass all the required inputs'}, status=status.HTTP_400_BAD_REQUEST)
        
        visitor_obj = Visitors.objects.get(genareted_visitor_id=request_data['generated_visitor_id'])
        for question in request.data['responses']:

            try:
                language_obj = Language.objects.get(language_code=language)
                country_obj = Country.objects.get(country_code=visitor_obj.country.country_code)

                question_obj = AffiliateRouterQuestionsData.objects.create(
                    visitor=visitor_obj,
                    parent_question_id=question['translated_question'],
                    country=country_obj,
                    received_answers_id=self.generateVisitorId(),
                    language=language_obj
                )

                for answer in question['parent_answers']:

                    #For Zipcode
                    if 'ZIP' in question['translated_question_type']:
                        question_obj.open_end_answer = answer['numeric_open_answer']
                        question_obj.save()
                    #For Age Question
                    elif 'NU' in question['translated_question_type']:
                        question_obj.open_end_answer = answer['extra_open_answer']
                        question_obj.save()
                    else:
                        answer_obj = TranslatedAnswer.objects.get(id=answer['parent_answer_id'])
                        question_obj.parent_answers.add(answer_obj)
            
            except IntegrityError:
                return Response(data={'message':'Same Question cannot be stored twice for the Same User'})

        return Response(data={'visitor_id':request_data['generated_visitor_id'], 'method':'GET', 'status':99})


# THIS API IS ONLY FOR DECIDING WHERE TO SEND THE VISITOR BASED ON THE EMPLOYMENT TYPE, REST ALL ANSWERS GIVEN BY HIM DO NOT MATTER
class SurveySideDecisionAPI(APIView):

    def get(self, request, visitorid):

        try:
            """
            '99':'CNT Router'
            '1':'Toluna'
            '2':'logic group'
            '3':'internal surveys'
            '4':'SAGO'
            """
            visitor_id = Visitors.objects.get(genareted_visitor_id=visitorid)
            pipe_data = request.GET.get('p','')
            mincpi = request.GET.get('cos',0)
            userid = request.GET.get('uid',None)
            suppliercode = visitor_id.source
            subsuppliercode = visitor_id.subsource
            useranswered_objs = AffiliateRouterQuestionsData.objects.filter(visitor = visitor_id)
            country = useranswered_objs.first().country.country_code
            language = useranswered_objs.first().language.language_code
            finalised_survey_list = []
            question_answer_dict = {item.parent_question.Internal_question_id:list(item.parent_answers.values_list('internal_answer_id',flat=True)) if item.parent_question.Internal_question_id not in ('112521','181411','900002','112498','181412','900073') else item.open_end_answer for item in useranswered_objs}
                    
            if len(finalised_survey_list) == 0 and pipe_data in ['',None]:
                # For priority surveys
                finalised_survey_list = survey_decision(get_project_group_priority_surveys(suppliercode,subsuppliercode, country, language,mincpi),question_answer_dict) 
                
                if not finalised_survey_list.exists():
                    finalised_survey_list = []

            if len(finalised_survey_list) == 0:
                
                #*****************Toluna Surveys*****************
                if pipe_data == '1':
                    finalised_survey_list = survey_decision(get_project_group_supplier_toluna_data(suppliercode,subsuppliercode, country, language,mincpi),question_answer_dict)
                            
                # #*****************logic group Surveys*****************
                elif pipe_data == '2':
                    finalised_survey_list = survey_decision(get_project_group_supplier_logic_group_data(suppliercode,subsuppliercode, country, language,mincpi),question_answer_dict)
                
                # # #*****************CNT Surveys*****************                
                # if pipe_data == '99' or pipe_data in ['',None] and len(project_group_supplier_qs) == 0:
                #     finalised_survey_list = survey_decision(get_project_group_supplier_cnt_router_data(suppliercode,subsuppliercode, country, language,mincpi),question_answer_dict)
                
                # #*****************Internal Surveys*****************
                elif pipe_data == '3':
                    finalised_survey_list = survey_decision(get_project_group_supplier_internal_survey_data(suppliercode,subsuppliercode, country, language,mincpi),question_answer_dict)

                elif pipe_data == '4':
                    finalised_survey_list = survey_decision(get_project_group_supplier_sago_data(suppliercode,subsuppliercode, country, language,mincpi),question_answer_dict)  

                if len(finalised_survey_list) == 0:
                    finalised_survey_list = survey_decision(get_project_group_supplier_api_client_data(suppliercode,subsuppliercode,country,language,mincpi),question_answer_dict)

            try:
                attempted_survey_list = list(VisitorSurveyRedirect.objects.filter(visitor_id__ruid = visitor_id.ruid).values_list('survey_number',flat=True))
                finalised_survey = random.choice(finalised_survey_list.order_by('-project_group__project_group_incidence').exclude(project_group__project_group_number__in = attempted_survey_list)[:9])
            except Exception as e:
                routerexception_log(visitor_id,e)
                return Response({"status":2,"URL":f"{settings.OPINIONSDEALSNEW_FRONTEND_URL}"}, status=status.HTTP_200_OK)
            

            if finalised_survey:
                
                if subsuppliercode not in ['',None]:
                    redirect_url = finalised_survey.project_group_supplier_fk.all().filter(sub_supplier_org__sub_supplier_code = subsuppliercode).first().sub_supplier_survey_url.replace('%%PID%%',visitor_id.ruid).replace('XXXXX',visitor_id.ruid)
                else:
                    redirect_url = finalised_survey.supplier_survey_url.replace('%%PID%%',visitor_id.ruid).replace('XXXXX',visitor_id.ruid)
               
                visitor_url_params = VisitorURLParameters.objects.get(visitor=visitor_id)
                visitor_url_params.exit_url = redirect_url
                visitor_url_params.save()
            else:
                return Response({"status":2,"URL":f"{settings.OPINIONSDEALSNEW_FRONTEND_URL}"}, status=status.HTTP_200_OK)
            
            survey_no = finalised_survey.project_group.project_group_number

            visitor_id.respondent_status = '2' if survey_no else '1'
            visitor_id.save()
            
            visitor_survey_redirect_obj = VisitorSurveyRedirect.objects.create(survey_number=survey_no,visitor_id=visitor_id)

            if userid:
                redirect_url = f'{redirect_url}&uid={userid}'

            QA = ''
            for key,values in question_answer_dict.items():
                QA = f'{QA}&{key}={",".join(values)}' if key not in ('112521','181411','900002','112498','181412','900073') else f'{QA}&{key}={values}'

            redirect_url = redirect_url + f"&router=2&p={visitor_survey_redirect_obj.id}{QA}"
            visitor_survey_redirect_obj.supplier_survey_url = redirect_url
            visitor_survey_redirect_obj.save()

            # try:
                # for opinionsdeal submit user redirect data
            #     if suppliercode == '464887392ff873ad':
            #         requests.post(f'{settings.OPINIONSDEALSNEW_BASE_URL}panel/survey-attempt-data-store?survey_number={survey_no}&uuid={userid}&survey_url={redirect_url}',headers={'Authorization':'Token 45Mvp7LKKN2837PfXCnSodldjDD67435odif5auts74sXALi05iqBHxuZKSJtd8v0'})
            # except:
            #     pass

            return Response({"status":1,'data':survey_no,'redirect_url':redirect_url})
        except Exception as e:
            routerexception_log(visitor_id,e)
            return Response({"status":2,"URL":f"{settings.OPINIONSDEALSNEW_FRONTEND_URL}"}, status=status.HTTP_200_OK)


class AffialiateRouterProjectGroupData(APIView):

    def get(self, request):

        project_survey_data = VisitorSurveyRedirect.objects.only('id','survey_number','supplier_survey_url').values().order_by('-id')[:5]

        return Response({"redirect_survey_data":project_survey_data}, status=status.HTTP_200_OK)


class RountingPriorityView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, )
    serializer_class = RountingPrioritySerializer

    def get(self, request, *args, **kwargs):
        routing_priority_obj = RountingPriority.objects.filter(project_group__project_group_status = "Live")
        serializer = self.serializer_class(routing_priority_obj, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):

        post_data = [ sub['project_group_number'] for sub in request.data ]

        if len(post_data) > 10:
            return Response({'error': 'You cannot set priority more than 10 surveys..!'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            RountingPriority.objects.all().delete()
            for survey in post_data:
                try:
                    progrp_obj = ProjectGroup.objects.get(project_group_number=survey,project_group_status="Live")
                    RountingPriority.objects.update_or_create(project_group = progrp_obj)
                except:
                    continue
            return Response({'message': 'Priority Surveys Updated'}, status=status.HTTP_200_OK)


class ReRountingUserRegister(APIView):

    def get(self,request):
        try:
            ReRoutingUser.objects.get(
                visitorId = request.GET.get('ruid')
            )
            return Response({'Success': True}, status=status.HTTP_200_OK)
        except:
            return Response({'Success': False}, status=status.HTTP_200_OK)
        
    def post(self,request):
        email = request.data.get('email')
        usc = request.data.get('usc','internal')
        if email:
            routobj,created = ReRoutingUser.objects.get_or_create(
                email = email,
                defaults = {
                    "visitorId" : request.GET.get('ruid',hashlib.md5(uuid.uuid4().hex.encode()).hexdigest()),
                    "usc" : usc
                }
            )
            return Response({'Data': routobj.visitorId}, status=status.HTTP_200_OK)
        return Response({"status":2,"message":"Thank You For Your Time..!"}, status=status.HTTP_200_OK)


class ReRountingUserCounts(APIView):

    def get(self,request):
        start_date = request.GET.get('start_date',None)
        last_date = request.GET.get('last_date',None)

        rerouting_supplier_list = ReRoutingUser.objects.all()

        if start_date:
            rerouting_supplier_list = rerouting_supplier_list.filter(created_at__date__gte = start_date)
        if last_date:
            rerouting_supplier_list = rerouting_supplier_list.filter(created_at__date__lte = last_date)
        
        rerouting_supplier_list = rerouting_supplier_list.values('email','usc','visitorId')

        return Response({"userlist" : rerouting_supplier_list,"usercount" : rerouting_supplier_list.count()}, status=status.HTTP_200_OK)


class SurveySideRedirectAPI(APIView):

    def get(self, request):

        surveynumber = request.GET.get('surveynumber')
        suppliercode = request.GET.get('sc')
        subsuppliercode = request.GET.get('ssc')
        ruid = request.GET.get('ruid')

        try:  
            if subsuppliercode not in ['',None]:
                finalised_survey_list = ProjectGroupSubSupplier.objects.get(sub_supplier_org__sub_supplier_code = subsuppliercode,sub_supplier_status='Live',project_group__project_group_status = 'Live',project_group__project_group_number = surveynumber)
            else:
                finalised_survey_list = ProjectGroupSupplier.objects.get(supplier_org__supplier_code=suppliercode,supplier_status='Live',project_group__project_group_status = 'Live',project_group__project_group_number = surveynumber)
        
            return Response ({'status': 1,'URL':finalised_survey_list.supplier_survey_url.replace('%%PID%%',ruid).replace('XXXXX',ruid)}) 
        except:
            return Response ({'status': '2'})
