from datetime import date
from hashlib import blake2b
from django.conf import settings
from rest_framework import status
from requests import Response
from Prescreener.models import ProjectGroupPrescreener
from Project.models import Language, Project, ProjectGroup, ProjectGroupStatsCalculations, ProjectGroupSubSupplier, ProjectGroupSupplier
from Project.serializers import median_value
from Questions.models import TranslatedAnswer, TranslatedQuestion
from Supplier.models import SupplierOrganisation
from Surveyentry.models import RespondentDetail
from employee.models import Country
from django.db.models import Sum, F,Value,ExpressionWrapper,When,Count,Q,Case
from django.db.models.functions import Cast,Coalesce
from django.db import models
import concurrent.futures


class ProjectViewSet:

    def project_list():
        project_obj_list = Project.objects.all()
        return project_obj_list
    
    def project_get(project_number_or_id):
        try:
            project_obj = Project.objects.get(project_number = project_number_or_id)
        except:
            try:
                project_obj = Project.objects.get(id = project_number_or_id)
            except:
                return None
        return project_obj

    def project_create(request,**kwargs):
        if kwargs['project_revenue_year'] > date.today().year or kwargs['project_revenue_year'] == date.today().year and kwargs['project_revenue_month'] >= date.today().month and kwargs['project_name'] not in ['',None]:
            project_obj = Project.objects.create(
                project_name = kwargs['project_name'],
                project_po_number = kwargs['project_po_number'],
                project_category = kwargs['project_category'],
                project_redirectID = ' ',
                project_revenue_month = kwargs['project_revenue_month'],
                project_revenue_year = kwargs['project_revenue_year'],
                project_notes = kwargs['project_notes'],
                project_client_invoicing_contact_person_id = kwargs['project_client_invoicing_contact_person'],
                project_client_contact_person_id = kwargs['project_client_contact_person'],
                project_manager_id = kwargs['project_manager'],
                secondary_project_manager_id = kwargs['secondary_project_manager'],
                project_customer_id = kwargs['project_customer'],
                project_currency_id = kwargs['project_currency'],
                project_sales_person_id = kwargs['project_sales_person'],
                project_type = kwargs['project_type'],
                project_redirect_type = kwargs['project_redirect_type'],
                project_status = kwargs['project_status'] if 'project_status' in kwargs else 'Live',
                bid_id = kwargs['bid'] if 'bid' in kwargs else None
            )
            project_number = 'PVP'+ str(1000+project_obj.id)
            project_obj.project_number = project_number
            key_value1 = 'df8ZLPDF36RfrnepCpTGXCTkRK9BfS'
            key_value2 = 'gPu2Cs7LbKxdK5LHFwTLRkg4atdSZW'
            keys = key_value1 + key_value2 + str(project_number)
            h2 = blake2b(digest_size=6)
            h2.update(keys.encode())
            project_obj.project_redirectID = h2.hexdigest()
            project_obj.save()
            return project_obj
        else:
            return Response({'error': 'Please enter a valid Details..!'}, status=status.HTTP_400_BAD_REQUEST)
    
    def project_update(request,project_id,**kwargs):
        if kwargs['project_revenue_year'] > date.today().year or kwargs['project_revenue_year'] == date.today().year and kwargs['project_revenue_month'] >= date.today().month and kwargs['project_name'] not in ['',None] and kwargs['id'] not in ['',None]:
            project_obj,created = Project.objects.update_or_create(
                id = project_id,
                defaults={
                    "project_name" : kwargs['project_name'],
                    "project_po_number" : kwargs['project_po_number'],
                    "project_category" : kwargs['project_category'],
                    "project_redirectID" : F('project_redirectID'),
                    "project_revenue_month" : kwargs['project_revenue_month'],
                    "project_revenue_year" : kwargs['project_revenue_year'],
                    "project_notes" : kwargs['project_notes'],
                    "project_client_invoicing_contact_person_id" : kwargs['project_client_invoicing_contact_person'],
                    "project_client_contact_person_id" : kwargs['project_client_contact_person'],
                    "project_manager_id" : kwargs['project_manager'],
                    "secondary_project_manager_id" : kwargs['secondary_project_manager'],
                    "project_customer_id" : kwargs['project_customer'],
                    "project_currency_id" : kwargs['project_currency'],
                    "project_sales_person_id" : kwargs['project_sales_person'],
                    "project_type" : kwargs['project_type'],
                    "project_redirect_type" : kwargs['project_redirect_type'],
                }
            )
            project_obj.save()
            return project_obj
        else:
            return Response({'error': 'Please enter a valid Details..!'}, status=status.HTTP_400_BAD_REQUEST)


class CountryViewSet:

    def country_list():
        project_obj_list = Country.objects.all()
        return project_obj_list
 
    
class LanguageViewSet:

    def language_list():
        project_obj_list = Language.objects.all()
        return project_obj_list


class ProjectGroupViewSet:

    def project_group_list():
        
        project_group_obj_list = ProjectGroup.objects.all()
        return project_group_obj_list

    def project_group_get(project_group_id):
        return ProjectGroup.objects.get(id = project_group_id)

    def project_group_create(request,**kwargs):
        
        if not(kwargs['project_group_enddate'] <= kwargs['project_group_startdate']) and not(kwargs['project_group_enddate'] <= str(date.today())):
            projectgroup_obj = ProjectGroup.objects.create(
                project_device_type = kwargs['project_device_type'],
                project_group_name = kwargs['project_group_name'],
                project_audience_type = kwargs['project_audience_type'],
                project_group_status = kwargs['project_group_status'],
                project_group_client_url_type = kwargs['project_group_client_url_type'],
                project_group_incidence = kwargs['project_group_incidence'],
                project_group_loi = kwargs['project_group_loi'],
                project_group_completes = kwargs['project_group_completes'],
                project_group_clicks = kwargs['project_group_clicks'],
                project_group_cpi = kwargs['project_group_cpi'],
                project_group_startdate = kwargs['project_group_startdate'],
                project_group_enddate = kwargs['project_group_enddate'],
                enable_panel = kwargs['enable_panel'],
                project_id = kwargs['project'],
                project_group_country_id = kwargs['project_group_country'],
                project_group_language_id = kwargs['project_group_language'],
                created_by = request.user,
                modified_by = request.user,
                respondent_risk_check = True,
                failure_check = True,
                duplicate_check = True,
                duplicate_score = 80,
                failure_reason = ["02","03","04","05","06","07","08","09","10","11","12","13","14","15"]
            )
            if projectgroup_obj.project_group_client_url_type == "1":
                projectgroup_obj.project_group_liveurl = kwargs['project_group_live_url']
                projectgroup_obj.project_group_testurl = kwargs['project_group_test_url']
            project_group_number = 1000000 + int(projectgroup_obj.id)
            projectgroup_obj.project_group_number = project_group_number
            key_value = 'LTauDqcaX4PdeBANhj3eLfkfrN65QEjhJ'
            h = blake2b(digest_size=25)
            h1 = blake2b(digest_size=25)
            grp_num = bin(project_group_number)
            h.update(grp_num.encode())
            val = h.hexdigest() + key_value
            h1.update(val.encode())
            excluded_project_grp = request.data.get('excluded_project_group', '')
            projectgroup_obj.excluded_project_group = [str(project_group_number)] if excluded_project_grp in ['',None] else [str(project_group_number)] + excluded_project_grp
            projectgroup_obj.project_group_encodedS_value = h.hexdigest()
            projectgroup_obj.project_group_encodedR_value = h1.hexdigest()
            projectgroup_obj.project_group_redirectID = projectgroup_obj.project.project_redirectID
            projectgroup_obj.project_group_surveyurl = settings.SURVEY_URL+"survey?glsid=" + projectgroup_obj.project_group_encodedS_value
            projectgroup_obj.project_group_revenue = projectgroup_obj.project_group_completes * projectgroup_obj.project_group_cpi
            projectgroup_obj.threat_potential_score = projectgroup_obj.project.project_customer.threat_potential_score
            projectgroup_obj.save()
            return projectgroup_obj
        else:
            return Response({'error': 'Please enter a valid Details..!'}, status=status.HTTP_400_BAD_REQUEST)
            
    def project_group_update(request,project_group_id,**kwargs):

        if not(kwargs['project_group_enddate'] <= kwargs['project_group_startdate']) and not(kwargs['project_group_enddate'] <= str(date.today())):
            projectgroup_obj, created = ProjectGroup.objects.update_or_create(
                id = project_group_id,
                defaults = {
                    "project_device_type" : kwargs['project_device_type'],
                    "project_group_name" : kwargs['project_group_name'],
                    "project_audience_type" : kwargs['project_audience_type'],
                    "enable_panel" : kwargs['enable_panel'],
                    "project_group_cpi" : kwargs['project_group_cpi'],
                    "project_group_completes" : kwargs['project_group_completes'],
                    "project_group_clicks" : kwargs['project_group_clicks'],
                    "project_group_incidence" : kwargs['project_group_incidence'],
                    "project_group_loi" : kwargs['project_group_loi'],
                    "project_group_client_url_type" : kwargs['project_group_client_url_type'],
                    "project_group_startdate" : kwargs['project_group_startdate'],
                    "threat_potential_score" : kwargs['threat_potential_score'],
                    "project_group_enddate" : kwargs['project_group_enddate'],
                    "project_group_language_id" : kwargs['project_group_language'],
                    "project_group_country_id" : kwargs['project_group_country'],
                    "project_group_security_check" : kwargs['project_group_security_check'],
                    "project_group_ip_check" : kwargs['project_group_ip_check'],
                    "excluded_project_group" : kwargs['excluded_project_group'],
                    "research_defender_oe_check" : kwargs['research_defender_oe_check'],
                    "project_group_number" : kwargs['project_group_number'],
                    "project_group_pid_check" : kwargs['project_group_pid_check'],
                    "project_group_allowed_svscore" : kwargs['project_group_allowed_svscore'],
                    "project_group_allowed_dupescore" : kwargs['project_group_allowed_dupescore'],
                    "project_group_allowed_fraudscore" : kwargs['project_group_allowed_fraudscore'],
                    "show_on_DIY" : kwargs['show_on_DIY'],
                    "respondent_risk_check" : kwargs['respondent_risk_check'],
                    "failure_check" : kwargs['failure_check'],
                    "duplicate_check" : kwargs['duplicate_check'],
                    "duplicate_score" : kwargs['duplicate_score'],
                    "failure_reason" : kwargs['failure_reason'],
                    "threat_potential_check" : kwargs['threat_potential_check'],
                }
            )
            if projectgroup_obj.project_group_client_url_type == "1":
                projectgroup_obj.project_group_liveurl = kwargs['project_group_live_url']
                projectgroup_obj.project_group_testurl = kwargs['project_group_test_url']
            if projectgroup_obj.project_group_security_check == True:
                if projectgroup_obj.excluded_project_group == []:
                    projectgroup_obj.excluded_project_group = [str(projectgroup_obj.project_group_number)]
                    if projectgroup_obj.project_group_ip_check == False:
                        projectgroup_obj.excluded_project_group = []
            else:
                projectgroup_obj.project_group_ip_check = False
                projectgroup_obj.project_group_pid_check = False
                projectgroup_obj.research_defender_oe_check = False
                projectgroup_obj.project_group_allowed_svscore = 0
                projectgroup_obj.project_group_allowed_dupescore = 0
                projectgroup_obj.project_group_allowed_fraudscore = 0
                projectgroup_obj.threat_potential_score = 0
                projectgroup_obj.excluded_project_group = []
            projectgroup_obj.save()
            return projectgroup_obj
        else:
            return Response({'error': 'Please enter a valid Details..!'}, status=status.HTTP_400_BAD_REQUEST)

    def project_group_create_update_default_question(project_group_id):
        
        # Added For only US Surveys
        prescreener_question_dict = {}
        try:
            # Age Question
            question_data1 = TranslatedQuestion.objects.get(
                Internal_question_id = "112521",lang_code=project_group_id.project_group_language)
            allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                translated_parent_question = question_data1).values_list('id',flat=True))
            prescreener_question_dict[question_data1] = {
                                "allowedoptions" : allowedoptions_ids,
                                "allowedRangeMin" : '18,25,30,35,40,45,50,55,60,65',
                                "allowedRangeMax" : '24,29,34,39,44,49,54,59,64,100',
                                "sequence" : 1
                            }

            #Gender Question
            question_data2 = TranslatedQuestion.objects.get(
                Internal_question_id = "112499",lang_code=project_group_id.project_group_language)
            allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                translated_parent_question = question_data2).values_list('id',flat=True))        
            prescreener_question_dict[question_data2] = {
                                "allowedoptions" : allowedoptions_ids,
                                "allowedRangeMin" : '',
                                "allowedRangeMax" : '',
                                "sequence" : 2
                            }

            #zipcode Question
            question_data3 = TranslatedQuestion.objects.get(
                Internal_question_id = "112498",lang_code=project_group_id.project_group_language)
            allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                translated_parent_question = question_data3).values_list('id',flat=True))        
            prescreener_question_dict[question_data3] = {
                                "allowedoptions" : allowedoptions_ids,
                                "allowedRangeMin" : '',
                                "allowedRangeMax" : '',
                                "sequence" : 3
                            }
            
            #HHI Question
            question_data4 = TranslatedQuestion.objects.get(
                Internal_question_id = "112393",lang_code=project_group_id.project_group_language)
            allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                translated_parent_question = question_data4).values_list('id',flat=True))        
            prescreener_question_dict[question_data4] = {
                                "allowedoptions" : allowedoptions_ids,
                                "allowedRangeMin" : '',
                                "allowedRangeMax" : '',
                                "sequence" : 4
                            }
            
            #Ethnicity Question
            question_data5 = TranslatedQuestion.objects.get(
                Internal_question_id = "112394",lang_code=project_group_id.project_group_language)
            allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                translated_parent_question = question_data5).values_list('id',flat=True))        
            prescreener_question_dict[question_data5] = {
                                "allowedoptions" : allowedoptions_ids,
                                "allowedRangeMin" : '',
                                "allowedRangeMax" : '',
                                "sequence" : 5
                            }
            
            #Employment Question
            question_data6 = TranslatedQuestion.objects.get(
                Internal_question_id = "112258",lang_code=project_group_id.project_group_language)
            allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                translated_parent_question = question_data6).values_list('id',flat=True))        
            prescreener_question_dict[question_data6] = {
                                "allowedoptions" : allowedoptions_ids,
                                "allowedRangeMin" : '',
                                "allowedRangeMax" : '',
                                "sequence" : 6
                            }
            
            #Employment Question
            question_data7 = TranslatedQuestion.objects.get(
                Internal_question_id = "112304",lang_code=project_group_id.project_group_language)
            allowedoptions_ids = list(TranslatedAnswer.objects.filter(
                translated_parent_question = question_data7).values_list('id',flat=True))        
            prescreener_question_dict[question_data7] = {
                                "allowedoptions" : allowedoptions_ids,
                                "allowedRangeMin" : '',
                                "allowedRangeMax" : '',
                                "sequence" : 7
                            }
        
        except:
            pass
        for question_key, values in prescreener_question_dict.items():
            ques_ans_obj, ques_ans_obj_created = ProjectGroupPrescreener.objects.update_or_create(
                            project_group_id = project_group_id,
                            translated_question_id = question_key,
                            defaults = {
                            "allowedRangeMin" : values['allowedRangeMin'],
                            "allowedRangeMax" : values['allowedRangeMax'],
                            "sequence" : values['sequence']
                            }
                        )
        
            ques_ans_obj.allowedoptions.clear()
            ques_ans_obj.allowedoptions.add(*values['allowedoptions'])
        return True
    

class ProjectGroupSupplierViewSet:

    def project_group_supplier_list():
        
        project_group_supplier_obj_list = ProjectGroupSupplier.objects.all()
        return project_group_supplier_obj_list

    def project_group_supplier_get(project_group_supplier_id):
        try:
            project_group_supplier_obj = ProjectGroupSupplier.objects.get(id = project_group_supplier_id)
            return project_group_supplier_obj
        except:
            return None
    
    def project_group_supplier_create(request,**kwargs):
        if not (ProjectGroupSupplier.objects.filter(supplier_org_id = kwargs['supplier_org'],project_group_id = kwargs['project_group']).last()) and SupplierOrganisation.objects.filter(id = kwargs['supplier_org'],supplier_status = '1').exists():
            project_group_obj = ProjectGroupViewSet.project_group_get(kwargs['project_group'])
            if project_group_obj.project_group_status == "Live":
                if int(kwargs['completes']) <= project_group_obj.project_group_completes:
                    project_grp_supplier_obj = ProjectGroupSupplier.objects.create(
                        completes = kwargs['completes'],
                        clicks = kwargs['clicks'],
                        cpi = kwargs['cpi'],
                        supplier_completeurl = kwargs['supplier_complete_url'],
                        supplier_terminateurl = kwargs['supplier_terminate_url'],
                        supplier_quotafullurl = kwargs['supplier_quotafull_url'],
                        supplier_securityterminateurl = kwargs['supplier_securityterminate_url'],
                        supplier_postbackurl = kwargs['supplier_postback_url'],
                        supplier_internal_terminate_redirect_url = kwargs['supplier_internal_terminate_redirect_url'],
                        supplier_terminate_no_project_available = kwargs['supplier_terminate_no_project_available'],
                        supplier_org_id = kwargs['supplier_org'],
                        project_group_id = kwargs['project_group'],
                    )
                    project_grp_supplier_obj.supplier_survey_url = project_group_obj.project_group_surveyurl+"&source="+str(project_grp_supplier_obj.supplier_org.id)+"&PID=XXXXX"
                    project_grp_supplier_obj.save()
                    return project_grp_supplier_obj
                else:
                    return Response({'error': 'Completes Must be less than or equal to project group completes'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error":"You Can't Add Supplier ..You Need to Live Survey First..!"}, status=status.HTTP_400_BAD_REQUEST)

    def project_group_supplier_update(request,proj_grp_supp_id,**kwargs):

        projectgroupsupplierobj = ProjectGroupSupplierViewSet.project_group_supplier_get(proj_grp_supp_id)
        supplier_type = SupplierOrganisation.objects.get(id=kwargs['supplier_org']).supplier_type

        if projectgroupsupplierobj.supplier_org.id != kwargs['supplier_org'] and supplier_type == '1':
            return Response({'error': 'You do not have access to change the supplier..!'}, status=status.HTTP_400_BAD_REQUEST)

        if supplier_type != '1':
            return Response({'error': 'You do not have access to add this supplier..!'}, status=status.HTTP_400_BAD_REQUEST)


        if int(kwargs['completes']) <= projectgroupsupplierobj.project_group.project_group_completes:
            project_grp_supplier_obj,created = ProjectGroupSupplier.objects.update_or_create(
                id = kwargs['id'],
                defaults={
                    "completes" : kwargs['completes'],
                    "clicks" : kwargs['clicks'],
                    "cpi" : kwargs['cpi'],
                    "supplier_completeurl" : kwargs['supplier_complete_url'],
                    "supplier_terminateurl" : kwargs['supplier_terminate_url'],
                    "supplier_quotafullurl" : kwargs['supplier_quotafull_url'],
                    "supplier_securityterminateurl" : kwargs['supplier_securityterminate_url'],
                    "supplier_postbackurl" : kwargs['supplier_postback_url'],
                    "supplier_internal_terminate_redirect_url" : kwargs['supplier_internal_terminate_redirect_url'],
                    "supplier_terminate_no_project_available" : kwargs['supplier_terminate_no_project_available'],
                }
            )     
            return project_grp_supplier_obj
        else:
            return Response(data={'error': 'completes must be less than or equal to project group completes...!'}, status=status.HTTP_400_BAD_REQUEST)

    def project_group_supplier_statistics(project_group_num,sup_type):

        # For List of Supplier

        grp_supp_list = ProjectGroupSupplier.objects.select_related(
            'project_group', 'supplier_org', 'respondentdetailsrelationalfield__respondent').filter(project_group__project_group_number=project_group_num, supplier_org__supplier_type = sup_type).values(
            'id',
            'project_group',
            'supplier_org',
            'clicks',
            'cpi',
            'supplier_survey_url',
            'supplier_internal_terminate_redirect_url',
            'supplier_terminate_no_project_available',
            'supplier_status',
            supplier_complete_url = F('supplier_completeurl'),
            supplier_terminate_url = F('supplier_terminateurl'),
            supplier_quotafull_url = F('supplier_quotafullurl'),
            supplier_securityterminate_url = F('supplier_securityterminateurl'),
            supplier_postback_url = F('supplier_postbackurl'),
            total_N=F('completes'),).annotate(
                completes = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4], respondentdetailsrelationalfield__respondent__url_type='Live')),
                incompletes = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=[3,9], respondentdetailsrelationalfield__respondent__url_type='Live')),
                terminates = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=[5], respondentdetailsrelationalfield__respondent__url_type='Live')),
                security_terminate = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=[7], respondentdetailsrelationalfield__respondent__url_type='Live')),
                quota_full = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=[6], respondentdetailsrelationalfield__respondent__url_type='Live')),
                starts = Count('respondentdetailsrelationalfield', filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=[3,4,5,6,7,8,9], respondentdetailsrelationalfield__respondent__url_type='Live')),
                total_visits = Count('respondentdetailsrelationalfield',filter=Q(respondentdetailsrelationalfield__respondent__url_type='Live')),
                incidence = Case(
                        When(Q(completes=0), then=Cast(0.0, output_field=models.DecimalField(max_digits=7,decimal_places=2))), 
                        default=Cast((100 * F('completes') / Count(
                                'respondentdetailsrelationalfield', 
                                filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4,5], respondentdetailsrelationalfield__respondent__url_type='Live')
                            )
                        ), output_field=models.DecimalField(max_digits=7,decimal_places=2))
                    ),
                median_LOI = ExpressionWrapper(
                        Value(
                            round(
                                float(
                                    median_value(
                                        RespondentDetail.objects.filter(resp_status__in=[4], url_type='Live', project_group_number=F('project_group_number'), source=F('source')
                                        ),'duration'
                                    )
                                ),0
                            )
                        ), output_field=models.FloatField()
                    ),
                revenue = Coalesce(
                        Sum(
                            'respondentdetailsrelationalfield__respondent__project_group_cpi', 
                            filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in=[4], respondentdetailsrelationalfield__respondent__url_type='Live')
                        ), 0.0
                    ),
                expense = Coalesce(
                        Sum(
                            'respondentdetailsrelationalfield__respondent__supplier_cpi', 
                            filter=Q(respondentdetailsrelationalfield__respondent__resp_status=4, respondentdetailsrelationalfield__respondent__url_type='Live')
                        ), 0.0
                    ),
                margin= Case(
                        When(Q(revenue=0.0) | Q(revenue=None), then=Cast(0.0, output_field=models.DecimalField(max_digits=7,decimal_places=2))), 
                        default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'), output_field=models.DecimalField(max_digits=7,decimal_places=2)),
                    ),
            )
        return grp_supp_list

    def project_group_sub_supplier_statistics(project_group_num,sup_type):

        grp_supp_list = ProjectGroupSubSupplier.objects.select_related('project_group', 'sub_supplier_org', 'respondentprojectgroupsubsupplier__respondent').filter(project_group__project_group_number=project_group_num, sub_supplier_org__supplier_org_id__supplier_type = sup_type).values(
            'id',
            'project_group', 
            'sub_supplier_org',
            'clicks',
            'cpi',
            'sub_supplier_survey_url',
            'sub_supplier_internal_terminate_redirect_url',
            'sub_supplier_terminate_no_project_available',
            'sub_supplier_status',
            sub_supplier_complete_url = F('sub_supplier_completeurl'),
            sub_supplier_terminate_url = F('sub_supplier_terminateurl'),
            sub_supplier_quotafull_url = F('sub_supplier_quotafullurl'),
            sub_supplier_securityterminate_url = F('sub_supplier_securityterminateurl'),
            sub_supplier_postback_url = F('sub_supplier_postbackurl'),
            total_N=F('completes'),
            ).annotate(
                completes = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[4], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                incompletes = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[3,9], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                terminates = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[5], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                security_terminate = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[7], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                quota_full = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[6], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                starts = Count('respondentprojectgroupsubsupplier', filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[3,4,5,6,7,8,9], respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                total_visits = Count('respondentprojectgroupsubsupplier',filter=Q(respondentprojectgroupsubsupplier__respondent__url_type='Live')),
                incidence = Case(
                        When(Q(completes=0), then=Cast(0.0, output_field=models.DecimalField(max_digits=7,decimal_places=2))), 
                        default=Cast((100 * F('completes') / Count(
                                'respondentprojectgroupsubsupplier', 
                                filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[4,5], respondentprojectgroupsubsupplier__respondent__url_type='Live')
                            )
                        ), output_field=models.DecimalField(max_digits=7,decimal_places=2))
                    ),
                median_LOI = ExpressionWrapper(
                        Value(
                            round(
                                float(
                                    median_value(
                                        RespondentDetail.objects.filter(
                                            resp_status__in=[4], 
                                            url_type='Live', 
                                            project_group_number=F('project_group_number'), 
                                            source=F('source')
                                        ),'duration'
                                    )
                                ),0
                            )
                        ), output_field=models.FloatField()
                    ),
                revenue = Coalesce(
                        Sum(
                            'respondentprojectgroupsubsupplier__respondent__project_group_cpi', 
                            filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[4], respondentprojectgroupsubsupplier__respondent__url_type='Live')
                        ), 0.0
                    ),
                expense = Coalesce(
                        Sum(
                            'respondentprojectgroupsubsupplier__project_group_sub_supplier__cpi', 
                            filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status=4, respondentprojectgroupsubsupplier__respondent__url_type='Live')
                        ), 0.0
                    ),
                margin= Case(
                        When(Q(revenue=0.0) | Q(revenue=None), then=Cast(0.0, output_field=models.DecimalField(max_digits=7,decimal_places=2))), 
                        default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'), output_field=models.DecimalField(max_digits=7,decimal_places=2)),
                    ),
            )
        return grp_supp_list
    
    def project_group_sub_supplier_stats(project_group_num,sup_type,sup_supplier_id):

        respdata = RespondentDetail.objects.filter(
            project_group_number = project_group_num,url_type='Live',
            respondentdetailsrelationalfield__project_group_sub_supplier__sub_supplier_org__id = sup_supplier_id).aggregate(
                completes = Count('id',filter=Q(resp_status__in=[4])),
                incompletes = Count('id', filter=Q(resp_status__in=[3,9])),
                terminates = Count('id',filter=Q(resp_status__in=[5])),
                security_terminate = Count('id',filter=Q(resp_status__in=[7])),
                quota_full = Count('id',filter=Q(resp_status__in=[6])),
                starts = Count('id',filter=Q(resp_status__in=[3,4,5,6,7,8,9])),
                total_visits = Count('id'),
                revenue = Coalesce(
                    Sum(
                        'respondentprojectgroupsubsupplier__respondent__project_group_cpi', 
                        filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status__in=[4], respondentprojectgroupsubsupplier__respondent__url_type='Live')
                    ), 0.0
                ),
                expense = Coalesce(
                    Sum(
                        'respondentprojectgroupsubsupplier__respondent__supplier_cpi', 
                        filter=Q(respondentprojectgroupsubsupplier__respondent__resp_status=4, respondentprojectgroupsubsupplier__respondent__url_type='Live')
                    ), 0.0
                ),
            )
        return respdata


class RespondentDetailstatisticsCalculations:

    def get_total_visits(request, *args, **kwargs):
        total_visits = request.count()
        return total_visits

    def get_starts(request):        
        starts = request.filter(resp_status__in=[3,4,5,6,7,8,9]).count()
        return starts

    def get_incidence(request):
        numerator = request.filter(resp_status__in=[4]).count()
        denomerator = request.filter(resp_status__in=[4,5]).count()
        try:
            incidence = (numerator/denomerator)*100
        except ZeroDivisionError:
            incidence = 0
        return incidence

    def get_median_LOI(request):
        survey_details = request.filter(resp_status__in=[4,9], url_type='Live')
        get_median = float(median_value(survey_details, 'duration'))
        median_LOI = round(get_median, 0)
        return median_LOI

    def get_revenue(request):
        revenue = request.filter(resp_status__in=[4,9], url_type='Live').aggregate(Sum("project_group_cpi"))
        return revenue['project_group_cpi__sum']

    def get_expense(request):
        expense = request.filter(resp_status=4, url_type='Live').aggregate(Sum("supplier_cpi"))
        return expense['supplier_cpi__sum']

    def get_margin(request):
        revenue = request.filter(resp_status__in=[4,9], url_type='Live').aggregate(Sum("project_group_cpi"))
        expense = request.filter(resp_status=4, url_type='Live').aggregate(Sum("supplier_cpi"))
        if revenue['project_group_cpi__sum'] == None or expense['supplier_cpi__sum'] == None:
            margin = 0
        else:
            margin = (revenue['project_group_cpi__sum'] - expense['supplier_cpi__sum']) / revenue['project_group_cpi__sum']
        return margin*100

    def get_completes(request):
        return request.filter(resp_status__in=[4,9]).count()

    def get_incompletes(request):
        return request.filter(resp_status__in=[3]).count()

    def get_terminates(request):
        return request.filter(resp_status=5).count()

    def get_security_terminate(request):
        return request.filter(resp_status=7).count()

    def get_quota_full(request):
        return request.filter(resp_status=6).count()


def project_group_statistics_create(project_number):

    project_group_list = list(ProjectGroup.objects.only('project_group_number').filter(project_group_number = project_number).values_list('project_group_number',flat=True))
    user_bulk_update_list = []
    respondent_details = list(RespondentDetail.objects.filter(
        url_type='Live',project_group_number__in = project_group_list).values('project_group_number').annotate(
            total_visits = Count('id',distinct=True), 
            starts = Count('resp_status', filter=Q(resp_status__in=[3,4,5,6,7,8,9])),
            internal_terminates = Count('resp_status', filter=Q(resp_status=2)), 
            completes = Count('resp_status', filter=Q(resp_status__in=[4,9])),
            incompletes = Count('resp_status', filter=Q(resp_status=3)), 
            terminates = Count('resp_status', filter=Q(resp_status=5)), 
            quota_full = Count('resp_status', filter=Q(resp_status=6)), 
            security_terminate = Count('resp_status', filter=Q(resp_status=7)),
            complete_rejected_by_client = Count('resp_status', filter=Q(resp_status=8)),
            client_rejected = Count('resp_status', filter=Q(resp_status=9)),
            revenue = Sum('project_group_cpi', filter=Q(resp_status__in=[4,9]), default=0),
            expense = Sum('supplier_cpi', filter=Q(resp_status__in=[4]),default=0),

            incidence = Case(When(Q(completes=0),then=0), default=((F('completes')*100)/(F('completes')+F('terminates')+F('quota_full')))),

            median_LOI = ExpressionWrapper(Value(round(float(median_value(RespondentDetail.objects.filter(resp_status=4, url_type='Live', project_group_number=F('project_group_number')),'duration')),0)),output_field=models.FloatField()),


            margin=Case(When(Q(revenue=0.0)|Q(revenue=0),then=Cast(0.0, models.DecimalField(max_digits=7,decimal_places=2))), 
            default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'), output_field=models.DecimalField(max_digits=7,decimal_places=2)))
        ))
    
    def parellel_surveys_stats_create(survey):
        try:
            project_group = ProjectGroup.objects.get(project_group_number = survey['project_group_number'])
            if survey['revenue'] in [None,""]:
                survey['revenue'] = 0
            if survey['expense'] in [None,""]:
                survey['expense'] = 0
            if survey['incidence'] in [None,""]:
                survey['incidence'] = 0
            if survey['median_LOI'] in [None,""]:
                survey['median_LOI'] = 0
            if survey['margin'] in [None,""]:
                survey['margin'] = 0
            user_bulk_update_list.append(ProjectGroupStatsCalculations(
                project_group = project_group,
                total_visits = survey['total_visits'],
                starts = survey['starts'],
                internal_terminate = survey['internal_terminates'],
                completes = survey['completes'],
                incompletes = survey['incompletes'],
                terminates = survey['terminates'],
                quota_full = survey['quota_full'],
                security_terminate = survey['security_terminate'],
                complete_rejected_by_client = survey['complete_rejected_by_client'],
                client_rejected = survey['client_rejected'],
                revenue = survey['revenue'],
                expense = survey['expense'],
                incidence = survey['incidence'],
                median_LOI = survey['median_LOI'],
                margin = survey['margin'],
                ))
        except:
            pass
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        yield_results = list(executor.map(parellel_surveys_stats_create, respondent_details))
    ProjectGroupStatsCalculations.objects.bulk_create(user_bulk_update_list)
    return "Success"


def project_group_statistics_update(project_number):

    project_group_list = list(ProjectGroup.objects.only('project_group_number').filter(project__project_number = project_number).values_list('project_group_number',flat=True))
    user_bulk_update_list = []
    respondent_details = list(RespondentDetail.objects.filter(
        url_type='Live',project_group_number__in = project_group_list).values(project_group_id = F('project_group_number')).annotate(
            total_visits = Count('id',distinct=True), 
            starts = Count('resp_status', filter=Q(resp_status__in=[3,4,5,6,7,8,9])),
            internal_terminates = Count('resp_status', filter=Q(resp_status=2)), 
            completes = Count('resp_status', filter=Q(resp_status__in=[4,9])),
            incompletes = Count('resp_status', filter=Q(resp_status=3)), 
            terminates = Count('resp_status', filter=Q(resp_status=5)), 
            quota_full = Count('resp_status', filter=Q(resp_status=6)), 
            security_terminate = Count('resp_status', filter=Q(resp_status=7)),
            complete_rejected_by_client = Count('resp_status', filter=Q(resp_status=8)),
            client_rejected = Count('resp_status', filter=Q(resp_status=9)),
            revenue = Sum('project_group_cpi', filter=Q(resp_status__in=[4,9]), default=0),
            expense = Sum('supplier_cpi', filter=Q(resp_status__in=[4]),default=0),

            incidence = Case(When(Q(completes=0),then=0), default=((F('completes')*100)/(F('completes')+F('terminates')+F('quota_full')))),

            median_LOI = ExpressionWrapper(Value(round(float(median_value(RespondentDetail.objects.filter(resp_status=4, url_type='Live', project_group_number=F('project_group_number')),'duration')),0)),output_field=models.FloatField()),


            margin=Case(When(Q(revenue=0.0)|Q(revenue=0),then=Cast(0.0, models.DecimalField(max_digits=7,decimal_places=2))), 
            default=Cast(((F('revenue')-F('expense'))*100)/F('revenue'), output_field=models.DecimalField(max_digits=7,decimal_places=2)))
        ))
    def parellel_surveys_stats_update(survey):
        try:
            projectstats = ProjectGroupStatsCalculations.objects.get(project_group__project_group_number = survey['project_group_id'])
            projectstats.total_visits = survey['total_visits']
            projectstats.starts = survey['starts']
            projectstats.internal_terminate = survey['internal_terminates']
            projectstats.completes = survey['completes']
            projectstats.incompletes = survey['incompletes']
            projectstats.terminates = survey['terminates']
            projectstats.quota_full = survey['quota_full']
            projectstats.security_terminate = survey['security_terminate']
            projectstats.complete_rejected_by_client = survey['complete_rejected_by_client']
            projectstats.client_rejected = survey['client_rejected']
            projectstats.revenue = survey['revenue'] if survey['revenue'] not in [None,''] else 0
            projectstats.expense = survey['expense'] if survey['expense'] not in [None,''] else 0
            projectstats.incidence = survey['incidence'] if survey['incidence'] not in [None,''] else 0
            projectstats.median_LOI = survey['median_LOI'] if survey['median_LOI'] not in [None,''] else 0
            projectstats.margin = survey['margin'] if survey['margin'] in [None,''] else 0
            user_bulk_update_list.append(projectstats)
        except:
            pass
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        yield_results = list(executor.map(parellel_surveys_stats_update, respondent_details))
    ProjectGroupStatsCalculations.objects.bulk_update(user_bulk_update_list,['total_visits','starts','internal_terminate','incompletes','completes','terminates','quota_full','security_terminate','complete_rejected_by_client','client_rejected','expense','revenue','incidence','median_LOI','margin'])
    return "Success"