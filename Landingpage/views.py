# *********** Django libraries ****************
from django.shortcuts import render, redirect
from django.conf import settings
from django.db.models.aggregates import Count
from django.db.models import Q

# rest-framework imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view

# in-projects import
from Surveyentry.models import *
from Project.models import *
from Landingpage.models import *
from Surveyentry.custom_function import *

# automated email notifications imports
from automated_email_notifications.project_custom_functions import update_status

# third-pary libraries
from hashlib import sha1
from urllib.parse import unquote
from django.utils import timezone
import requests
import asyncio

final_status_dict= {
    "4" : "Completed - Postback",
    "5" : "Terminate - Postback",
    "6" : "Quotafull - Postback",
    "7" : "Security Terminate - Postback",
}

def comman_function(response,source):

    if int(source)>0:
        group_code = response.project_group_number
        required_N = response.respondentprojectdetail.project_group_completes
        supplier_required_N = response.respondentsupplierdetail.supplier_requiredN
        
        respondent_details = RespondentDetail.objects.filter(project_group_number=group_code, url_type="Live") .aggregate(
            supplier_achieved_N = Count('source', filter=Q(source=source,resp_status="4")),
            achieved_N = Count('resp_status', filter=Q(resp_status="4"))
        )


        if int(required_N) <= respondent_details['achieved_N']:
            group_obj = ProjectGroup.objects.get(project_group_number=group_code)
            group_obj.project_group_status = "Paused"
            group_obj.save()

        if int(supplier_required_N) <= respondent_details['supplier_achieved_N']:
            group_supplier_obj = ProjectGroupSupplier.objects.get(project_group__project_group_number=group_code)
            group_supplier_obj.supplier_status = "Paused"
            group_supplier_obj.save()
        return True
    return False

def capture_status(request):

    final_status = request.GET.get("stv")
    RID = request.GET.get("RID", request.GET.get("mid"))
    redirectID = request.GET.get("prid")
    template_name = 'Landingpage/landing_page.html'
    context = {}
    detail_reason = ""
    security_term = False
    panel_redirect_url = "https://www.opinionsdeal.com/"
    cpi = request.GET.get('cpi')
    url_data = request.GET

    if RID and (final_status in ["4","5","6","7"]):
        try:
            # if True:
            if redirectID:
                response = RespondentDetail.objects.get(respondenturldetail__RID=RID, respondentprojectdetail__project_group_redirectID=redirectID)
            else:
                response = RespondentDetail.objects.get(respondenturldetail__RID=RID)

            current_status = response.resp_status

            if current_status == "3":
            
                PID = response.respondenturldetail.pid
                source = int(response.source)
                urltype = response.url_type
                if final_status == "4":
                    redirect_type = response.respondenturldetail.project_redirect_type
                    if redirect_type == "1":
                        project_redirect_id = response.respondentprojectdetail.project_group_redirectID
                        if project_redirect_id != redirectID:
                            security_term = True
                            response.resp_status = "7"
                            response.end_time = timezone.now()
                            response.save()
                    if not(security_term):
                        detail_reason = "Completed"
                        if cpi not in ["",None]:
                            response.supplier_cpi = cpi
                            clientBackTrackingDetails.objects.update_or_create(respondent = response, defaults = {"captured_url_params" : url_data})
                        response.resp_status = "4"
                        response.end_time = timezone.now()
                        response.save()

                        response.respondentpagedetails.endpageurl_link = request.build_absolute_uri()
                        response.respondentpagedetails.save()
                    
                        if int(source)>0:
                            group_code = response.project_group_number
                            required_N = response.respondentprojectdetail.project_group_completes
                            supplier_required_N = response.respondentsupplierdetail.supplier_requiredN
                            
                            respondent_details = RespondentDetail.objects.filter(project_group_number=group_code, url_type="Live") .aggregate(
                                supplier_achieved_N = Count('source', filter=Q(source=source,resp_status="4")),
                                achieved_N = Count('resp_status', filter=Q(resp_status="4"))
                            )

                            if int(required_N) <= respondent_details['achieved_N']:
                                group_obj = ProjectGroup.objects.get(project_group_number=group_code)
                                update_status(group_obj.id, "Paused", action='change-projectgroup-status',user=request.user)

                            if int(supplier_required_N) <= respondent_details['supplier_achieved_N']:
                                group_supplier_obj = ProjectGroupSupplier.objects.get(project_group__project_group_number=group_code, supplier_org__id=source)
                                update_status(group_supplier_obj.id, "Paused", action='change-projectgroupsupplier-status')
                elif final_status == "5":
                    detail_reason = "Client-Side Terminate"
                    response.resp_status = "5"
                    response.end_time = timezone.now()
                    response.save()
                elif final_status == "6":    
                    detail_reason = "Client-Side Quotafull"
                    response.resp_status = "6"
                    response.end_time = timezone.now()
                    response.save()
                else:      
                    detail_reason = "Client-Side Security Terminate"
                    response.resp_status = "7"
                    response.end_time = timezone.now()
                    response.save()
                calculated_duration = response.end_time - response.start_time
                duration_in_minutes = calculated_duration.seconds/60.0

                # response.resp_status = final_status
                response.final_detailed_reason = detail_reason
                response.duration = duration_in_minutes
                response.save()

                if int(source) > 0:
                    if final_status in ["5", "6", "7"]:
                        return redirect("Surveyentry:supplierterminate", response.respondenturldetail.url_safe_string)
                    else:
                        return redirect("Surveyentry:suppliersideterminate", response.respondenturldetail.url_safe_string)
                else:
                    context["PID"] = PID
                    context["Final_Status"] = detail_reason
        except:
          pass

    if final_status == '4':

        context["heading"] = "Completed Page..!"
        context["message"] = "Thank you for completing the survey. We will credit your rewards within few weeks."
    elif final_status == '6':

        context["heading"] = "Quotafull Page..!"
        context["message"] = "Thank you for your time. We have met the target for this study."
    else:

        context["heading"] = "Screened Page..!"
        context["message"] = "Thank you for your time. Unfortunately you are not qualified for this survey."

    return render(request, template_name, context)


@api_view(['GET',])
def CaptureStatusLandingPageAPIFunc(request):

    final_status = request.GET.get("stv")
    RID = request.GET.get("RID",request.GET.get("mid"))
    redirectID = request.GET.get("prid")
    lucid_cpi = request.GET.get("cpi",None)
    context = {}
    detail_reason = ""
    security_term = False


    if RID and (final_status in ["4","5","6","7"]):

        try:
            response_obj = RespondentDetail.objects.select_related('respondenturldetail','respondentprojectdetail','respondentsupplierdetail').filter(respondenturldetail__RID=RID)
            
            api_client = True if response_obj.first().respondentdetailsrelationalfield.project.project_customer.customer_url_code in ['toluna','zamplia'] else False
            
            # if True:
            if not(api_client) and redirectID:
                response_obj = response_obj.filter(respondentprojectdetail__project_group_redirectID=redirectID)
            
            response = response_obj.first()
            current_status = response.resp_status

            if current_status == "3":
            
                PID = response.respondenturldetail.pid
                source = int(response.source)
                urltype = response.url_type

                if final_status == "4":
                    redirect_type = response.respondenturldetail.project_redirect_type
                    response.client_landing_url = request.build_absolute_uri()
                    if response.respondentdetailsrelationalfield.project.project_customer.customer_url_code == 'lucid-redirect' and lucid_cpi != None:
                        response.project_group_cpi = lucid_cpi
                    response.save()
                    if redirect_type == "1":
                        project_redirect_id = response.respondentprojectdetail.project_group_redirectID
                        if project_redirect_id != redirectID:
                            security_term = True
                            response.resp_status = "7"
                            response.end_time = timezone.now()
                            response.save()
                            detail_reason = "URL manipulation. Captured status is Completed"

                    if not(security_term):

                        detail_reason = "Completed"
                        response.resp_status = "4"
                        response.end_time = timezone.now()
                        response.save()
                    
                        if int(source)>0:
                            if response.respondentdetailsrelationalfield.source.supplier_type == '5':
                                sub_supplier_postbackurl = response.respondentprojectgroupsubsupplier.sub_supplier_postback_url
                                if sub_supplier_postbackurl not in ['', None]:
                                    try:
                                        response.respondentprojectgroupsubsupplier.sub_supplier_postback_url_response = requests.post(sub_supplier_postbackurl.replace('%%PID%%',PID))
                                        response.respondentprojectgroupsubsupplier.save()
                                    except Exception as e:
                                        response.respondentprojectgroupsubsupplier.sub_supplier_postback_url_response = e
                                        response.respondentprojectgroupsubsupplier.save()
                            else:
                                postbackurl = response.respondentsupplierdetail.supplier_postback_url
                                if postbackurl not in ['', None]:
                                    try:
                                        response.respondentsupplierdetail.supplier_postback_url_response = requests.post(postbackurl.replace('%%PID%%',PID))
                                        response.respondentsupplierdetail.save()
                                    except Exception as e:
                                        response.respondentsupplierdetail.supplier_postback_url_response = e
                                        response.respondentsupplierdetail.save()

                elif final_status == "5":
                    detail_reason = "Client-Side Terminate"
                    response.resp_status = "5"
                    response.end_time = timezone.now()
                    response.save()

                elif final_status == "6":     
                    detail_reason = "Client-Side Quotafull"
                    response.resp_status = "6"
                    response.end_time = timezone.now()
                    response.save()
                else:
                    detail_reason = "Client-Side Security Terminate"
                    response.resp_status = "7"
                    response.end_time = timezone.now()
                    response.save()
                calculated_duration = response.end_time - response.start_time
                duration_in_minutes = calculated_duration.seconds/60.0

                # response.resp_status = final_status
                response.final_detailed_reason = detail_reason
                response.duration = duration_in_minutes
                response.save()

                if response.url_type == "Live" and int(response.respondentprojectdetail.project_group_loi)>1:
                    if response.resp_status == '4' and int(duration_in_minutes) < int(response.respondentprojectdetail.project_group_loi)/4:
                        response.resp_status = "7"
                        response.final_detailed_reason = "Speeder - {duration_in_minutes}"
                        response.end_time = timezone.now()
                        response.save()

                if response.respondentdetailsrelationalfield.source.supplier_type == '4':
                    
                    # GENERATE KEY TO AUTHENTICATE YOURSELF TO THE Opinions Deal API
                    hash_key_params = f'resp_token={response.respondenturldetail.pid}&resp_status={response.resp_status}'
                    secret_key = 'PSfX8aW2VezKXmfmJpZ7xTaUg3BWfwPQ'
                    hash_key = hash_key_params + secret_key
                    hash_key = sha1(hash_key.encode()).hexdigest()
                    survey_no = response.project_group_number
                    # GENERATE KEY TO AUTHENTICATE YOURSELF TO THE Opinions Deal API

                    callOpinionsDealApi(api_url=settings.OPINIONSDEALSNEW_BASE_URL + f'panel/survey/status-store?{hash_key_params}&hkey={hash_key}&survey_no={survey_no}', req_method="post")

                
                if int(source) > 0:
                    return Response(data={'status':5, 'urlsafe_str':response.respondenturldetail.url_safe_string})
                else:
                    context["PID"] = PID
                    context["Final_Status"] = detail_reason
        except:
            pass
   
    if final_status == '4':

        context["heading"] = "Completed Page..!"
        context["message"] = "Thank you for completing the survey. We will credit your rewards within few weeks."
        

    elif final_status == '6':

        context["heading"] = "Quotafull Page..!"
        context["message"] = "Thank you for your time. We have met the target for this study."
        
    else:
        context["heading"] = "Screened Page..!"
        context["message"] = "Thank you for your time. Unfortunately you are not qualified for this survey."
    try:
        context["status"] = response.resp_status
        context["urlsafe_str"] = response.respondenturldetail.url_safe_string
    except:
        context["status"] = 0
    return Response(data=context)



class postbackTracking(APIView):
    def get(self, request):

        final_status = request.GET.get("stupid")
        redirectID = request.GET.get("surid",None)
        RID = request.GET.get("transaction_id")

        actualURL = unquote(request.build_absolute_uri())
        newurl = capturePostbackHits(capturedURL = actualURL, method_name = 'GET')
        newurl.save()

        if RID and (final_status in ["4","5","6","7"]):
            try:
                if redirectID:
                    response = RespondentDetail.objects.get(respondenturldetail__RID=RID, respondentprojectdetail__project_group_redirectID=redirectID)
                else:
                    response = RespondentDetail.objects.get(respondenturldetail__RID=RID)

                current_status = response.resp_status
                source = response.source

                if current_status == "3":
                    if final_status in ["4","5","6","7"]:
                        response.final_detailed_reason = final_status_dict[final_status]
                        response.resp_status = final_status
                        calculated_duration = response.end_time - response.start_time
                        response.duration = calculated_duration.seconds/60.0
                        response.save()
                        comman_function(response,source)
                return Response({"status":"success"}, status=status.HTTP_200_OK)
            except:
                pass
        return Response({"status":"FORBIDDEN","message":"Wrong Transaction ID"}, status=status.HTTP_403_FORBIDDEN)

    def post(self, request):
        final_status = request.GET.get("stupid")
        redirectID = request.GET.get("surid")
        RID = request.GET.get("transaction_id")

        actualURL = unquote(request.build_absolute_uri())
        newurl = capturePostbackHits(capturedURL = actualURL, method_name = "POST")
        newurl.save()
        
        if redirectID and RID and (final_status in ["4"]):
            try:
                response = RespondentDetail.objects.get(respondenturldetail__RID=RID, respondentprojectdetail__project_group_redirectID=redirectID)

                current_status = response.resp_status
                source = response.source

                if current_status == "3":

                    if final_status in ["4","5","6","7"]:
                        response.final_detailed_reason = final_status_dict[final_status]
                        response.resp_status = final_status
                        calculated_duration = response.end_time - response.start_time
                        response.duration = calculated_duration.seconds/60.0
                        response.save()
                        comman_function(response,source)
                return Response({"status":"success"}, status=status.HTTP_200_OK)
            except:
                pass
        return Response({"status":"FORBIDDEN","message":"Wrong Transaction ID"}, status=status.HTTP_403_FORBIDDEN)
