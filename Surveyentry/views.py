import base64 ,datetime ,hmac ,json ,requests ,geoip2.webservice ,concurrent.futures ,uuid, secrets, re, hashlib
import random
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db.models.aggregates import Count
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from ClientSupplierAPIIntegration.TolunaClientAPI.models import ClientLayer, ClientQuota, ClientSubQuota, ClientSurveyPrescreenerQuestions
from Logapp.views import surveyentry_log
from Questions.models import TranslatedAnswer, TranslatedQuestion, ZipCodeMappingTable
from Recontact_Section.models import Recontact
from Supplier.models import SupplierAPIAdditionalfield, SupplierOrgAuthKeyDetails, SupplierOrganisation
from SupplierAPI.models import LucidCountryLanguageMapping
from Project.models import MultipleURL, ProjeGroupForceStop, ProjectGroup, ProjectGroupSubSupplier, ProjectGroupSupplier, ZipCode
from Prescreener.models import ProjectGroupPrescreener
from Surveyentry.custom_function import callOpinionsDealApi, hmac_sha1_encoding
from Surveyentry.models import AffiliateRouterExtraURLParams, DisqoQueryParam, GEOIPAPItable, ProjectGroupPrescreenerDataStore, ResearchDefenderFailureReasonDataStore, ResearchDefenderResponseDetail, ResearchDefenderSearch, RespondentDetail, RespondentDetailTolunaFields, RespondentDetailsRelationalfield, RespondentDeviceDetail, RespondentPageDetails, RespondentProjectDetail, RespondentProjectGroupSubSupplier, RespondentResearchDefenderDetail, RespondentRoutingDetail, RespondentSupplierDetail, RespondentURLDetail, SurveyEntryWelcomePageContent
from Surveyentry.serializers import PrescreenerForBeforeSurveyEntry, ProjectGroupPrescreenerQuestionsListSerializer
from affiliaterouter.custom_functions import get_project_group_supplier_overall, survey_decision
from employee.models import Country
from affiliaterouter.models import RountingPriority
from myproject.credentials import get_credential_details
from automated_email_notifications.project_custom_functions import update_status
from urllib.parse import unquote
from fuzzywuzzy import fuzz
from rest_framework.views import APIView


class healtcheck(APIView):
    context_object_name = 'context'
    def get(self,request):
        return Response(status=status.HTTP_200_OK)

      
class SurveyEntryAPIView(APIView):

    def get(self,request):

        # *********************Capture Url parameters ********************* #
        screened = False
        final_detailed_reason = ""
        encodedS_value = request.GET.get('glsid')
        source = request.GET.get('source',0)
        pub_id = request.GET.get('pubid')
        rsid = request.GET.get('rsid')
        pid = request.GET.get('PID', request.GET.get('pid'))
        userid = request.GET.get('userid',None)
        isTest = request.GET.get('isTest')
        api_supplier = request.GET.get('api_supplier')
        pgn = request.GET.get('pgn')
        ruid = request.GET.get('ruid', '')
        us = request.GET.get('router','1')  # Which type of Supplier/UTM Source
        supplier_source = request.GET.get('um', None)
        sub_sup_code = request.GET.get('sub_sup', None)  ## This Parameter For Use Only AD Panel Supplier

        if api_supplier=='disqo':
            auth = request.GET.get('auth')
            clientId = request.GET.get('clientId')
            projectId = request.GET.get('projectId')
            quotaIds = request.GET.get('quotaIds')
            supplierId = request.GET.get('supplierId')
            tid = request.GET.get('tid')
            
        # If any of the parameter is not available in survey URL, it will be redirected to survey term page.
        if not(encodedS_value):
            return Response(data={'status':'2'}) # 2 => Terminate
        
        actualURL = unquote(request.build_absolute_uri())
        urltype = 'Test' if isTest else 'Live'
        userAgent = request.META["HTTP_USER_AGENT"]
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        operating_system = request.user_agent.os
        browser = request.user_agent.browser
        mobile = request.user_agent.is_mobile
        tablet = request.user_agent.is_tablet
        touch_capable = request.user_agent.is_touch_capable
        desktop = request.user_agent.is_pc
        bot = request.user_agent.is_bot
        
        try:
            project_group = ProjectGroup.objects.get(project_group_encodedS_value = encodedS_value)
            project_group_loi = project_group.project_group_loi
            survey_status = project_group.project_group_status
            requiredN = project_group.project_group_completes
            required_clicks = project_group.project_group_clicks
            client_cpi = project_group.project_group_cpi
            project_group_redirectID = project_group.project_group_redirectID
            project_number = project_group.project.project_number
            project_redirect_type = project_group.project.project_redirect_type
            project_group_number = project_group.project_group_number
            project_group_security_check =  project_group.project_group_security_check
            project_group_language = project_group.project_group_language
            if project_group_security_check:
                project_group_ip_check = project_group.project_group_ip_check
                project_group_pid_check = project_group.project_group_pid_check
                research_defender_oe_check = project_group.research_defender_oe_check
                respondent_risk_check = project_group.respondent_risk_check 
                failure_check = project_group.failure_check 
                duplicate_check = project_group.duplicate_check 
                threat_potential_check = project_group.threat_potential_check 
            else:
                project_group_ip_check = False
                project_group_pid_check = False
                research_defender_oe_check = False
                respondent_risk_check = False
                failure_check = False
                duplicate_check = False
                threat_potential_check = False

            project_group_allowed_svscore = 100
            project_group_allowed_dupescore = 100
            project_group_allowed_fraudscore = 100 
            duplicate_score = project_group.duplicate_score

            # ********************* Save initial data: *********************
            resp = RespondentDetail.objects.create(
                us = us,
                source=source,
                url_type=urltype,
                project_number=project_number,
                project_group_number=project_group_number,
                project_group_cpi=client_cpi,
            )

            # Generate RID and PID if pid not passed in URL Parameters
            uuid4_str = uuid.uuid4().hex
            RID = hashlib.md5(str(resp.id).encode() + uuid4_str.encode()).hexdigest()
            if not pid:
                pid = RID

            clientURL = ""
            if project_group.project_group_client_url_type == "1":
                if urltype == 'Test':
                    clientURL = project_group.project_group_testurl
                else:
                    clientURL = project_group.project_group_liveurl
            elif project_group.project_group_client_url_type == "2":
                                
                multiple_url_obj = MultipleURL.objects.filter(project_group=project_group, is_used = False).exists()
                if not(multiple_url_obj):
                    screened = True
                    final_detailed_reason = "Multiple URL not available"
            else:
                recontact_obj = Recontact.objects.filter(project_group=project_group, pid= pid, is_used = False)
                if recontact_obj.exists():
                    recon_obj = recontact_obj.first()
                    recon_obj.is_used = True
                    recon_obj.save()

                    RID = recon_obj.rid
                    pid = recon_obj.pid
                    clientURL = recon_obj.url
                    
                else:
                    screened = True
                    final_detailed_reason = "Recontact URL not available"
            
            url_str = str(resp.id)+"$"+secrets.token_urlsafe(40)
            urlsafe_str = hashlib.md5(url_str.encode()).hexdigest()

            mac_address = uuid.getnode()

            RespondentURLDetail.objects.create(
                respondent = resp,
                actual_url = actualURL,
                url_safe_string = urlsafe_str,
                user_agent = userAgent,
                ip_address = ip,
                pid = pid,
                userid = userid,
                RID = RID,
                project_redirect_type = project_redirect_type,
                ruid = ruid,
                pub_id = pub_id if pub_id else '',
                rsid = rsid if rsid else '',
                sub_sup_id = sub_sup_code if sub_sup_code else '',
            )

            RespondentDeviceDetail.objects.create(
                respondent = resp,
                operating_system = operating_system,
                browser = browser,
                mobile = mobile,
                tablet = tablet,
                desktop = desktop,
                touch_capable = touch_capable,
                bot = bot,
                mac_address = mac_address
            )

            RespondentProjectDetail.objects.create(
                respondent = resp,
                project_group_status = survey_status,
                project_group_loi = project_group_loi,
                project_group_completes = requiredN,
                project_group_clicks = required_clicks,
                project_group_redirectID = project_group_redirectID,
                clientURL = clientURL,
                project_group_security_check =  project_group_security_check,
                project_group_ip_check = project_group_ip_check,
                project_group_pid_check = project_group_pid_check,
                research_defender_oe_check = research_defender_oe_check,
                project_group_allowed_svscore = project_group_allowed_svscore,
                project_group_allowed_dupescore = project_group_allowed_dupescore,
                project_group_allowed_fraudscore = project_group_allowed_fraudscore,
                respondent_risk_check = respondent_risk_check,
                failure_check = failure_check,
                duplicate_check = duplicate_check,
                duplicate_score = duplicate_score,
                threat_potential_check = threat_potential_check
            )  

            # FETCH EXTRA URL PARAMS THAT CAME FROM THE AFFILIATEROUTER TRAFFIC, SO THAT WE CAN SAVE THE PARAMS IN THE DB AND LATER USE IT IN SUPPLIERSIDEREDIRECT S2S POSTBACK URL
            exclude_params_list = ['glsid','source','PID','pid','router','rsid','pubid']
            parameter_dict = {}
            parameter_list = []
            for key, value in request.GET.items():
                if key in exclude_params_list:
                    continue
                else:
                    parameter_dict[key] = value
                    parameter_list.append(key)
            RespondentPageDetails.objects.create(respondent=resp,last_page_seen = "Survey Entry Page", url_extra_params=parameter_dict)

            # IF THE RESPONDENT IS COMING FROM AFFILIATEROUTER SUPPLIER, THEN STORE ALL HIS CUSTOM URL PARAMS IN A SEPARATE TABLE
            if supplier_source == 'af':
                af_url_params = request.GET

                AffiliateRouterExtraURLParams.objects.create(respondent=resp, ubid=af_url_params.get('ubid'), zoneid=af_url_params.get('zoneid'), campaignid=af_url_params.get('campaignid'), os=af_url_params.get('os'), country=af_url_params.get('country'), cost=af_url_params.get('cost'), device=af_url_params.get('device'), browser=af_url_params.get('browser'), browserversion=af_url_params.get('browserversion'), osversion=af_url_params.get('osversion'), countryname=af_url_params.get('countryname'), region=af_url_params.get('region'), useragent=af_url_params.get('useragent'), language=af_url_params.get('language'), connection_type=af_url_params.get('connection_type'), carrier=af_url_params.get('carrier'), clickID=af_url_params.get('clickID'), bannerid=af_url_params.get('bannerid'), user_activity=af_url_params.get('user_activity'), payout=af_url_params.get('payout'), zone_type=af_url_params.get('zone_type'))

            # IF THE RESPONDENT IS COMING FROM AFFILIATEROUTER SUPPLIER, THEN STORE ALL HIS CUSTOM URL PARAMS IN A SEPARATE TABLE
            if api_supplier:
                if api_supplier == 'disqo':
                    DisqoQueryParam.objects.create(
                        respondent = resp,
                        auth = auth,
                        clientId = clientId,
                        pid = pid,
                        projectId = projectId,
                        quotaIds = quotaIds,
                        supplierId = supplierId,
                        tid = tid
                    )

            supplier_cpi = 0
            
            try:
                supplierorg_obj = SupplierOrganisation.objects.get(id=source)
            except Exception as error:
                supplierorg_obj = None
            
            try:
                projgrp_supp_obj = ProjectGroupSupplier.objects.get(project_group= project_group, supplier_org=supplierorg_obj)
                supplier_cpi = projgrp_supp_obj.cpi
                supplier_status = projgrp_supp_obj.supplier_status
                supplier_requiredN = projgrp_supp_obj.completes
                supplier_required_clicks = projgrp_supp_obj.clicks
                supplier_complete_url = projgrp_supp_obj.supplier_completeurl
                supplier_terminate_url = projgrp_supp_obj.supplier_terminateurl
                supplier_quotafull_url = projgrp_supp_obj.supplier_quotafullurl
                supplier_securityterminate_url = projgrp_supp_obj.supplier_securityterminateurl
                supplier_internal_terminate_redirect_url = projgrp_supp_obj.supplier_internal_terminate_redirect_url
                supplier_terminate_no_project_available = projgrp_supp_obj.supplier_terminate_no_project_available
                if supplier_internal_terminate_redirect_url in ['',None]:
                    supplier_internal_terminate_redirect_url = supplier_terminate_url
                    supplier_internal_terminate_redirect_url = supplier_terminate_url
                supplier_postback_url = projgrp_supp_obj.supplier_postbackurl
            except Exception as error:
                projgrp_supp_obj = None
        

            if projgrp_supp_obj not in ['', None]:
                RespondentSupplierDetail.objects.create(
                    respondent = resp,
                    supplier_status = supplier_status,
                    supplier_requiredN = supplier_requiredN,
                    supplier_required_clicks = supplier_required_clicks,
                    supplier_complete_url = supplier_complete_url,
                    supplier_terminate_url = supplier_terminate_url,
                    supplier_quotafull_url = supplier_quotafull_url,
                    supplier_securityterminate_url = supplier_securityterminate_url,
                    supplier_postback_url = supplier_postback_url,
                    supplier_terminate_no_project_available = supplier_terminate_no_project_available,
                    supplier_internal_terminate_redirect_url = supplier_internal_terminate_redirect_url
                )
                
            if projgrp_supp_obj != None and projgrp_supp_obj.supplier_org.supplier_type == '5':

                projgrp_sub_supp_obj = ProjectGroupSubSupplier.objects.get(
                    project_group = project_group,
                    sub_supplier_org__sub_supplier_code = sub_sup_code
                )
                sub_supplier_status = projgrp_sub_supp_obj.sub_supplier_status
                supplier_cpi = projgrp_sub_supp_obj.cpi
                
                RespondentProjectGroupSubSupplier.objects.create(
                    respondent = resp,
                    project_group_sub_supplier = projgrp_sub_supp_obj,
                    sub_supplier_requiredN = projgrp_sub_supp_obj.completes,
                    sub_supplier_required_clicks = projgrp_sub_supp_obj.clicks,
                    sub_supplier_complete_url = projgrp_sub_supp_obj.sub_supplier_completeurl,
                    sub_supplier_terminate_url = projgrp_sub_supp_obj.sub_supplier_terminateurl,
                    sub_supplier_quotafull_url = projgrp_sub_supp_obj.sub_supplier_quotafullurl,
                    sub_supplier_securityterminate_url = projgrp_sub_supp_obj.sub_supplier_securityterminateurl,
                    sub_supplier_internal_terminate_redirect_url = projgrp_sub_supp_obj.sub_supplier_internal_terminate_redirect_url,
                    sub_supplier_terminate_no_project_available = projgrp_sub_supp_obj.sub_supplier_terminate_no_project_available,
                    sub_supplier_postback_url = projgrp_sub_supp_obj.sub_supplier_postbackurl
                )
            else:
                projgrp_sub_supp_obj = None
            
            resp.supplier_cpi = supplier_cpi
            resp.save()

            RespondentDetailsRelationalfield.objects.create(
                respondent = resp,
                source = supplierorg_obj,
                project = project_group.project,
                project_group = project_group,
                project_group_supplier = projgrp_supp_obj,
                project_group_sub_supplier = projgrp_sub_supp_obj
            )

            # ********************* END Save respondent detail relationalfield data: *********************
            
            # ********************* Check Status Specific Terminations *********************
            
            if urltype == 'Live':
                if survey_status not in ['Live']:
                    screened = True
                    final_detailed_reason = f"Survey is not live. Status is {survey_status}"
                
                if int(source) > 0:
                    if not(screened) and projgrp_supp_obj in ['', None]:
                        screened = True
                        final_detailed_reason = "Supplier URL Manipulation"

                    if not(screened) and sub_sup_code not in ['', None] and projgrp_sub_supp_obj in ['', None]:
                        screened = True
                        final_detailed_reason = "Sub-Supplier URL Manipulation"    

                    if not(screened) and supplier_status not in ['Live']:
                        screened = True
                        final_detailed_reason = f"Supplier is not live. Supplier status is {supplier_status}"

                    if not(screened) and projgrp_supp_obj.supplier_org.supplier_type == '5' and sub_supplier_status not in ['Live']:
                        screened = True
                        final_detailed_reason = f"Sub Supplier is not live. Supplier status is {sub_supplier_status}"
                    

            # ********************* Check Device terminations *********************
            if not(screened):
                project_device_type = project_group.project_device_type
                
                if project_device_type == '2' and not desktop:
                    screened = True
                    final_detailed_reason = "Desktop Device does not match"
                elif project_device_type == '3' and not tablet:
                    screened = True
                    final_detailed_reason = "Tablet Device does not match"
                elif project_device_type == '4' and not mobile:
                    screened = True
                    final_detailed_reason = "Mobile Device does not match"
                elif project_device_type == '5' and not (desktop or tablet):
                    screened = True
                    final_detailed_reason = "Desktop and Tablet Device does not match"
                elif project_device_type == '6' and not (desktop or mobile):
                    screened = True
                    final_detailed_reason = "Desktop and Mobile Device does not match"
                elif project_device_type == '7' and not (tablet or mobile):
                    screened = True
                    final_detailed_reason = "Tablet and Mobile Device does not match"

                # ********************* Save additional Details ********************
        
                # ********************* Save respondent routing detail data: *********************
                if pgn:
                    previous_project_group_number_value = pgn
                    is_routing_value = True
                else:
                    previous_project_group_number_value = ''
                    is_routing_value = False
                
                RespondentRoutingDetail.objects.create(
                    respondent = resp,
                    base_supplier_cpi = supplier_cpi,
                    previous_project_group_number = previous_project_group_number_value,
                    is_routing = is_routing_value
                )

                    # ********************* END Save respondent routing detail data: *********************

        except Exception as error:
            surveyentry_log(f'{error}Exception number ------113 raised',encodedS_value)
            return Response(data={'status':'2'})
        
        if screened:
            resp.end_time = timezone.now()
            resp.duration = 0
            resp.resp_status = "2"
            resp.final_detailed_reason = final_detailed_reason
            resp.save()
            return Response(data={'status':'2','urlsafe_str':urlsafe_str}) # 2 => Supplier Redirect
        
        
        # **************** Update Project Group Statistics ************************
        
        context = {}

        page_contents = SurveyEntryWelcomePageContent.objects.filter(language=project_group_language).values('row_1_text','row_2_text','row_3_text','row_4_text','row_5_text')

        context['loi'] = project_group_loi
        context['urlsafe_str'] = urlsafe_str
        context['page_contents'] = page_contents
        context['message'] = 'Welcome Page Contents'
        context['status'] = '1'
        context['rd'] = RID
        context['sn'] = project_group_number
        return Response(data=context)



class SurveySecurityCheckAPIView(APIView):

    def get(self,request,urlsafe_str):
        screened = False
        respondent = RespondentDetail.objects.select_related('respondenturldetail').get(respondenturldetail__url_safe_string = urlsafe_str)
        urltype = respondent.url_type
        ip = respondent.respondenturldetail.ip_address
        source = respondent.source

        if int(source) > 0:
            if urltype == 'Live' and settings.SERVER_TYPE in ['production']:
                    
                    """# ===================================================================
                        MaxMind GEOIP2 API data Call Start
                    # ==================================================================="""

                    try:
                        if ip:
                            client = geoip2.webservice.Client('275599', 'fgjd0IOKJkfEvpHr')
                            API_response = client.country(ip)
                            country_iso = API_response.country.iso_code

                            try:
                                country_obj = Country.objects.get(country_code = country_iso)
                                geoip_obj = GEOIPAPItable.objects.update_or_create(RespondentDetail = respondent, defaults={'country' : country_obj})
                                geoip_obj.save()
                            except Exception as error:
                                surveyentry_log(f'{error}Exception number ------114 raised',urlsafe_str)
                                geoip_obj = GEOIPAPItable.objects.update_or_create(RespondentDetail = respondent, defaults={'city' : country_iso, 'maxmind_api_response' : API_response})
                                geoip_obj.save()
                                screened = True
                                final_detailed_reason = "Country Code outside of ISO list"
                        

                            if not(screened):
                                if country_iso.lower()!= respondent.respondentdetailsrelationalfield.project_group.project_group_country.country_code.lower():
                                    screened = True
                                    final_detailed_reason = "GEOIP"
                    except Exception as error:
                        surveyentry_log(f'{error}Exception number ------115 raised',urlsafe_str)
                        pass

                    """# ===================================================================
                        MaxMind GEOIP2 API data Call End
                    # ==================================================================="""

            respondent_details_obj = RespondentDetail.objects.filter(url_type="Live",respondenturldetail__ip_address = ip,resp_status__in=[2, 4, 5, 6, 7])
            if urltype == 'Live' and respondent.respondentdetailsrelationalfield.project_group.project_group_ip_check:

                if respondent.respondentdetailsrelationalfield.project_group.excluded_project_group == []:
                    ip_exist = respondent_details_obj.filter(project_number = respondent.project_number).exists()
                else:
                    ip_exist = respondent_details_obj.filter(project_group_number__in = respondent.respondentdetailsrelationalfield.project_group.excluded_project_group).exists()
                if ip_exist:
                    screened = True
                    final_detailed_reason = "IP Duplicate"

            # if urltype == 'Live' and respondent.respondentdetailsrelationalfield.project_group.project_group_pid_check:

            #     if respondent.respondentdetailsrelationalfield.project_group.excluded_project_group == []:
            #         pid_exist = respondent_details_obj.filter(project_number = respondent.project_number).exists()
            #     else:
            #         pid_exist = respondent_details_obj.filter(project_group_number__in = respondent.respondentdetailsrelationalfield.project_group.excluded_project_group).exists()
            #     if pid_exist:
            #         screened = True
            #         final_detailed_reason = "PID Duplicate"
            
            if not screened:
                respondent_details_list = RespondentDetail.objects.filter(url_type="Live",project_group_number = respondent.project_group_number)
                
                respondent_details = respondent_details_list.aggregate(
                    total_click_count = Count('resp_status',filter=(Q(resp_status__in=[3, 4, 5, 6, 7,8,9]))),
                    supplier_click_count = Count('source',filter=(Q(resp_status__in=[3, 4, 5, 6, 7,8,9], source = source))),
                    completes_count = Count('resp_status',filter=(Q(resp_status__in=[4,9]))),
                    supplier_completes_count = Count('resp_status',filter=(Q(resp_status__in=[4], source = source))),
                )
                
                # Terminate if number of clicks achieved for Project Group
                if int(respondent.respondentprojectdetail.project_group_clicks) <= respondent_details['total_click_count']:
                    screened = True
                    final_detailed_reason = "Project Target for clicks has been reached"
                    update_status(respondent.respondentdetailsrelationalfield.project_group.id, "Paused", action='change-projectgroup-status')
                    
                # Check Project Group Completes                    
                if not(screened):
                    if int(respondent.respondentprojectdetail.project_group_completes) <= respondent_details['completes_count']:
                        screened = True
                        final_detailed_reason = "Project Target for N has been reached"
                        update_status(respondent.respondentdetailsrelationalfield.project_group.id, "Paused", action='change-projectgroup-status')
                
                # Supplier Click Check
                if not(screened):
                    if int(respondent.respondentsupplierdetail.supplier_required_clicks) <= respondent_details['supplier_click_count']:
                        screened = True
                        final_detailed_reason = "Supplier Target for clicks has been reached"
                        update_status(respondent.respondentdetailsrelationalfield.project_group_supplier.id, "Paused", action='change-projectgroupsupplier-status')

                # Supplier Completes check        
                if not(screened):
                    if int(respondent.respondentsupplierdetail.supplier_requiredN) <= respondent_details['supplier_completes_count']:
                        screened = True
                        final_detailed_reason = "Supplier Target for N has been reached"
                        update_status(respondent.respondentdetailsrelationalfield.project_group_supplier.id, "Paused", action='change-projectgroupsupplier-status')

                # Check Sub Supplier Clicks
                if not(screened) and respondent.respondentdetailsrelationalfield.source.supplier_type == '5':
                    respondent_sub_supplier_details = respondent_details_list.filter(
                        respondenturldetail__sub_sup_id = respondent.respondenturldetail.sub_sup_id).aggregate(
                        sub_supplier_click_count = Count('respondenturldetail__sub_sup_id',filter=(Q(resp_status__in=[3, 4, 5, 6, 7,8,9]))),
                        sub_supplier_completes_count = Count('respondenturldetail__sub_sup_id',filter=(Q(resp_status__in=[4,9]))))
                    
                    # Sub Supplier Click Check
                    if not(screened) and int(respondent.respondentprojectgroupsubsupplier.sub_supplier_required_clicks) <= respondent_sub_supplier_details['sub_supplier_click_count']:
                        screened = True
                        final_detailed_reason = "Ad-Supplier Target for clicks has been reached"
                        respondent.respondentdetailsrelationalfield.project_group_sub_supplier.sub_supplier_status = 'Paused'
                        respondent.respondentdetailsrelationalfield.project_group_sub_supplier.save()
                    
                    # Sub Supplier Completes check
                    if not(screened) and int(respondent.respondentprojectgroupsubsupplier.sub_supplier_requiredN) <= respondent_sub_supplier_details['sub_supplier_completes_count']:
                        screened = True
                        final_detailed_reason = "Ad-Supplier Target for N has been reached"
                        respondent.respondentdetailsrelationalfield.project_group_sub_supplier.sub_supplier_status = 'Paused'
                        respondent.respondentdetailsrelationalfield.project_group_sub_supplier.save()
            
            if screened:
                respondent.end_time = timezone.now()
                respondent.duration = 0
                respondent.resp_status = "2"
                respondent.final_detailed_reason = final_detailed_reason
                respondent.save()
                return Response(data={'status':"2",'urlsafe_str':urlsafe_str})
        return Response({"status":"1"}, status=status.HTTP_200_OK)


class SurveyPrescreenerAPIView2(APIView):
    
    def get(self, request, url_string):
        context = {}

        try:
            resp_obj = RespondentDetail.objects.select_related('respondentdetailsrelationalfield','respondenturldetail','respondentpagedetails').get(respondenturldetail__url_safe_string=url_string, resp_status = "1")

            project_group_number = resp_obj.project_group_number

            prescreener_to_show = ProjectGroupPrescreener.objects.filter(project_group_id__project_group_number = project_group_number,is_enable = True)
            
            question_counts = prescreener_to_show.count()
            resp_obj.respondentpagedetails.total_question_shown = question_counts
            resp_obj.respondentpagedetails.last_page_seen = 'Prescreener Question GET'
            resp_obj.respondentpagedetails.save(update_fields = {'total_question_shown':question_counts, 'last_page_seen':'Prescreener Question GET'})
            if question_counts==0:
                # Check client url type for Multiple
                context['prescreener'] = []
                context['message'] = 'No Questions added in this Survey'
                return Response(data=context)
            else:
                # Offerwall Integration is pending.
                # if supplier_url_code in ["offerwall", "Offerwall"]:
                #     question_numbers_list = list(prescreener_to_show.values_list('translated_question_id__parent_question__parent_question_number', flat=True))
                #     supplier_request_url = resp_obj.respondentdetailsrelationalfield.source.supplier_buyer_apid.request_api_url
                #     offerwall_req_1 = callOfferWallApi(supplier_request_url + '/question-ids', req_method="post", json={"pid":resp_obj.respondenturldetail.pid, "question_numbers": question_numbers_list})
                #     if offerwall_req_1.status_code == 200:
                #         offewrwall_questions_list = offerwall_req_1.json()
                        
                #         for offewrwall_questions_key, offewrwall_questions_value in offewrwall_questions_list.items():
                #             url_extra_params_list[offewrwall_questions_key] = ','.join(offewrwall_questions_value) if type(offewrwall_questions_value) == list else offewrwall_questions_value
                #             translated_question_obj = TranslatedQuestion.objects.get(parent_question__parent_question_number=offewrwall_questions_key)
                #             question_data, question_data_created = ProjectGroupPrescreenerDataStore.objects.get_or_create(respondent = resp_obj, translated_question_id = translated_question_obj)

                #             if translated_question_obj.parent_question.parent_question_type == 'NU':
                #                 question_data.received_response = offewrwall_questions_value
                #                 question_data.save()
                #             if translated_question_obj.parent_question.parent_question_type == 'MS':
                #                 answer_options = TranslatedAnswer.objects.filter(parent_answer__parent_answer_id__in = offewrwall_questions_value)
                #                 question_data.selected_options.set(answer_options)
                #             if translated_question_obj.parent_question.parent_question_type == 'SS':
                #                 answer_options = TranslatedAnswer.objects.filter(parent_answer__parent_answer_id = offewrwall_questions_value)
                #                 question_data.selected_options.set(answer_options)

                #         # Store the url_extra_params_list in RespondentPageDetails
                #         resp_page_details.url_extra_params = url_extra_params_list
                #         resp_page_details.save(force_update=True, update_fields=["url_extra_params"])
                        
                # prescreener_to_show = prescreener_to_show.exclude(translated_question_id__parent_question__parent_question_number__in = url_extra_params_list.keys())
                serializer = ProjectGroupPrescreenerQuestionsListSerializer(prescreener_to_show, many=True, context = {'client_code':resp_obj.respondentdetailsrelationalfield.project.project_customer.customer_url_code})
                context['prescreener'] = serializer.data
                return Response(data=context)

        except Exception as error_msg:
            surveyentry_log(f'{error_msg}Exception number ------116 raised',url_string)
            return Response(data={'status':'2','error':error_msg}, status=status.HTTP_200_OK)

    
    def post(self, request, url_string):
        resp_obj = RespondentDetail.objects.only('respondentpagedetails').get(respondenturldetail__url_safe_string=url_string)
        project_group_number = resp_obj.project_group_number
        project_group = ProjectGroup.objects.get(project_group_number = project_group_number)
        quota_check = True if project_group.project.project_customer.customer_url_code in ['toluna','zamplia'] else False
        resp_obj.respondentpagedetails.last_page_seen = 'Prescreener Question GET'
        resp_obj.respondentpagedetails.save(update_fields = {'last_page_seen':'Prescreener Question Save'})
        question_answer_list = request.data
        question_list_store = []

        def parellel_threading_func(ques_ans_dict):
            terminate_respondent = False
            text_evaluation = False
            question_store = {}
            add_question_data = True
            question_obj = TranslatedQuestion.objects.get(Internal_question_id=ques_ans_dict['question_id'])
            prescreener_question_obj = ProjectGroupPrescreener.objects.get(translated_question_id__Internal_question_id=ques_ans_dict['question_id'], project_group_id__id = project_group.id,is_enable = True)
            question_data, question_data_created = ProjectGroupPrescreenerDataStore.objects.get_or_create(respondent = resp_obj, translated_question_id = question_obj, prescreener_question = prescreener_question_obj)

            if question_data.translated_question_id.parent_question_type in ['CTZIP','ZIP']:
                add_question_data = False
            else:
                if project_group.project.project_customer.customer_url_code == 'toluna':
                    question_store.update({'QuestionID':question_data.translated_question_id.toluna_question_id})
                elif project_group.project.project_customer.customer_url_code == 'zamplia':
                    question_store.update({'QuestionID':question_data.translated_question_id.zamplia_question_id})
                else:
                    question_store.update({'QuestionID':question_data.translated_question_id.Internal_question_id})

            sc_op = True
            research_defender_fail = False
            research_defender_fail_message = False
            parent_question_type = question_obj.parent_question.parent_question_type

            
            if parent_question_type in ['MS','SS','CTZIP']:
                has_no_answer = True
                if parent_question_type == 'CTZIP':
                    question_data.received_response = str(int(ques_ans_dict['answer_id']))
                    question_data.save()
                    ques_ans_dict['answer_id'] = list(ZipCodeMappingTable.objects.filter(
                        zipcode__in = [str(int(ques_ans_dict['answer_id'])),ques_ans_dict['answer_id']]).values_list('parent_answer_id__internal_answer_id',flat=True))

                allowed_options_obj = prescreener_question_obj.allowedoptions.filter(
                    internal_answer_id__in=ques_ans_dict['answer_id'] if type(ques_ans_dict['answer_id'])== list else [ques_ans_dict['answer_id']])

                sc_op = False if allowed_options_obj.exists() else True
                has_no_answer = False
                entered_answer_options = TranslatedAnswer.objects.filter(
                    translated_parent_question = question_obj,
                    internal_answer_id__in=ques_ans_dict['answer_id'] if type(ques_ans_dict['answer_id']) == list else [ques_ans_dict['answer_id']])
                
                entered_answer_options_list = list(entered_answer_options.values_list('id', flat=True))
                
                question_data.selected_options.add(*entered_answer_options_list)

                if add_question_data:
                    if len(entered_answer_options_list)<2:
                        if project_group.project.project_customer.customer_url_code == 'toluna':
                            updated_answer_id = entered_answer_options.first().toluna_answer_id
                        elif project_group.project.project_customer.customer_url_code == 'zamplia':
                            updated_answer_id = entered_answer_options.first().zamplia_answer_id
                        else:
                            updated_answer_id = entered_answer_options.first().internal_answer_id
                        question_store.update({'AnswerID':updated_answer_id})
                    else:
                        if project_group.project.project_customer.customer_url_code == 'toluna':
                            question_store.update({'Answers':[{'AnswerID':answer_id} for answer_id in list(entered_answer_options.values_list('toluna_answer_id', flat=True))]})
                        elif project_group.project.project_customer.customer_url_code == 'zamplia':
                            question_store.update({'Answers':[{'AnswerID':answer_id} for answer_id in list(entered_answer_options.values_list('zamplia_answer_id', flat=True))]})
                        else:
                            question_store.update({'Answers':[{'AnswerID':answer_id} for answer_id in list(entered_answer_options.values_list('internal_answer_id', flat=True))]})
                if has_no_answer:
                    sc_op = True
                    question_data.delete()
            
            if parent_question_type == 'NU':
                try:
                    entered_value = ques_ans_dict['answer_id']
                    numeric_response = ques_ans_dict['answer_id']
                    if len(str(entered_value)) > 0:
                        selected_option = TranslatedAnswer.objects.filter(translated_parent_question = question_obj)
                        question_data.selected_options.add(*selected_option)
                        if ques_ans_dict['qt'] == 'DT':
                            dob = datetime.datetime.strptime(entered_value,"%m/%d/%Y")
                            current_year = datetime.datetime.now()
                            entered_value = relativedelta(current_year, dob).years
                            question_data.calculated_response = entered_value
                        
                        if add_question_data and ques_ans_dict['qt'] != 'DT':
                            if len(selected_option)<2:
                                if project_group.project.project_customer.customer_url_code == 'toluna':
                                    updated_answer_id = selected_option.first().toluna_answer_id
                                elif project_group.project.project_customer.customer_url_code == 'zamplia':
                                    updated_answer_id = selected_option.first().zamplia_answer_id
                                else:
                                    updated_answer_id = selected_option.first().internal_answer_id
                                question_store.update({'AnswerID':updated_answer_id})
                            else:

                                if project_group.project.project_customer.customer_url_code == 'toluna':
                                    question_store.update({'Answers':[{'AnswerID':answer_id} for answer_id in list(entered_answer_options.values_list('toluna_answer_id', flat=True))]})
                                elif project_group.project.project_customer.customer_url_code == 'zamplia':
                                    question_store.update({'Answers':[{'AnswerID':answer_id} for answer_id in list(entered_answer_options.values_list('zamplia_answer_id', flat=True))]})
                                else:
                                    question_store.update({'Answers':[{'AnswerID':answer_id} for answer_id in list(entered_answer_options.values_list('internal_answer_id', flat=True))]})
                                
                        question_data.received_response = numeric_response
                        question_data.save()
                        
                        allowedRangeMin = prescreener_question_obj.allowedRangeMin.split(",")
                        allowedRangeMax = prescreener_question_obj.allowedRangeMax.split(",")

                        if quota_check:
                            sc_op  = False
                        else:
                            for index,value in enumerate(allowedRangeMin):
                                if int(entered_value) >= int(allowedRangeMin[index]) and int(entered_value) <= int(allowedRangeMax[index]):
                                    sc_op = False
                    else:
                        sc_op = True
                        question_data.delete()

                except Exception as error:
                    surveyentry_log(f'{error}Exception number ------123 raised',project_group_number)
            
            if parent_question_type == 'ZIP':
                try:
                    entered_value = str(int(ques_ans_dict['answer_id']))
                    question_data.received_response = entered_value
                    question_data.save()
                    sc_op = False

                    if question_obj.parent_question.parent_question_number in ['112498','181412'] and len(entered_value) > 3:
                        zipexist = int(entered_value) in list(map(int,prescreener_question_obj.allowed_zipcode_list))
                        if not zipexist and prescreener_question_obj.allowed_zipcode_list != []:
                            sc_op = True
                    else:
                        sc_op = True
                except Exception as error:
                    surveyentry_log(f'{error}Exception number ------124 raised',project_group_number)
            
            if parent_question_type == 'OE':
                try:
                    entered_value = ques_ans_dict['answer_id']
                    question_data.received_response = entered_value
                    question_data.save()
                    sc_op = False
                        
                    if len(entered_value) > 9:
                        encoded_page_load_time = request.POST.get(f"enc_page_load_time_{question_obj.id}", '')
                        encoded_pasted_text_data = request.POST.get(f"enc_pasted_text_{question_obj.id}", '')
                        encoded_answer_typed_time = request.POST.get(f"enc_text_typed_time_{question_obj.id}", '')
                        encoded_answer_submited_time = request.POST.get(f"enc_submit_text_time_{question_obj.id}", '')
                        page_load_time = request.POST.get('pageLoadTime', 0)
                        pasted_text_data = request.POST.get('pastedTextData', '')
                        answer_typed_time = request.POST.get('answeredTime',0)
                        answer_submited_time = request.POST.get('submitTime',0)
                        
                        # ========= Text evaluation ====================
                        all_oe_responses_list = list(ProjectGroupPrescreenerDataStore.objects.filter(respondent__project_group_number = project_group_number, translated_question_id = question_obj).exclude(id = question_data.id).values_list('received_response', flat=True))
                        text_evaluation_result_list = []
                        
                        for oe_resp in all_oe_responses_list:
                            set_ratio = fuzz.token_set_ratio(entered_value,oe_resp)   
                            text_evaluation_result_list.append(set_ratio)
                            if int(set_ratio)>85:
                                text_evaluation = True
                                question_data.text_evalution_flag = True
                                break
                        if len(text_evaluation_result_list) == 0:
                            question_data.text_evalution_result = 0
                        else:
                            question_data.text_evalution_result = max(text_evaluation_result_list)
                        question_data.save()
                        # ========= Text evaluation End ================

                        # ========= Research Defender ================
                        if project_group.research_defender_oe_check == True:
                            try:
                                resp_research_defender_obj = RespondentResearchDefenderDetail.objects.create(
                                    respondent = resp_obj,
                                    q_id = question_obj.id,
                                    entered_text = entered_value,
                                    encoded_page_load_time = encoded_page_load_time,
                                    encoded_answer_typed_time = encoded_answer_typed_time,
                                    encoded_answer_submited_time = encoded_answer_submited_time,
                                    page_load_time = page_load_time,
                                    answer_typed_time = answer_typed_time,
                                    answer_submited_time = answer_submited_time,
                                    sn_ud = resp_obj.respondenturldetail.RID,
                                    sy_nr = resp_obj.project_group_number,
                                    s_text_length = len(entered_value),

                                )
                                if pasted_text_data not in ['', None]:
                                    resp_research_defender_obj.pasted_text_data = pasted_text_data
                                if encoded_pasted_text_data not in ['', None]:
                                    resp_research_defender_obj.encoded_pasted_text_data = encoded_pasted_text_data
                                resp_research_defender_obj.save(force_update=True)

                                # Get the credentails details
                                credential_data = get_credential_details()
                                research_defender_url = f"{credential_data['research_defender_api_url']}/review/{credential_data['research_defender_publisher_api_key']}"
                                req_data = {
                                    "q_id": resp_research_defender_obj.q_id,
                                    "text": resp_research_defender_obj.entered_text,
                                    "c_text": resp_research_defender_obj.encoded_pasted_text_data,
                                    "t_page_load": resp_research_defender_obj.page_load_time,
                                    "t_text_typed": resp_research_defender_obj.answer_typed_time,
                                    "t_submit": resp_research_defender_obj.answer_submited_time,
                                    "s_text_length": resp_research_defender_obj.s_text_length,
                                    "sn_ud": resp_research_defender_obj.sn_ud,
                                    "sy_nr": resp_research_defender_obj.sy_nr
                                }
                                # Send request to research defender
                                research_defender_req = requests.post(research_defender_url, json=req_data)
                                if research_defender_req.status_code in [200]:
                                    research_defender_response = research_defender_req.json()

                                    for research_defender_resp_dtl in research_defender_response['results']:
                                        research_defender_entered_dtl = research_defender_resp_dtl['input']
                                        research_defender_score_dtl = research_defender_resp_dtl['score']

                                        try:
                                            research_defender_resp_obj = ResearchDefenderResponseDetail.objects.create(
                                                research_defender = resp_research_defender_obj,
                                                entered_text = research_defender_entered_dtl['text'],
                                                entered_q_id = research_defender_entered_dtl['q_id'],
                                                entered_similarity_text_length = research_defender_entered_dtl['similarity_text_length'],
                                                language_detected = research_defender_score_dtl['language_detected'],
                                                pasted_response = research_defender_score_dtl['pasted_response'],
                                                typed_response_time = research_defender_score_dtl['typed_response_time'],
                                                page_view_time = research_defender_score_dtl['page_view_time'],
                                                garbage_words_score = research_defender_score_dtl['garbage_words_score'],
                                                similarity_text = research_defender_score_dtl['similarity_text'],
                                                garbage_words = research_defender_score_dtl['garbage_words'],
                                                language_detected_score = research_defender_score_dtl['language_detected_score'],
                                                profanity_check_score = research_defender_score_dtl['profanity_check_score'],
                                                pasted_response_score = research_defender_score_dtl['pasted_response_score'],
                                                profanity_check = research_defender_score_dtl['profanity_check'],
                                                engagement_score = research_defender_score_dtl['engagement_score'],
                                                composite_score = research_defender_score_dtl['composite_score']
                                            )
                                            try:
                                                research_defender_resp_obj.entered_sn_ud = research_defender_entered_dtl['sn_ud']
                                            except Exception as error:
                                                surveyentry_log(f'{error}Exception number ------125 raised',project_group_number)
                                            try:
                                                research_defender_resp_obj.entered_sy_nr = research_defender_entered_dtl['sy_nr']
                                            except Exception as error:
                                                surveyentry_log(f'{error}Exception number ------126 raised',project_group_number)

                                            research_defender_resp_obj.save(force_update=True)
                                            if research_defender_resp_obj.composite_score > 90:
                                                research_defender_fail = True
                                                research_defender_fail_message = 'Composite Score > 90'
                                            if research_defender_resp_obj.profanity_check_score > 0.9:
                                                research_defender_fail_message+=' & Profanity Score > 0.9' if research_defender_fail == True else 'Profanity Score > 0.9'
                                                research_defender_fail = True 
                                            if research_defender_resp_obj.language_detected == 'Unknown':
                                                research_defender_fail_message+= ' & Language Detected is Unknown' if research_defender_fail == True else 'Language Detected is Unknown'
                                                research_defender_fail = True
                                                
                                        except Exception as error:
                                            surveyentry_log(f'{error}Exception number ------127 raised',project_group_number)
                                            research_defender_fail = True
                                            research_defender_fail_message = error.__str__()
                            except Exception as error:
                                surveyentry_log(f'{error}Exception number ------128 raised',project_group_number)
                                research_defender_fail = True
                                research_defender_fail_message = error.__str__()
                        
                        # ========= Research Defender End ================
                    else:
                        if question_obj.parent_question.parent_question_number != 'Zip' and len(entered_value) == 0:
                            sc_op = True
                            question_data.delete()

                        if question_obj.parent_question.parent_question_number != 'Zip' and len(entered_value) > 0 and len(entered_value) <= 9:
                            sc_op = True
                            question_data.delete()

                except Exception as error:
                    surveyentry_log(f'{error}Exception number ------129 raised',project_group_number)
                    return False

            if(sc_op) and not quota_check:
                resp_obj.end_time = timezone.now()
                resp_obj.resp_status = "2"
                if resp_obj.final_detailed_reason in ('',None):
                    resp_obj.final_detailed_reason = "Question: " + str(question_obj.parent_question.parent_question_number)
                resp_obj.save()
                terminate_respondent = True

            if text_evaluation:
                resp_obj.end_time = timezone.now()
                resp_obj.resp_status = "2"
                if resp_obj.final_detailed_reason in ('',None):
                    resp_obj.final_detailed_reason = "OE Threshold Failed at " + str(question_obj.parent_question.parent_question_number)
                resp_obj.save()
                terminate_respondent = True

            if research_defender_fail:
                resp_obj.end_time = timezone.now()
                resp_obj.resp_status = "2"
                if resp_obj.final_detailed_reason in ('',None):
                    resp_obj.final_detailed_reason = research_defender_fail_message + ' ' + str(question_obj.parent_question.parent_question_number)
                resp_obj.save()
                terminate_respondent = True
            if terminate_respondent:
                return False
            else:
                if len(question_store)>0:
                    question_list_store.append(question_store)
                return True      
        

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            yield_results = executor.map(parellel_threading_func, question_answer_list)

        results_list = list(yield_results)

        if all(results_list) == True or project_group.project.project_customer.customer_url_code in ['toluna','zamplia']:
            RespondentDetailTolunaFields.objects.update_or_create(respondent = resp_obj, defaults={'user_prescreener_response': question_list_store})
            return Response(data={'status':'1'})

        return Response(data={'status':'2'})

class SurveyPrescreenerAPIView3(APIView):

    def get(self,request,url_string):
        try:
            language_agreement_question_list = json.load(open('InitialSetup/LanguageAgreementQuestion.json',encoding="utf8"))

            resp_obj = RespondentDetail.objects.select_related('respondentdetailsrelationalfield').get(respondenturldetail__url_safe_string=url_string)
            if resp_obj.respondentdetailsrelationalfield.project_group.project_group_language.language_code != 'en':
                language_agreement_question = language_agreement_question_list.pop(resp_obj.respondentdetailsrelationalfield.project_group.project_group_language.language_code)

                random_key1, random_value2 = random.choice(list(language_agreement_question_list.items()))
                random_key3, random_value4 = random.choice(list(language_agreement_question_list.items()))

                questiondict = {
                    'status':'1',
                    "question" : language_agreement_question['question'],
                    "answer" : {
                        1 : "Yes, I know the language and agree to participate",
                        2 : random_value2['answer'],
                        3 : random_value4['answer'],
                        4 : language_agreement_question['answer']
                    }
                }
                return Response(questiondict, status=status.HTTP_200_OK)
            else:
                return Response({'status':'2'},status=status.HTTP_200_OK)
        except:
            return Response({'status':'2'},status=status.HTTP_200_OK)
    
    def post(self,request,url_string):
        try:
            answer_data = request.data['answerid']
            if answer_data != '4':
                resp_obj = RespondentDetail.objects.select_related('respondentdetailsrelationalfield').get(respondenturldetail__url_safe_string=url_string)
                resp_obj.resp_status = '2'
                resp_obj.final_detailed_reason = 'Language Agreement Terminate'
                resp_obj.save()
                return Response(data={'status':'2'})
            else:
                return Response(data={'status':'1'})
        except:
            return Response(data={'status':'2'})
    
class SurveyFinalizedAPI(APIView):
    
    def get(self, request, url_string):

        internalterminate_url = settings.SURVEY_URL + "landingpage?stv=2"
        
        try:
            # if True:
            resp_obj = RespondentDetail.objects.get(respondenturldetail__url_safe_string=url_string)
            resp_page_details = RespondentPageDetails.objects.get(respondent=resp_obj)
            resp_page_details.last_page_seen = 'Supplier Redirect Page'
            resp_page_details.save()
            
            if request.GET.get('terminate_resp') == 'true':    
                if int(resp_obj.source) > 0:
                    redirect_to_supplier_side = "/survey/pre/supplierredirect/"+str(url_string)
                    # Redirect to Supplier Redirect URL | 'url':redirect_to_supplier_side
                    return Response(data={'status':resp_obj.resp_status}) # Status = 2
                else:
                    # Redirect to Internally Terminate URL | 'url':internalterminate_url
                    return Response(data={'status':resp_obj.resp_status}) # Status = 2
            else:
                project_group_number = resp_obj.project_group_number
                project_group = ProjectGroup.objects.get(project_group_number = project_group_number)

                already_answer_question = ProjectGroupPrescreenerDataStore.objects.filter(respondent = resp_obj).values('translated_question_id')
                prescreener_to_show = ProjectGroupPrescreener.objects.filter(project_group_id__id = project_group.id,is_enable = True).exclude(translated_question_id__in = already_answer_question)

                if prescreener_to_show.count()==0:
                    # Redirect to the Client Side, all questions correctly answered | URL - /survey-api/pre/clientredirect/{url_string}
                    return Response(data={'status':resp_obj.resp_status}) # Status = 1
                else:
                    ProjectGroupPrescreenerDataStore.objects.filter(respondent = resp_obj).delete()
                    # Redirect to the Prescreener Page, as not answered all the questions | URL - /survey-api/pre/{url_string}
                    return Response(data={'showagain':'yes'}) # 5 => Prescreener Page Again, as not answered all the questions
        except Exception as error:
            surveyentry_log(f'{error}Exception number ------130 raised',url_string)
            # Redirect to Internally Terminate URL | 'url':internalterminate_url
            return Response(data={'status':'2'}) # Status = 2



class SupplierTerminateRedirectAPIView(APIView):
    
    def get(self, request, url_string):
        redirect_to_url = ""
        reroute = request.GET.get('reroute','No')
        if reroute == 'Yes':
            messages.error(request, 'This question is required..!')
        resp_obj = RespondentDetail.objects.get(respondenturldetail__url_safe_string = url_string)
        resp_obj.respondentpagedetails.last_page_seen = 'Routing Confirmation Page'
        resp_obj.respondentpagedetails.save()
        if resp_obj.respondentdetailsrelationalfield.source.supplierapiadditionalfield.enable_routing:
            return Response(data={'status':'Redirect to Routing Confirmation HTML page'})
        else:
            redirect_to_url = "/survey/pre/suppliersideredirect/"+str(url_string)
            return Response(data={'url':redirect_to_url})

    
    def post(self, request, url_string):
        try:
            data = request.POST
            if data['routingconfirmation'] == 'yes':
                redirect_to_url = '/routingtraffic/'+str(url_string)
            else:
                redirect_to_url = "/survey/pre/suppliersideredirect/"+str(url_string)
            return Response(data={'url':redirect_to_url})
        except Exception as error:
            surveyentry_log(f'{error}Exception number ------131 raised',url_string)
            redirect_to_url = "/survey/pre/supplierredirect/"+str(url_string)+"?reroute=Yes"
            return Response(data={'url':redirect_to_url})




class SupplierSideTerminateRedirectAPIView(APIView):
    
    def get(self,request, url_string):
        
        try:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')

            resp_obj = RespondentDetail.objects.select_related('respondenturldetail','respondentsupplierdetail').get(respondenturldetail__url_safe_string = url_string)
            resp_page_details = RespondentPageDetails.objects.get(respondent=resp_obj)
            url = f'https://opinionsdeal.com?s=InternalTerminate'
            if int(resp_obj.source) ==0:
                url = f'{url}&PID={resp_obj.respondenturldetail.pid}'
                return Response(data={'redirect_url':url},status=status.HTTP_200_OK)
            resp_obj.respondentpagedetails.last_page_seen = 'Supplier Side Terminate'
            resp_obj.respondentpagedetails.save()

            # ***** End Ip Address Store *****
            resp_obj.respondenturldetail.end_ip_address = ip
            resp_obj.respondenturldetail.save()

            source = resp_obj.source
            resp_status = resp_obj.resp_status
            hashing_status = 'x'
            if resp_status == '4':
                url = resp_obj.respondentsupplierdetail.supplier_complete_url if resp_obj.respondentdetailsrelationalfield.project_group_supplier.supplier_org.supplier_type != '5' else resp_obj.respondentprojectgroupsubsupplier.sub_supplier_complete_url
                hashing_status = 'c'
            if resp_status == '5':
                url = resp_obj.respondentsupplierdetail.supplier_terminate_url if resp_obj.respondentdetailsrelationalfield.project_group_supplier.supplier_org.supplier_type != '5' else resp_obj.respondentprojectgroupsubsupplier.sub_supplier_terminate_url
                hashing_status = 's'
            if resp_status == '2':
                url = resp_obj.respondentsupplierdetail.supplier_internal_terminate_redirect_url if resp_obj.respondentdetailsrelationalfield.project_group_supplier.supplier_org.supplier_type != '5' else resp_obj.respondentprojectgroupsubsupplier.sub_supplier_internal_terminate_redirect_url
                hashing_status = 'x'
            if resp_status == '6':
                url = resp_obj.respondentsupplierdetail.supplier_quotafull_url if resp_obj.respondentdetailsrelationalfield.project_group_supplier.supplier_org.supplier_type != '5' else resp_obj.respondentprojectgroupsubsupplier.sub_supplier_quotafull_url
                hashing_status = 'q'
            if resp_status == '7':
                url = resp_obj.respondentsupplierdetail.supplier_securityterminate_url if resp_obj.respondentdetailsrelationalfield.project_group_supplier.supplier_org.supplier_type != '5' else resp_obj.respondentprojectgroupsubsupplier.sub_supplier_securityterminate_url
                hashing_status = 'x'
            
            pid = resp_obj.respondenturldetail.pid
            userid = resp_obj.respondenturldetail.userid
            glsid = resp_obj.project_number
            if url in ['', None]:
                url = f"{settings.OPINIONSDEALSNEW_FRONTEND_URL}dashboards?is_popup={1}&status={resp_status}&PID=%%PID%%"
                # url = f"https://opinionsdeal.com/surveyrouterlandingpage?is_popup={1}&status={resp_status}&PID=%%PID%%"

            redirect_to_url = url.replace("%%PID%%",pid)
            redirect_to_url = redirect_to_url.replace("%%glsid%%",glsid)
            redirect_to_url = redirect_to_url.replace("%%SUPCPI%%", str(resp_obj.supplier_cpi))
            redirect_to_url = redirect_to_url.replace("%%PROJID%%",glsid)
            if userid:
                redirect_to_url = redirect_to_url.replace("%%USERID%%",userid)

            # try:
            #     supplier_request_url = resp_obj.respondentdetailsrelationalfield.source.supplier_buyer_apid.request_api_url
            #     supplier_url_code = resp_obj.respondentdetailsrelationalfield.source.supplier_url_code

            #     # Mark user status on OfferWall
            #     if supplier_url_code in ["offerwall", "Oferwall"]:
            #         offerwall_url = f"{supplier_request_url}supplier/visitor-status-store?"
            #         offerwall_url_params = f"resp_token={resp_obj.respondenturldetail.pid}&resp_status={resp_obj.resp_status}"
            #         # Hash the offerwall url_params
            #         secret_key = 'g8FxNtNoYnmEi1FX9vubfSTnyvGUHq'
            #         redirect_to_encode = offerwall_url_params+secret_key
            #         offerall_encode_url = hashlib.sha1(redirect_to_encode.encode()).hexdigest()
            #         offerwall_url_with_params = f"{offerwall_url}{offerwall_url_params}&hkey={offerall_encode_url}"
            #         offerwall_req = callOfferWallApi(offerwall_url_with_params, req_method="post")
            # except Exception as error:
                # surveyentry_log(f'{error}Exception number ------132 raised')
            #     pass

            if resp_obj.respondentdetailsrelationalfield.source.supplier_type == '4':
                if resp_obj.resp_status == '2':
                    final_status = 2
                    survey_no = resp_obj.project_group_number
                    hash_key_params = f'resp_token={resp_obj.respondenturldetail.pid}&resp_status={final_status}'

                    secret_key = 'PSfX8aW2VezKXmfmJpZ7xTaUg3BWfwPQ'
                    hash_key = hash_key_params + secret_key
                    hash_key = hashlib.sha1(hash_key.encode()).hexdigest()
                    opinions_deal_url = callOpinionsDealApi(api_url=settings.OPINIONSDEALSNEW_BASE_URL + f'panel/survey/status-store?{hash_key_params}&hkey={hash_key}&survey_no={survey_no}', req_method="post")

                    # return opinions_deal_url
                
            if int(source) == 83 or (int(source)==42 and settings.SERVER_TYPE == 'staging'):
                # For Purespectrum
                secret_key = 'sguRZm9jMPWkgW4D5xmB4KtJkx6gpZpRv3'
                redirect_to_encode = redirect_to_url+secret_key
                encode_url = hashlib.sha1(redirect_to_encode.encode()).hexdigest()
                resp_obj.respondentsupplierdetail.hash_value = encode_url
                resp_obj.respondentsupplierdetail.save()
                redirect_to_url = redirect_to_url+"&encid="+encode_url
            
            elif (int(source)==95):
                secret_key = 'Zy1cXNLWo2MrVKkNG5HK789MDNm243Me'
                values_to_be_hashed = f"{secret_key}{glsid}{pid}"
                encoded_values = values_to_be_hashed.encode()
                finalresult = hashlib.md5(encoded_values)
                redirect_to_url = redirect_to_url.replace("%%hashkey%%",finalresult.hexdigest())

            elif int(source) == 104 or (int(source) == 33 and settings.SERVER_TYPE == "staging"):
                # For WJSurvey
                secret_key = 'SBy0GxAS4CbqqvnWOtW6KTks6VMvKTaX'
                signature = f"{pid}{hashing_status}{secret_key}"
                hashed_value = hashlib.md5(signature.encode('utf-8')).hexdigest()
                resp_obj.respondentsupplierdetail.hash_value = hashed_value
                resp_obj.respondentsupplierdetail.save()
                redirect_to_url = redirect_to_url.replace("%%hashkey%%",hashed_value)
                redirect_to_url = redirect_to_url.replace("%%statuscode%%",hashing_status)
            
            elif int(source) == 106:
                # For OpinionKiss
                sup_obj = SupplierAPIAdditionalfield.objects.get(supplier__id = source)
                secret_key = sup_obj.hash_security_key
                signature = f"{pid}{hashing_status}{secret_key}"
                hashed_value = hashlib.md5(signature.encode('utf-8')).hexdigest()
                resp_obj.respondentsupplierdetail.hash_value = hashed_value
                resp_obj.respondentsupplierdetail.save()
                redirect_to_url = redirect_to_url.replace("%%hashkey%%",hashed_value)
                redirect_to_url = redirect_to_url.replace("%%statuscode%%",hashing_status)
            
            elif (int(source) == 11) or (int(source) == 18) or (int(source) == 40 and (settings.SERVER_TYPE == 'staging')) or (int(source) == 96 and (settings.SERVER_TYPE == 'production')):
                sup_obj = SupplierAPIAdditionalfield.objects.get(supplier__id = source)
                #Fulcrum = 11 and hashvar = ienc2
                #TC Task 18 and hashvar = hash
                key = sup_obj.hash_security_key
                URL = redirect_to_url+"&"
                encoded_key = key.encode('utf-8')
                encoded_URL = URL.encode('utf-8')
                final_result = hmac_sha1_encoding(encoded_key, encoded_URL)
                resp_obj.respondentsupplierdetail.hash_value = final_result
                resp_obj.respondentsupplierdetail.save()
                redirect_to_url = f"{redirect_to_url}&{sup_obj.hash_variable_name}={final_result}"
            
            # elif resp_obj.respondentdetailsrelationalfield.source.supplier_url_code in ['disqo', 'Disqo']:
            elif int(source) == 84:
                #For Disqo
                # key = settings.DISQO_HASH_KEY
                key = SupplierOrgAuthKeyDetails.objects.get(supplierOrg__id=84).secret_key
                
                disqo_status = {"2":8,"4":1,"5":3,"6":2,"7":4}

                d_status = disqo_status[resp_status]

                URL = f'status={d_status}&clientId={resp_obj.disqoqueryparam.clientId}&projectId={resp_obj.disqoqueryparam.projectId}&quotaIds={resp_obj.disqoqueryparam.quotaIds}&supplierId={resp_obj.disqoqueryparam.supplierId}&tid={resp_obj.disqoqueryparam.tid}&pid={resp_obj.disqoqueryparam.pid}'

                encoded_key = key.encode('utf-8')
                encoded_URL = URL.encode('utf-8')
                hashed = hmac.new(encoded_key, msg=encoded_URL, digestmod=hashlib.sha1)
                digested_hash = hashed.digest()
                base64_encoded_result = base64.b64encode(digested_hash)
                final_result = base64_encoded_result.decode('utf-8') .replace('+', '-').replace('/', '_').replace('=', '')
                resp_obj.respondentsupplierdetail.hash_value = final_result
                resp_obj.respondentsupplierdetail.save()
                if "?" in redirect_to_url:
                    redirect_to_url = redirect_to_url+"&"+URL+"&auth="+final_result
                else:
                    redirect_to_url = redirect_to_url+"?"+URL+"&auth="+final_result
        except Exception as error:
            surveyentry_log(f'{error}Exception number ------133 raised',url_string)
            redirect_to_url = f'https://router.panelviewpoint.com/?sc=d7356887e29ae4ac&ruid={url_string}'
            return Response(data={'redirect_url':redirect_to_url},status=status.HTTP_200_OK)


        # SUPPLIER POSTBACK URL PROVIDED BY THE SUPPLIER TO HIT AND RECEIVE THE POSTBACK TEXT RESPONSE
        if resp_status == '4':
            supplier_postback_url = resp_obj.respondentsupplierdetail.supplier_postback_url
            if supplier_postback_url not in ('',None,""):
                if re.search('^http|^https', supplier_postback_url):
                    supplier_postback_url = supplier_postback_url.replace("%%PID%%", pid)
                    supplier_postback_url = supplier_postback_url.replace("%%PROJID%%",glsid)
                    supplier_postback_url = supplier_postback_url.replace("%%SUPCPI%%",str(resp_obj.supplier_cpi))
                    if userid:
                        supplier_postback_url = supplier_postback_url.replace("%%USERID%%",userid)

                    # ADD EXTRA URL PARAMS FROM THE ROUTER TRAFFIC URL
                    # supplier_postback_url = supplier_postback_url + f'&{resp_obj.respondentpagedetails.url_extra_params}'
                    supplier_postback_url = supplier_postback_url
                    resp_page_details.postbackurl_link = supplier_postback_url
                    resp_page_details.save()

                    sup_postbak_response = requests.post(supplier_postback_url)
                    resp_obj.respondentsupplierdetail.supplier_postback_url_response = sup_postbak_response.text
                    resp_obj.respondentsupplierdetail.save()
                    # postbackstatus = 'True&redirecttourl='+redirect_to_url
                # return redirect(redirect_to_url) +"?postbackstatus="+postbackstatus
        is_routing = False
        routing_redirect_url = redirect_to_url

        # if resp_obj.respondentdetailsrelationalfield.project.project_customer.customer_url_code == "lucid-redirect":
        #     redirect_to_url = 'https://www.opinionsdeal.com/?utm_source=lucidcompleterouting'
        #     # if resp_obj.final_detailed_reason == "GEOIP":
        #     #     redirect_to_url = "https://opinionsdeal.com/?utm_source=GEOIP"
        #     # else:
        #     #     redirect_to_url = resp_obj.respondentdetailsrelationalfield.project_group_supplier.supplier_survey_url.replace("XXXXX", resp_obj.respondenturldetail.pid) + "&sfc=false"
        #     #     redirect_to_url = redirect_to_url.replace("%%PID%%", resp_obj.respondenturldetail.pid)

        #     is_routing = True
        resp_page_details.suppliersideredirect_link = routing_redirect_url
        resp_page_details.save()
        return Response(data={'redirect_url':redirect_to_url,'is_routing':is_routing,'routing_redirect_url':routing_redirect_url},status=status.HTTP_200_OK)


class ClientRedirectAPIView(APIView):
    
    def get(self, request, url_string):
        
        """
        Return the URL redirect to. Keyword arguments from the URL pattern
        match generating the redirect request are provided as kwargs to this
        method.
        """
        internalterminate_url = settings.SURVEY_URL + "landingpage?stv=2"
        redirect_url = ''
        try:
            resp_obj = RespondentDetail.objects.select_related('respondentdetailsrelationalfield','respondenturldetail', 'respondentpagedetails').get(respondenturldetail__url_safe_string=url_string)
            RID = resp_obj.respondenturldetail.RID
            resp_obj.respondentpagedetails.last_page_seen = 'Client Side Redirect View'
            resp_obj.respondentpagedetails.save()
        except Exception as error:
            surveyentry_log(f'{error}Exception number ------134 raised',url_string)
            return Response(data={'redirect_url':internalterminate_url,'client_side_url':internalterminate_url, 'status':'3'})
    
        try:
            respondent_status = True #will turn into False when respondent fails on any prescreener condition
            final_detailed_reason = ''
            project_group = resp_obj.respondentdetailsrelationalfield.project_group
            prescreener_question = ProjectGroupPrescreener.objects.only('allowedoptions','allowedRangeMin','allowedRangeMax').filter(project_group_id = project_group,is_enable = True)
            for prescreener_obj in prescreener_question:
                question_data = ProjectGroupPrescreenerDataStore.objects.select_related('translated_question_id__parent_question').prefetch_related('selected_options').get(respondent = resp_obj, translated_question_id = prescreener_obj.translated_question_id)
                sc_op = True
                final_detailed_reason = ""
                if question_data.translated_question_id.parent_question.parent_question_type in ['MS', 'SS','CTZIP']:
                    answer_options = question_data.selected_options.all().values_list('id', flat=True)
                    if prescreener_obj.allowedoptions.filter(id__in=list(answer_options)).count() > 0:
                        sc_op = False
                if question_data.translated_question_id.parent_question.parent_question_type == 'FU' and question_data.answer_file not in ['',None]:
                    sc_op = False
                if question_data.translated_question_id.parent_question.parent_question_type == 'NU':
                    try:
                        entered_value = int(question_data.calculated_response)
                        allowedRangeMin = prescreener_obj.allowedRangeMin.split(",")
                        allowedRangeMax = prescreener_obj.allowedRangeMax.split(",")
                        for index,value in enumerate(allowedRangeMin):
                            if int(entered_value)>=int(allowedRangeMin[index]) and int(entered_value)<=int(allowedRangeMax[index]):
                                sc_op = False
                    except Exception as error:
                        surveyentry_log(f'{error}Exception number ------135 raised',url_string)
                        pass  
                if question_data.translated_question_id.parent_question.parent_question_type == 'OE':
                    if question_data.translated_question_id.parent_question.parent_question_number == 'Zip':
                        try:
                            entered_value = question_data.received_response
                            zipexist = ZipCode.objects.filter(zip_code = str(int(entered_value)), project_group_id__project_group_number = resp_obj.project_group_number).exists()
                            if zipexist:
                                sc_op = False
                        except Exception as error:
                            surveyentry_log(f'{error}Exception number ------136 raised',url_string)
                            pass
                    else:
                        sc_op = False
                
                if question_data.translated_question_id.parent_question.parent_question_type == 'ZIP':
                    entered_value = question_data.received_response
                    zipexist = int(entered_value) in list(map(int,prescreener_obj.allowed_zipcode_list))
                    if not zipexist and prescreener_obj.allowed_zipcode_list != []:
                        sc_op = True
                    else:
                        sc_op = False

                if sc_op:
                    respondent_status = False
                    final_detailed_reason = f"Question: {question_data.translated_question_id.parent_question.parent_question_number}"
                    break
                
            if respondent_status: 
                if project_group.project_group_client_url_type in ["1", "3"]:
                    redirect_url = resp_obj.respondentprojectdetail.clientURL
                else:
                    multiple_url_obj = MultipleURL.objects.filter(project_group=project_group, is_used = False).first()
                    try:
                        multiple_url_obj.is_used = True
                        multiple_url_obj.save() 
                        RID = multiple_url_obj.client_url_id
                        resp_obj.respondenturldetail.RID = RID
                        resp_obj.respondenturldetail.save()
                        redirect_url = multiple_url_obj.client_url
                    except Exception as error:
                        surveyentry_log(f'{error}Exception number ------137 raised',url_string)
                        respondent_status = False
                        final_detailed_reason = "Multiple URL not available"

            if not(respondent_status):
                #In case respondent is terminated
                resp_obj.end_time = timezone.now()
                resp_obj.resp_status = 2
                resp_obj.final_detailed_reason = final_detailed_reason
                
                if int(resp_obj.source)>0:
                    redirect_url = resp_obj.respondentsupplierdetail.supplier_terminate_url
                else:
                    redirect_url = internalterminate_url
            else:
                resp_obj.resp_status = 3
                resp_obj.save()

            if resp_obj.respondentdetailsrelationalfield.project.project_customer.customer_url_code == "toluna" and resp_obj.resp_status == 3:
                return Response(data={'status':'31'}, status=status.HTTP_202_ACCEPTED)
            elif resp_obj.respondentdetailsrelationalfield.project.project_customer.customer_url_code == "zamplia" and resp_obj.resp_status == 3:
                return Response(data={'status':'32'}, status=status.HTTP_202_ACCEPTED)
            elif resp_obj.respondentdetailsrelationalfield.project.project_customer.customer_url_code == "lucid-redirect" and resp_obj.resp_status == 3:
                try:
                    cos = resp_obj.respondentdetailsrelationalfield.project_group_supplier.cpi*2
                    loi = resp_obj.respondentdetailsrelationalfield.project_group.project_group_loi
                    resp_obj.respondentsupplierdetail.supplier_lucid_min_cpi = cos
                    resp_obj.respondentsupplierdetail.save()
                except Exception as error:
                    surveyentry_log(f'{error}Exception number ------138 raised',url_string)
                    cos = 0.5
                    loi = resp_obj.respondentdetailsrelationalfield.project_group.project_group_loi

                credential_data = get_credential_details()
                try:
                    country_language = LucidCountryLanguageMapping.objects.only('lucid_country_lang_id').get(country_id = resp_obj.respondentdetailsrelationalfield.project_group.project_group_country.id,lanugage_id=resp_obj.respondentdetailsrelationalfield.project_group.project_group_language.id).lucid_country_lang_id
                except Exception as error:
                    surveyentry_log(f'{error}Exception number ------139 raised',url_string)
                    country_language = 9

                supplier_id = credential_data['supplier_id']
                baseurl = credential_data['baseurl']
                redirected_survey_url = f'{baseurl}/s/default.aspx?sid={supplier_id}&pid=p{RID}&clid={country_language}&maid={resp_obj.project_group_number}&mid={RID}&cos={cos}&loi={loi}'
                hashing_key = credential_data['hashing_key']
                URL = redirected_survey_url+"&"
                encoded_key = hashing_key.encode('utf-8')
                encoded_URL = URL.encode('utf-8')
                hashed = hmac.new(encoded_key, msg=encoded_URL, digestmod=hashlib.sha1)
                digested_hash = hashed.digest()
                base64_encoded_result = base64.b64encode(digested_hash)
                final_result = base64_encoded_result.decode('utf-8').replace('+', '-').replace('/', '_').replace('=', '')
                redirected_survey_url = f'{redirected_survey_url}&hash={final_result}'
                resp_obj.resp_status = 3
                resp_obj.end_time = timezone.now()
                resp_obj.save()
                resp_obj.respondentpagedetails.clientredirect_link = redirected_survey_url
                resp_obj.respondentpagedetails.last_page_seen = f'Redirected to {redirected_survey_url}'
                resp_obj.respondentpagedetails.save()
                return Response(data={'redirect_url':redirected_survey_url,'client_side_url':redirected_survey_url, 'status':'3'})
            else:
                redirect_url = redirect_url.replace("%%RID%%",RID)
                redirect_url = redirect_url.replace("%%MUID%%",RID)
                redirect_url = redirect_url.replace('%%PID%%',resp_obj.respondenturldetail.pid)
                redirect_url = redirect_url.replace('%%PROJID%%',resp_obj.project_number)
                redirect_url = redirect_url.replace("%E2%80%8B","")
                resp_obj.end_time = timezone.now()
                resp_obj.save()
                resp_obj.respondentpagedetails.clientredirect_link = redirect_url
                resp_obj.respondentpagedetails.last_page_seen = f'Redirected to {redirect_url}'
                resp_obj.respondentpagedetails.save()
                return Response(data={'redirect_url':redirect_url,'client_side_url':redirect_url, 'status':'3'})
        except Exception as error:
            surveyentry_log(f'{error}Exception number ------140 raised',url_string)
            resp_obj.end_time = timezone.now()
            resp_obj.resp_status = 2
            resp_obj.final_detailed_reason = "Exception raised."
            resp_obj.save()
            resp_obj.respondentpagedetails.clientredirect_link = redirect_url
            resp_obj.respondentpagedetails.last_page_seen = f'Exception raised--- {error}'
            resp_obj.respondentpagedetails.save()
            return Response(data={'redirect_url':internalterminate_url,'client_side_url':internalterminate_url, 'status':'2'})

# Toluna API Specific Views. Used only for Toluna API Integration
class validateQuotaEligibilityAPI(APIView):
    # https://docs.integratedpanel.toluna.com/externalsample/samplingrules.html
    # Should Qualify for atleast one quota

    """
    These rules can be consolidated into simple boolean conditions:

    Quotas are “OR” conditions
    Layers are “AND” conditions
    SubQuotas are “OR” conditions
    AnswerIDs are “OR” conditions
    Within a SubQuota
    “OR” for the same QuestionID
    “AND” for multiple QuestionIDs

    """
    def get(self, request, url_string):
        # IF RESPONDENT ALREADY COMES WITH THE SURVEY AND SUPPLIER
        respondentdetail_obj = RespondentDetail.objects.get(respondenturldetail__url_safe_string = url_string)
        answered_questions = ProjectGroupPrescreenerDataStore.objects.filter(respondent=respondentdetail_obj)

        clientquota_obj = ClientQuota.objects.filter(project_group__project_group_number=respondentdetail_obj.project_group_number)
        qualified_quota = []
        for quota in clientquota_obj:
            qualified_layer = []
            clientlayer_obj = ClientLayer.objects.filter(client_quota = quota)
            for layer in clientlayer_obj:
                qualified_subquota = []
                subquota_obj = ClientSubQuota.objects.filter(client_layer = layer)
                for subquota in subquota_obj:
                    skip_subquota_loop = False
                    qualify_for_questions = []
                    client_survey_question_obj = ClientSurveyPrescreenerQuestions.objects.filter(client_subquota = subquota)
                    for question in client_survey_question_obj:
                        # Check if Subquota questions and answer matches with the user responses.
                        if question.client_question_mapping.parent_question_type == 'NU':
                            allowedRangeMin = question.allowedRangeMin.split(",")
                            allowedRangeMax = question.allowedRangeMax.split(",")
                            age_in_years = answered_questions.get(translated_question_id = question.client_question_mapping).calculated_response
                            for index,value in enumerate(allowedRangeMin):
                                if int(age_in_years)>=int(allowedRangeMin[index]) and int(age_in_years)<=int(allowedRangeMax[index]):
                                    qualify_for_questions.append(question.id)
                        elif question.client_question_mapping.parent_question_type == 'ZIP':
                            zipexist = str(answered_questions.get(translated_question_id = question.client_question_mapping).received_response) in list(answered_questions.filter(translated_question_id__toluna_question_id ='1001042').values_list('prescreener_question__allowed_zipcode_list',flat = True))[0]
                            if zipexist:
                                qualify_for_questions.append(question.id)
                        else:
                            answered_questions_obj = answered_questions.filter(translated_question_id = question.client_question_mapping, selected_options__in = question.client_answer_mappings.all())
                            if answered_questions_obj.exists():
                                qualify_for_questions.append(question.id)
                    
                    # Check the qualification for Subquota and Layer. 
                    if client_survey_question_obj.count() == len(qualify_for_questions):
                        qualified_subquota.append(subquota.subquota_id)
                        qualified_layer.append(layer.layer_id)
                        break
                    
            if clientlayer_obj.count() == len(qualified_layer):
                qualified_quota.append(quota.quota_id)
                RespondentDetailTolunaFields.objects.update_or_create(respondent=respondentdetail_obj, defaults = {"qualified_quota" : qualified_quota[0], "redirected_survey_quota_id":qualified_quota[0]})
                break
        if(len(qualified_quota)==0):
            return Response({'status':'2'}, status=status.HTTP_200_OK)
        return Response({'status':'31', 'qualified_Quota':quota.quota_id}, status=status.HTTP_200_OK)

class fetchURLAPI(APIView):
    def get(self, request, url_string):
        try:
            respondentdetail_obj = RespondentDetail.objects.get(respondenturldetail__url_safe_string = url_string)
        except Exception as error:
            surveyentry_log(f'{error}Exception number ------141 raised',url_string)
            return Response(data={'message':'Invalid Url', 'status':'2'}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)
        
        # Toluna Specific Code        
        if request.GET.get('survey') == "31":
            member_code = respondentdetail_obj.respondenturldetail.RID
            selected_quota_obj = respondentdetail_obj.survey_entry_toluna_field.qualified_quota
            PartnerGUID = respondentdetail_obj.respondentdetailsrelationalfield.project_group.project_group_encodedR_value
            user_provided_response = respondentdetail_obj.survey_entry_toluna_field.user_prescreener_response

            if settings.SERVER_TYPE == 'localhost':
                is_test = True
            elif settings.SERVER_TYPE == 'staging':
                is_test = True
            else:
                is_test = False

            date_of_birth_data = ProjectGroupPrescreenerDataStore.objects.filter(respondent = respondentdetail_obj, translated_question_id__parent_question__toluna_question_id = '1001538').first().received_response
            PostalCode = ProjectGroupPrescreenerDataStore.objects.filter(respondent = respondentdetail_obj, translated_question_id__parent_question_type = 'ZIP').first().received_response
            PostalCode = PostalCode if len(PostalCode) == 5 else "" # need to change when we use multiple Country now it for only US
            data_payload = json.dumps({
                "PartnerGUID": PartnerGUID,
                "MemberCode": member_code,
                "IsActive": True,
                "IsTest": is_test,
                "BirthDate": date_of_birth_data,
                "PostalCode": PostalCode,
                "IsPIIDataRegulated": False,
                "AnsweredQuestions": list(filter(lambda d: 'AnswerID' in d, user_provided_response))
            })

            # Add member at Toluna End
            response = requests.post(settings.TOLUNA_CLIENT_MEMBER_ADD_URL + f'/IntegratedPanelService/api/Respondent/', headers={'Accept':'application/json;version=2.0', 'Content-Type':'application/json'}, verify=False, data=data_payload)
            if response.status_code not in (200,201):
                respondentdetail_obj.resp_status='2'
                respondentdetail_obj.final_detailed_reason=f'Not registered at Toluna End - {response.text}'
                respondentdetail_obj.save()
                return Response({'status':'2', 'visitor_uid':url_string},status=status.HTTP_200_OK)

            # Generate Invite
            generate_survey_url = settings.TOLUNA_CLIENT_MEMBER_ADD_URL + f'/IPExternalSamplingService/ExternalSample/{PartnerGUID}/{member_code}/Invite/{selected_quota_obj}'

            # response3 = requests.get(generate_survey_url, headers={'API_AUTH_KEY':'97C3119F-8DDF-4D79-BFA0-04B60D5BA62B'}, verify=False)
            response3 = requests.get(generate_survey_url, headers={'API_AUTH_KEY':settings.TOLUNA_API_AUTH_KEY}, verify=False)
            if response3.status_code not in (200,201):
                respondentdetail_obj.resp_status='2'
                respondentdetail_obj.final_detailed_reason=f'Visitor Eligible but Survey URL Not generated due to {response3.text}'
                respondentdetail_obj.save()
                if response3.json()['ResultCode'] == 9:
                    client_quota_obj = ClientQuota.objects.filter(project_group__project_group_number=respondentdetail_obj.project_group_number)
                    if client_quota_obj.count() == 1:
                        project_group_obj = ProjectGroup.objects.filter(project_group_number = respondentdetail_obj.project_group_number)
                        ProjeGroupForceStop.objects.update_or_create(
                            project_group = project_group_obj.first(),
                            defaults={"current_status" : "Live"}
                        )
                        project_group_obj.update(project_group_status= 'Paused')
                        RountingPriority.objects.filter(project_group__project_group_number = respondentdetail_obj.project_group_number).delete()
                        ProjectGroupSupplier.objects.filter(project_group__in=project_group_obj).update(supplier_status = 'Paused')
                        ProjectGroupSubSupplier.objects.filter(project_group__project_group_number=respondentdetail_obj.project_group_number).update(
                            sub_supplier_status = 'Paused')
                    else:
                        client_quota_obj.filter(quota_id=selected_quota_obj).delete()
                return Response(data={'status':'2', 'visitor_uid':url_string}, status=status.HTTP_203_NON_AUTHORITATIVE_INFORMATION)

            resp_dict = response3.json()

            survey_url = resp_dict['URL']

            RespondentPageDetails.objects.filter(respondent=respondentdetail_obj).update(clientredirect_link=survey_url)

            respondentdetail_obj.resp_status='3'
            respondentdetail_obj.save()
            return Response(data={'client_side_url':survey_url,'status':'311'}, status=status.HTTP_200_OK)
        
        # Zamplia Specific Code
        if request.GET.get('survey') == "32":
            base_url = settings.STAGING_URL
            URL = f'{base_url}/Surveys/GenerateLink?SurveyId={respondentdetail_obj.respondentdetailsrelationalfield.project_group.client_survey_number}&IpAddress={respondentdetail_obj.respondenturldetail.ip_address}&TransactionId={respondentdetail_obj.respondenturldetail.RID}'
            headers = {
                'Accept' : 'application/json',
                'ZAMP-KEY' : settings.STAGING_KEY
            }
            redirected_survey_url_api_call = requests.get(URL, headers=headers).json()['result']
            if redirected_survey_url_api_call['success']:
                redirected_survey_url = redirected_survey_url_api_call['data'][0]['LiveLink']
                respondentdetail_obj.end_time = timezone.now()
                respondentdetail_obj.resp_status='3'
                respondentdetail_obj.save()
                respondentdetail_obj.respondentpagedetails.clientredirect_link = redirected_survey_url
                respondentdetail_obj.respondentpagedetails.last_page_seen = f'Redirected to {redirected_survey_url}'
                respondentdetail_obj.respondentpagedetails.save()
                return Response(data={'client_side_url':redirected_survey_url,'status':'311'})
            else:
                zamplia_response_code = redirected_survey_url_api_call['Code']
                respondentdetail_obj.resp_status='2'
                respondentdetail_obj.final_detailed_reason = zamplia_response_code
                respondentdetail_obj.save()
                update_status(respondentdetail_obj.respondentdetailsrelationalfield.project_group.id, "Paused", action='change-projectgroup-status')
                return Response(data={'status':'2'})
                




class TrafficRoutingAPIView(APIView):

    def get(self, request, url_safe_string):

        redirect_url = ''
        resp_obj = RespondentDetail.objects.get(respondenturldetail__url_safe_string = url_safe_string)
        pid = resp_obj.respondenturldetail.pid
        all_attempts = RespondentDetail.objects.filter(respondenturldetail__pid = pid).values_list('project_group_number', flat=True)
        if len(list(all_attempts)) < 5:
            language = resp_obj.respondentdetailsrelationalfield.project_group.project_group_language
            country = resp_obj.respondentdetailsrelationalfield.project_group.project_group_country
            base_supplier_cpi = resp_obj.respondentroutingdetail.base_supplier_cpi
            all_attempted_project_groups = list(all_attempts)

            if resp_obj.id % 2 == 0:
                priority_survey= '1'
            else:
                priority_survey= '2'

            prioritized_surveys = RountingPriority.objects.values('project_group__project_group_number')
            if  not prioritized_surveys.exists():
                priority_survey = '2'

            if priority_survey == '1':
                pgs_obj = ProjectGroupSupplier.objects.filter(project_group__project_group_number__in = prioritized_surveys,supplier_org__id = resp_obj.source, supplier_status = 'Live', cpi__gte =  base_supplier_cpi, project_group__project_group_country = country, project_group__project_group_language = language).exclude(project_group__project_group_number__in = all_attempted_project_groups)

                if not pgs_obj.exists():
                    priority_survey = '2'
            
            if priority_survey == '2':
                pgs_obj = ProjectGroupSupplier.objects.filter(supplier_org__id = resp_obj.source, supplier_status = 'Live', cpi__gte =  base_supplier_cpi, project_group__project_group_country = country, project_group__project_group_language = language).exclude(project_group__project_group_number__in = all_attempted_project_groups)

            if pgs_obj.count()>0:
                random_project_group_supplier = pgs_obj.order_by('?').first()
                survey_url = random_project_group_supplier.supplier_survey_url
                survey_url = survey_url.replace('PID=XXXXX', f"PID={pid}")
                survey_url = survey_url.replace("PID=%%PID%%", f"PID={pid}")
                redirect_url = f"{survey_url}&BSC={base_supplier_cpi}&pgn={random_project_group_supplier.project_group.project_group_number}"

                # Record Which Page the Respondent was last seen
                # resp_obj.last_page_seen = f'TrafficRouting Redirected Page & being redirected to {redirect_url}'
                # resp_obj.save()
            
                return Response(data={'redirect_url':redirect_url})

        # Record Which Page the Respondent was last seen
        # resp_obj.last_page_seen = f'TrafficRouting Redirected Page & being redirected to {redirect_url}'
        # resp_obj.save()

        redirect_url = "/survey/pre/suppliersideredirect/"+str(url_safe_string)
        return Response(data={'suppliersideredirect_url':redirect_url})
    

class ResearchDefenderSearchView(APIView):

    def post(self,request):
        screened = False
        final_detailed_reason = ""
        url_string = self.request.GET.get('url_string')
        respondent_obj = RespondentDetail.objects.select_related('respondentdetailsrelationalfield','respondenturldetail', 'respondentpagedetails').get(respondenturldetail__url_safe_string=url_string)
        respondent_obj.respondentpagedetails.last_page_seen = 'Research Defender Data store'
        respondent_obj.respondentpagedetails.save()

        ResearchDefenderFailureReasonDataStore.objects.update_or_create(
            respondent = respondent_obj, defaults={
                'defender_response' : request.data
                }
            )
        
        try:
            merge_dict = request.data['Surveys'][0]
            merge_dict.update(request.data['Respondent'])
            survey_number = merge_dict['survey_number']
        except Exception as error:
            surveyentry_log(f'{error}Exception number ------142 raised',url_string)
            respondent_obj.final_detailed_reason = f"failure_reason- {error}"
            respondent_obj.resp_status = 2
            respondent_obj.save()
            return Response({"status":"2"}, status=status.HTTP_200_OK)
        
        try:    
            project_group_obj = ProjectGroup.objects.get(project_group_number = survey_number)
            if respondent_obj.resp_status == "1":
                if project_group_obj.project_group_security_check:
                    if project_group_obj.project_group_ip_check and project_group_obj.duplicate_check and merge_dict['duplicate_score'] > project_group_obj.duplicate_score:
                        screened = True
                        final_detailed_reason = f"High Duplicate Score - {merge_dict['duplicate_score']}/{project_group_obj.duplicate_score}"
                    if not (screened) and project_group_obj.threat_potential_check and merge_dict['threat_potential_score'] > project_group_obj.threat_potential_score:
                        screened = True
                        final_detailed_reason = f"High threat Potential score - {merge_dict['threat_potential_score']}/{project_group_obj.threat_potential_score}"

                    if not(screened) and project_group_obj.failure_check and merge_dict['failure_reason'] in project_group_obj.failure_reason:
                        screened = True
                        failure_reason_choices = {
                            "01":"Everything all right",
                            "02":"Duplicate entrant into survey",
                            "03":"User Emulator",
                            "04":"Nefarious VPN usage detected",
                            "05":"TOR network detected",
                            "06":"Public proxy server detected",
                            "07":"Web proxy service used",
                            "08":"Web crawler usage detected",
                            "09":"Internet fraudster detected",
                            "10":"Retail and ad-tech fraudster detected ",
                            "11":"IP Address subnet detected",
                            "12":"Recent Abuse detected",
                            "13":"Duplicate Survey Group detected",
                            "14":"Navigator Webdriver detected",
                            "15":"Developer tool detected",
                        }
                        final_detailed_reason = f"failure_reason - {failure_reason_choices[merge_dict['failure_reason']]}"

                ResearchDefenderSearch.objects.update_or_create(respondent=respondent_obj,defaults=merge_dict)
                if settings.SERVER_TYPE in ['production'] and project_group_obj.project_group_security_check and respondent_obj.url_type == 'Live':
                    if screened:
                        respondent_obj.resp_status = 2
                        respondent_obj.end_time = timezone.now()
                        respondent_obj.final_detailed_reason = final_detailed_reason
                        respondent_obj.save()
                        return Response({"status":"2"}, status=status.HTTP_200_OK)
                return Response({"status":"1"}, status=status.HTTP_200_OK)
            else:
                return Response({"status":"2"}, status=status.HTTP_200_OK)
        except Exception as error:
            surveyentry_log(f'{error}Exception number ------143 raised',url_string)
            respondent_obj.final_detailed_reason = f"failure_reason- {error}"
            respondent_obj.resp_status = 2
            respondent_obj.save()
            return Response({"status":"2"}, status=status.HTTP_200_OK)


class SurveyEntryDecision(APIView):

    def post(self,request):
        try:
            source = request.data['source']
            subsuppliercode = request.data.get('sub_sup',None)
            question_answer_dict = request.data['question_answer_dict']
            pid = request.data['pid']
            glsid = request.data['glsid']
            qdata = {}

            for question in question_answer_dict:
                if question['question_id'] == '112521':
                    qdata[question['question_id']] = (question['answer_id']).replace('/','-')
                elif question['question_id'] == '112498':
                    qdata[question['question_id']] = question['answer_id']
                else:
                    qdata[question['question_id']] = [question['answer_id']]

            project_obj = ProjectGroup.objects.get(project_group_encodedS_value = glsid)
            suppliercode = SupplierOrganisation.objects.get(id=source).supplier_code

            country = project_obj.project_group_country.country_code
            language = project_obj.project_group_language.language_code

            if subsuppliercode:
                mincpi = ProjectGroupSubSupplier.objects.get(
                    sub_supplier_org__sub_supplier_code = subsuppliercode,project_group = project_obj).cpi
            else:
                mincpi = ProjectGroupSupplier.objects.get(
                    supplier_org_id = source,project_group = project_obj).cpi
            
            attempted_survey_list = list(RespondentDetail.objects.filter(respondenturldetail__pid = pid).values_list('project_group_number',flat=True))
            finalised_survey_list = survey_decision(get_project_group_supplier_overall(suppliercode,subsuppliercode, country, language,mincpi),qdata)

            if len(finalised_survey_list):
                finalised_survey = random.choice(finalised_survey_list.order_by('-project_group__project_group_incidence').exclude(project_group__project_group_number__in = attempted_survey_list)[:5])
                return Response({"glsid":finalised_survey.project_group.project_group_encodedS_value}, status=status.HTTP_200_OK)
            else:
                return Response({"message":"Sorry..!No Any Survey Found"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"status":"Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)
        

class SurveyEntryGetQuestionAnswers(APIView):

    def post(self,request):
        try:
            glsid = request.data['glsid']
            supplierid = request.data.get('source',0)
            sub_sup = request.data.get('sub_sup',0)
            supplierstatus = 'Paused'
            if supplierid:
                projectgrop_supplier_obj = ProjectGroupSupplier.objects.get(supplier_org_id = supplierid,project_group__project_group_encodedS_value = glsid)
                if projectgrop_supplier_obj.project_group.project_group_status == 'Live':
                    supplierstatus = 'Live'

            if sub_sup:
                projectgrop_sub_supplier_obj = ProjectGroupSubSupplier.objects.get(sub_supplier_org__sub_supplier_code = sub_sup,project_group__project_group_encodedS_value = glsid)
                if projectgrop_sub_supplier_obj.project_group.project_group_status == 'Live' and supplierstatus == 'Live':
                    supplierstatus = 'Live'
                else:
                    supplierstatus = 'Paused'

            prescreener_to_show = ProjectGroupPrescreener.objects.filter(project_group_id__project_group_encodedS_value = glsid,is_enable=True)

            if len(prescreener_to_show):
                customer_code = prescreener_to_show.first().project_group_id.project.project_customer.customer_url_code

                serializer = PrescreenerForBeforeSurveyEntry(prescreener_to_show, many=True, context = {'client_code':customer_code})

                return Response({"Qulifications":serializer.data,"supplierstatus":supplierstatus}, status=status.HTTP_200_OK)
            else:
                return Response({"Qulifications":[],"supplierstatus":supplierstatus}, status=status.HTTP_200_OK)
        except:
            return Response({"status":"Something Went Wrong"}, status=status.HTTP_400_BAD_REQUEST)


class SurveyEntryAnswerFileUpload(APIView):

    def post(self,request,url_string):
        try:
            filetypes = ['pdf','jpg','jpeg','png','xls','xlsx','csv','docx','doc','zip','txt','HEIF','heif','hevc','HEVC']

            if request.FILES['answer_file'].name.split(".")[-1] not in filetypes:  
                return Response(data={'status':'2'})
            
            resp_obj = RespondentDetail.objects.only('respondentpagedetails').get(respondenturldetail__url_safe_string=url_string)

            question_obj = TranslatedQuestion.objects.get(Internal_question_id=request.data['question_id'])

            prescreener_question_obj = ProjectGroupPrescreener.objects.get(translated_question_id__Internal_question_id=request.data['question_id'], project_group_id__project_group_number = resp_obj.project_group_number,is_enable = True)

            question_data, question_data_created = ProjectGroupPrescreenerDataStore.objects.get_or_create(respondent = resp_obj, translated_question_id = question_obj, prescreener_question = prescreener_question_obj)

            question_data.answer_file = request.FILES['answer_file']
            question_data.save()
            
            return Response(data={'status':'1'})
        except:
            return Response(data={'status':'2'})