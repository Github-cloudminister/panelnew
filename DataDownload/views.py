from io import BytesIO
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from django.http import HttpResponse
from django.db.models import Q, F, Case, Value, When
from knox.auth import TokenAuthentication
from rest_framework.views import APIView
from .serializers import ResearchDefenderDetailListSerializer, RespondentDetailSerializer, SuppliersMonthlyDetailListSerializer
from Surveyentry.models import *
from Supplier.models import SupplierOrganisation
from Customer.models import CustomerOrganization
from employee.models import EmployeeProfile
from Project.models import Project, ProjectGroup
from Questions.models import ParentQuestion

# third party apps
import csv,xlsxwriter, json

class RespondentProjectGroup(generics.ListAPIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    filterset_fields = ['project_group_number', 'url_type']

    queryset = RespondentDetail.objects.all()
    serializer_class = RespondentDetailSerializer


class SideBarCountsView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        employee_obj = EmployeeProfile.objects.filter(is_superuser=False, user_type = '1').exclude(emp_type = '10').count()
        supplier_obj = SupplierOrganisation.objects.count()
        customer_obj = CustomerOrganization.objects.count()
        project_obj = Project.objects.filter(project_status='Live').count()
        all_project_obj = Project.objects.count()
        questions = ParentQuestion.objects.count()
        client_supplier_survey_obj = ProjectGroup.objects.filter(
            project__project_customer__customer_url_code__in = ['toluna','zamplia','sago'],project_group_status = 'Live').count()

        #Counts of each module in database
        data = [{
            'Employees': employee_obj,
            'Suppliers': supplier_obj,
            'Customers': customer_obj,
            'Live_Projects': project_obj,
            'Total_Projects': all_project_obj,
            'Total_Questions': questions,
            'client_supplier_surveys': client_supplier_survey_obj
            }]

        return Response(data)


class ProjectGroupDataAPIView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_group_num):

        resp_obj = RespondentDetail.objects.filter(Q(project_group_number = project_group_num) | Q(project_number = project_group_num))

        if len(resp_obj) > 0:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=' + str(project_group_num) + '.csv'
            writer = csv.writer(response)
            header = ["Project ID", "Project Name", "Group ID", "Group Name", "Vendor Name", "Vendor User ID", "RID", 
                                    "Resp Status", "Detailed Reason", "Client CPI", "Supplier CPI", "Start Date", "End Date", "Reconciliation Date", "LOI",  "IP", "Device", "URL Type","Last page Seen"]
            count = 0
            for resp in resp_obj:
                try:
                    project_num = resp.project_number
                except:
                    project_num = 'N/A'
                try:
                    project_name = Project.objects.get(project_number=resp.project_number).project_name
                except:
                    project_name = 'None'
                try:
                    project_group_no = resp.project_group_number
                except:
                    project_group_no = 'N/A'
                try:
                    project_group_name = ProjectGroup.objects.get(project_group_number=resp.project_group_number).project_group_name
                except:
                    project_group_name = 'None'
                try:
                    supplier_name = SupplierOrganisation.objects.get(id=resp.source).supplier_name
                except:
                    supplier_name = 'Internal'
                try:
                    pid = resp.respondenturldetail.pid
                except:
                    pid = 'N/A'
                try:
                    rid = resp.respondenturldetail.RID
                except:
                    rid = 'N/A'
                try:
                    resp_status = resp.get_resp_status_display()
                except:
                    resp_status = 'N/A'
                try:
                    Detailed_Reason = resp.final_detailed_reason
                except:
                    Detailed_Reason = ''
                try:
                    client_cpi = resp.project_group_cpi
                except:
                    client_cpi = 0
                try:
                    supplier_cpi = resp.supplier_cpi
                except:
                    supplier_cpi = 0
                try:
                    start_time = resp.start_time
                except:
                    start_time = 'None'
                try:
                    end_time = resp.end_time
                except:
                    end_time = 'None'
                try:
                    reconciliation_time = resp.respondentreconcilation.verified_at
                except:
                    reconciliation_time = 'None'
                try:
                    duration = resp.duration
                except:
                    duration = '0'
                try:
                    ip_address = resp.respondenturldetail.ip_address
                except:
                    ip_address = 'N/A'
                try:
                    device = resp.respondentdevicedetail
                    device_name = 'Bot'
                    if device.mobile:
                        device_name = 'Mobile'
                    if device.tablet:
                        device_name = 'Tablet'
                    if device.desktop:
                        device_name = 'Desktop/Laptop'
                except:
                    device_name = 'None'

                try:
                    url_type = resp.url_type
                except:
                    url_type = 'N/A'

                try:
                    last_page_seen = resp.respondentpagedetails.last_page_seen
                except:
                    last_page_seen = 'N/A'
                    
                content = [project_num, project_name, project_group_no, project_group_name, supplier_name,
                                        pid, rid, resp_status, Detailed_Reason, client_cpi, supplier_cpi, start_time, end_time, reconciliation_time, duration, ip_address, device_name, url_type,last_page_seen]
                if count == 0:
                    writer.writerow(header)
                    count += 1
                writer.writerow(content)
            return response
        else:
            return Response({'error': 'Survey Data is not available against this Project Group Number'}, status=status.HTTP_400_BAD_REQUEST)



class CustSuppQuestionDataDownload(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        customer_id = request.GET.get('customer')
        supplier_id = request.GET.get('supplier')

        if start_date in ('',None) or end_date in ('',None):
            return Response({'message': 'Please pass start_date and end_date both'}, status=status.HTTP_400_BAD_REQUEST)

        if customer_id in ('',None) and supplier_id in ('',None):
            return Response({'message': 'Please pass either customer or supplier'}, status=status.HTTP_400_BAD_REQUEST)

        if customer_id:
            resp_obj = RespondentDetail.objects.select_related('respondentdetailsrelationalfield','respondentdetailsrelationalfield__project','respondentdetailsrelationalfield__project__project_customer').filter(respondentdetailsrelationalfield__project__project_customer__id=customer_id, end_time_day__gte=start_date, end_time_day__lte=end_date)
        elif supplier_id:
            resp_obj = RespondentDetail.objects.select_related('respondentdetailsrelationalfield','respondentdetailsrelationalfield__project','respondentdetailsrelationalfield__project__project_customer').filter(respondentdetailsrelationalfield__source__id=supplier_id, end_time_day__gte=start_date, end_time_day__lte=end_date)

        if len(resp_obj) > 0:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=' + 'Suplplier_report' + '_Suppplier_data' + '.csv' if supplier_id else 'attachment; filename=' + 'Suplplier_report' + '_Client_Data' + '.csv'
            writer = csv.writer(response)
            header = ["Project ID", "Project Name", "Group ID", "Group Name", "Vendor Name", "Vendor User ID", "Client User ID", 
                                    "Resp Status", "Detailed Reason", "Client CPI", "Supplier CPI", "Start Date", "End Date", "Reconciliation Date", "LOI",  "IP", "Device", "URL Type","Last page Seen", "RID", "PID", "URL_Type", "Survey Number"]
            count = 0
            
            for resp in resp_obj:
                try:
                    project_num = resp.project_number
                except:
                    project_num = 'N/A'
                try:
                    project_name = Project.objects.get(project_number=resp.project_number).project_name
                except:
                    project_name = 'None'
                try:
                    project_group_no = resp.project_group_number
                except:
                    project_group_no = 'N/A'
                try:
                    project_group_name = ProjectGroup.objects.get(project_group_number=resp.project_group_number).project_group_name
                except:
                    project_group_name = 'None'
                try:
                    supplier_name = SupplierOrganisation.objects.get(id=resp.source).supplier_name
                except:
                    supplier_name = 'Internal'
                try:
                    pid = resp.respondenturldetail.pid
                except:
                    pid = 'N/A'
                try:
                    rid = resp.respondenturldetail.RID
                except:
                    rid = 'N/A'
                try:
                    resp_status = resp.get_resp_status_display()
                except:
                    resp_status = 'N/A'
                try:
                    Detailed_Reason = resp.final_detailed_reason
                except:
                    Detailed_Reason = ''
                try:
                    client_cpi = resp.project_group_cpi
                except:
                    client_cpi = 0
                try:
                    supplier_cpi = resp.supplier_cpi
                except:
                    supplier_cpi = 0
                try:
                    start_time = resp.start_time.date()
                except:
                    start_time = 'None'
                try:
                    end_time = resp.end_time.date()
                except:
                    end_time = 'None'
                try:
                    reconciliation_time = resp.respondentreconcilation.verified_at.date()
                except:
                    reconciliation_time = 'None'
                try:
                    duration = resp.duration
                except:
                    duration = '0'
                try:
                    ip_address = resp.respondenturldetail.ip_address
                except:
                    ip_address = 'N/A'
                try:
                    device = resp.respondentdevicedetail
                    device_name = 'Bot'
                    if device.mobile:
                        device_name = 'Mobile'
                    if device.tablet:
                        device_name = 'Tablet'
                    if device.desktop:
                        device_name = 'Desktop/Laptop'
                except:
                    device_name = 'None'

                try:
                    url_type = resp.url_type
                except:
                    url_type = 'N/A'

                try:
                    last_page_seen = resp.respondentpagedetails.last_page_seen
                except:
                    last_page_seen = 'N/A'
                
                try:
                    rid = resp.respondenturldetail.RID
                except:
                    rid = 'N/A'
                try:
                    pid = resp.respondenturldetail.pid
                except:
                    pid = 'N/A'
                try:
                    url_type = resp.get_url_type_display()
                except:
                    url_type = 'N/A'
                try:
                    project_group_no = resp.project_group_number
                except:
                    project_group_no = 'N/A'
                    
                content = [project_num, project_name, project_group_no, project_group_name, supplier_name,
                                        pid, rid, resp_status, Detailed_Reason, client_cpi, supplier_cpi, start_time, end_time, reconciliation_time, duration, ip_address, device_name, url_type,last_page_seen, rid, pid, url_type, project_group_no]

                projectgroup_prescreener_data = ProjectGroupPrescreenerDataStore.objects.filter(respondent=resp)
                answer_list = []
                for question in projectgroup_prescreener_data:

                    # ******************** Dynamically add question in Header *************************
                    question_text = question.translated_question_id.parent_question.parent_question_text
                    if question_text in header:
                        pass
                    else:
                        header.append(question.translated_question_id.parent_question.parent_question_text)
                        question_type = question.translated_question_id.parent_question.parent_question_type
                        if question_type == "OE":
                            header.append("Duplicate Ratio")
                    # ******************** End Dynamically add question in Header *************************

                    # ******************** Dynamically add answer in Content *************************
                    question_type = question.translated_question_id.parent_question.parent_question_type
                    if question_type == "MS":
                        answer_list = [answer.translated_answer for answer in question.selected_options.all()]
                        converted_answer = ' | '.join(map(str, answer_list))
                    elif question_type == "SS":
                        answer_list = [answer.translated_answer for answer in question.selected_options.all()]
                        converted_answer = answer_list[0]
                    else:
                        converted_answer = question.received_response
                    content.append(converted_answer)
                    if question_type == "OE":
                        content.append(question.text_evalution_result)
                    # ********************END Dynamically add answer in Content *************************

                if count == 0:
                    writer.writerow(header)
                    count += 1
                writer.writerow(content)
            return response
        else:
            return Response({'error': 'Invalid supplier/customer or start_date/end_date passed'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectGroupJsonDataAPIView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_group_num):

        project_rep_obj = RespondentDetail.objects.filter(
            project_group_number = project_group_num).only("project_number","url_type","project_group_number","project_group_cpi","supplier_cpi","resp_status","final_detailed_reason","start_time","end_time","duration","respondenturldetail__pid","respondenturldetail__RID","respondentreconcilation__verified_at","respondenturldetail__ip_address","respondenturldetail__end_ip_address","respondentdevicedetail", "respondentdetailsrelationalfield__source__supplier_name","respondentpagedetails__last_page_seen").values(
            "project_number","url_type","project_group_number","project_group_cpi","supplier_cpi","resp_status","final_detailed_reason","start_time","end_time","duration",sub_supplier_cpi = F("respondentprojectgroupsubsupplier__project_group_sub_supplier__cpi")
            ).annotate(Suppliername = F('respondentdetailsrelationalfield__source__supplier_name'),
                       PID = F('respondenturldetail__pid'), RID = F('respondenturldetail__RID'),
                       Ip = F('respondenturldetail__ip_address'), End_Ip = F('respondenturldetail__end_ip_address'),
                       last_seen = F("respondentpagedetails__last_page_seen"),
                       Device = Case(
                           When(respondentdevicedetail__mobile = True,then=Value('Mobile')),
                           When(respondentdevicedetail__tablet = True,then=Value('Tablet')),
                           When(respondentdevicedetail__desktop = True,then=Value('Desktop/Laptop'))
                       )
                       ).order_by('-id')

        return Response(project_rep_obj, status=status.HTTP_200_OK)
        
class ProjectDataAPIView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_number):

        project_rep_obj = RespondentDetail.objects.filter(project_number = project_number).only(
            "project_number",
            "source",
            "url_type",
            "project_group_number",
            "project_group_cpi",
            "supplier_cpi",
            "resp_status",
            "final_detailed_reason",
            "start_time",
            "end_time",
            "duration",
            "respondenturldetail__pid",
            "respondenturldetail__RID",
            "respondentpagedetails__last_page_seen",
            "respondentreconcilation__verified_at",
            "respondenturldetail__ip_address",
            "respondentdevicedetail"
        )
        if len(project_rep_obj) > 0:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=' + str(project_number) + '.csv'
            writer = csv.writer(response)
            header = ["Project ID", "Group ID", "Vendor Name", "Vendor User ID", "Client User ID", 
                                    "Resp Status", "Detailed Reason", "Client CPI", "Vendor CPI", "Start Date", "End Date", "Reconciliation Date", "LOI",  "IP", "Device", "URL Type","Last Page Seen"]
            count = 0
            for obj in project_rep_obj:
                try:
                    project_num = obj.project_number
                except:
                    project_num = 'N/A'
                try:
                    project_group_no = obj.project_group_number
                except:
                    project_group_no = 'N/A'
                try:
                    supplier_name = SupplierOrganisation.objects.get(id=obj.source).supplier_name
                except:
                    supplier_name = 'Internal'
                try:
                    pid = obj.respondenturldetail.pid
                except:
                    pid = 'N/A'
                try:
                    rid = obj.respondenturldetail.RID
                except:
                    rid = 'N/A'
                try:
                    resp_status = obj.get_resp_status_display()
                except:
                    resp_status = 'N/A'
                try:
                    Detailed_Reason = obj.final_detailed_reason
                except:
                    Detailed_Reason = ''
                try:
                    client_cpi = obj.project_group_cpi
                except:
                    client_cpi = 0
                try:
                    supplier_cpi = obj.supplier_cpi
                except:
                    supplier_cpi = 0
                try:
                    start_time = obj.start_time
                except:
                    start_time = 'None'
                try:
                    end_time = obj.end_time
                except:
                    end_time = 'None'
                try:
                    reconciliation_time = obj.respondentreconcilation.verified_at
                except:
                    reconciliation_time = 'None'
                try:
                    duration = obj.duration
                except:
                    duration = '0'
                try:
                    ip_address = obj.respondenturldetail.ip_address
                except:
                    ip_address = 'N/A'
                try:
                    device = obj.respondentdevicedetail
                    device_name = 'Bot'
                    if device.mobile:
                        device_name = 'Mobile'
                    if device.tablet:
                        device_name = 'Tablet'
                    if device.desktop:
                        device_name = 'Desktop/Laptop'
                except:
                    device_name = 'None'

                try:
                    url_type = obj.url_type
                except:
                    url_type = 'N/A'

                try:
                    last_page_seen = obj.respondentpagedetails.last_page_seen
                except:
                    last_page_seen = 'N/A'
                    
                content = [project_num, project_group_no, supplier_name,
                                        pid, rid, resp_status, Detailed_Reason, client_cpi, supplier_cpi, start_time, end_time, reconciliation_time, duration, ip_address, device_name, url_type,last_page_seen]
                if count == 0:
                    writer.writerow(header)
                    count += 1
                writer.writerow(content)
            return response
        else:
            return Response({'error': 'Invalid project Number..!'}, status=status.HTTP_400_BAD_REQUEST)


class ProjectDataApiView_V2(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_number):
        if request.GET.get('status') == "99":
            project_rep_obj = RespondentDetail.objects.filter(
            project_number = project_number).only("project_number","source","url_type","project_group_number","project_group_cpi","supplier_cpi","resp_status","final_detailed_reason","start_time","end_time","duration","respondenturldetail__pid","respondenturldetail__RID","respondentreconcilation__verified_at","respondenturldetail__ip_address","respondenturldetail__end_ip_address","respondentdevicedetail", "respondentdetailsrelationalfield__source__supplier_name").values(
            "project_number","source","url_type","project_group_number","project_group_cpi","supplier_cpi","resp_status","final_detailed_reason","start_time","end_time","duration"
            ).annotate(Suppliername = F('respondentdetailsrelationalfield__source__supplier_name'),
                       PID = F('respondenturldetail__pid'), RID = F('respondenturldetail__RID'),
                       Ip = F('respondenturldetail__ip_address'), End_Ip = F('respondenturldetail__end_ip_address'))
        else:
            project_rep_obj = RespondentDetail.objects.filter(
                project_number = project_number,resp_status__in = list(map(str,request.GET.get('status')))).only("project_number","source","url_type","project_group_number","project_group_cpi","supplier_cpi","resp_status","final_detailed_reason","start_time","end_time","duration","respondenturldetail__pid","respondenturldetail__RID","respondentreconcilation__verified_at","respondenturldetail__ip_address","respondentdevicedetail", "respondentdetailsrelationalfield__source__supplier_name").values(
                "project_number","source","url_type","project_group_number","project_group_cpi","supplier_cpi","resp_status","final_detailed_reason","start_time","end_time","duration"
                ).annotate(Suppliername = F('respondentdetailsrelationalfield__source__supplier_name'),
                        PID = F('respondenturldetail__pid'), RID = F('respondenturldetail__RID'),
                        Ip = F('respondenturldetail__ip_address'), End_Ip = F('respondenturldetail__end_ip_address'))
        return Response(project_rep_obj, status=status.HTTP_200_OK)


class ProjectGroupQuestionDataAPIView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_group_number):

        group_resp_obj = RespondentDetail.objects.filter(project_group_number = project_group_number).order_by('id')
        
        if len(group_resp_obj) > 0:

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=' + str(project_group_number) + '.csv'
            writer = csv.writer(response)

            header = ["RID", "PID", "URL_Type", "Survey Number", "Vendor Name", "Resp status"]
            count = 0
            
            # ******************** Dynamically add question in Header *************************
            for obj in group_resp_obj:
                projectgroup_prescreener_data = ProjectGroupPrescreenerDataStore.objects.filter(respondent=obj).order_by('translated_question_id')
                
                for question in projectgroup_prescreener_data:
                    
                    question_text = question.translated_question_id.parent_question.parent_question_text
                    if question_text in header:
                        pass
                    else:
                        header.append(question.translated_question_id.parent_question.parent_question_text)
                        question_type = question.translated_question_id.parent_question.parent_question_type
                        if question_type == "OE":
                            header.append("Duplicate Ratio")
            # ******************** End Dynamically add question in Header *************************
                    
            for obj in group_resp_obj:

                try:
                    rid = obj.respondenturldetail.RID
                except:
                    rid = 'N/A'
                try:
                    pid = obj.respondenturldetail.pid
                except:
                    pid = 'N/A'
                try:
                    url_type = obj.get_url_type_display()
                except:
                    url_type = 'N/A'
                try:
                    project_group_no = obj.project_group_number
                except:
                    project_group_no = 'N/A'
                try:
                    supplier_name = SupplierOrganisation.objects.get(id=obj.source).supplier_name
                except:
                    supplier_name = 'Internal'
                try:
                    resp_status = obj.get_resp_status_display()
                except:
                    resp_status = 'N/A'
             
                content = [rid, pid, url_type, project_group_no, supplier_name, resp_status,]

                # ******************** Dynamically add answer in Content *************************
                projectgroup_prescreener_data = ProjectGroupPrescreenerDataStore.objects.filter(respondent=obj).order_by('translated_question_id')
                answer_list = []
                for question in projectgroup_prescreener_data:
                    
                    question_type = question.translated_question_id.parent_question.parent_question_type
                    if question_type == "MS":
                        answer_list = [answer.translated_answer for answer in question.selected_options.all()]
                        converted_answer = ' | '.join(map(str, answer_list))
                    elif question_type == "SS":
                        answer_list = [answer.translated_answer for answer in question.selected_options.all()]
                        converted_answer = answer_list[0]
                    else:
                        converted_answer = question.received_response
                    content.append(converted_answer)
                    if question_type == "OE":
                        content.append(question.text_evalution_result)
                
                if count == 0:
                    writer.writerow(header)
                    count += 1
                writer.writerow(content)
            return response
        else:
            return Response({'error': 'Survey Data is not available against this Project Group Number'}, status=status.HTTP_400_BAD_REQUEST)


class ResearchDefenderDataAPIView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_group_num, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=research_defender_' + str(project_group_num) + '.csv'
        writer = csv.writer(response)
        header = ["Project ID", "Survey Number", "Vendor Name", "Vendor User ID", "Client User ID", "Resp Status", "Detailed Reason", "Start Date", "End Date", "IP", "Device", "URL Type"]

        research_defender_queryset = RespondentResearchDefenderDetail.objects.filter(Q(respondent__project_group_number = project_group_num) | Q(respondent__project_number = project_group_num)).order_by('-respondent__id')

        count = 0
        # ******************** Dynamically add question in Header *************************
        for research_defender_obj in research_defender_queryset:
            research_defender_resp_obj = research_defender_obj.researchdefenderresponsedetail

            projectgroup_prescreener_data = ProjectGroupPrescreenerDataStore.objects.filter(respondent=research_defender_obj.respondent, translated_question_id__parent_question__parent_question_type = "OE").order_by('id')

            for question in projectgroup_prescreener_data:
                    
                    question_text = question.translated_question_id.parent_question.parent_question_text
                    if question_text in header:
                        pass
                    else:
                        header.append(question.translated_question_id.parent_question.parent_question_text)

        # ******************** End Dynamically add question in Header *************************
        header.extend(["Similarity Text Length", "Similarity Text", "Detected Language Score", "Detected Language", "Pasted Response Score", "Pasted Response", "Typed Response Time", "Page View Time", "Garbage Words Score", "Garbage Words", "Profanity Check Score", "Profanity Check", "Engagement Score", "Composite Score"])

        for research_defender_obj in research_defender_queryset:
            research_defender_resp_obj = research_defender_obj.researchdefenderresponsedetail

            try:
                project_num = research_defender_obj.respondent.project_number
            except:
                project_num = 'N/A'
            try:
                project_group_no = research_defender_obj.respondent.project_group_number
            except:
                project_group_no = 'N/A'
            try:
                supplier_name = SupplierOrganisation.objects.get(id=research_defender_obj.respondent.source).supplier_name
            except:
                supplier_name = 'Internal'
            try:
                pid = research_defender_obj.respondent.respondenturldetail.pid
            except:
                pid = 'N/A'
            try:
                rid = research_defender_obj.respondent.respondenturldetail.RID
            except:
                rid = 'N/A'
            try:
                resp_status = research_defender_obj.respondent.get_resp_status_display()
            except:
                resp_status = 'N/A'
            try:
                Detailed_Reason = research_defender_obj.respondent.final_detailed_reason
            except:
                Detailed_Reason = ''
            try:
                start_time = research_defender_obj.respondent.start_time
            except:
                start_time = 'None'
            try:
                end_time = research_defender_obj.respondent.end_time
            except:
                end_time = 'None'
            try:
                ip_address = research_defender_obj.respondent.respondenturldetail.ip_address
            except:
                ip_address = 'N/A'
            try:
                device = research_defender_obj.respondent.respondentdevicedetail
                device_name = 'Bot'
                if device.mobile:
                    device_name = 'Mobile'
                if device.tablet:
                    device_name = 'Tablet'
                if device.desktop:
                    device_name = 'Desktop/Laptop'
            except:
                device_name = 'None'

            try:
                url_type = research_defender_obj.respondent.url_type
            except:
                url_type = 'N/A'
            
            content = [project_num, project_group_no, supplier_name, pid, rid, resp_status, Detailed_Reason, start_time, end_time, ip_address, device_name, url_type,]

            projectgroup_prescreener_data = ProjectGroupPrescreenerDataStore.objects.filter(respondent=research_defender_obj.respondent, translated_question_id__parent_question__parent_question_type = "OE").order_by('id')

            for question in projectgroup_prescreener_data:
                content.append(question.received_response)
            
            content.extend([
                research_defender_obj.researchdefenderresponsedetail.entered_similarity_text_length, # Similarity Text Length
                research_defender_obj.researchdefenderresponsedetail.similarity_text, # Similarity Text
                research_defender_obj.researchdefenderresponsedetail.language_detected_score, # Detected Language Score
                research_defender_obj.researchdefenderresponsedetail.language_detected, # Detected Language
                research_defender_obj.researchdefenderresponsedetail.pasted_response_score, # Pasted Response Score
                research_defender_obj.researchdefenderresponsedetail.pasted_response, # Pasted Response
                research_defender_obj.researchdefenderresponsedetail.typed_response_time, # Typed Response Time
                research_defender_obj.researchdefenderresponsedetail.page_view_time, # Page View Time
                research_defender_obj.researchdefenderresponsedetail.garbage_words_score, # Garbage Words Score
                research_defender_obj.researchdefenderresponsedetail.garbage_words, # Garbage Words
                research_defender_obj.researchdefenderresponsedetail.profanity_check_score, # Profanity Check Score
                research_defender_obj.researchdefenderresponsedetail.profanity_check, # Profanity Check
                research_defender_obj.researchdefenderresponsedetail.engagement_score, # Engagement Score
                research_defender_obj.researchdefenderresponsedetail.composite_score, # Composite Score
            ])

            if count == 0:
                writer.writerow(header)
                count += 1
            writer.writerow(content)
        return response



class SuppliersMonthlyDetailListAPI(generics.ListAPIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SuppliersMonthlyDetailListSerializer


    def get_queryset(self):
        supplier_ids = self.request.GET.get('supplier_ids')
        months = self.request.GET.get('months')
        year = self.request.GET.get('year')

        if not supplier_ids:
            return []

        resp_detail_qs = RespondentDetail.objects.filter(source__in=supplier_ids.split(','), resp_status='4')

        if months and year:
            months = months.split(',')
            resp_detail_qs = resp_detail_qs.filter(start_time__date__month__in=months, start_time__date__year=year)

        return resp_detail_qs



    def get(self, request):
        response = super().get(request)
        in_memory = BytesIO()
        workbook = xlsxwriter.Workbook(in_memory)
        worksheet = workbook.add_worksheet('Suppliers Data')

        column_incr = 0
        cell_format = workbook.add_format({'bold': True})

        head_columns = ['Supplier Name','Project No','Survey No','Project Status','PID','Start Time', 'End Time', 'Visitor Status']

        for column in head_columns:
            worksheet.set_column(column_incr, column_incr, 19)
            worksheet.write(0, column_incr, column, cell_format)
            column_incr+=1

        data_row_incr = 1
        for supplier_dict in response.data:
            supplier_dict = dict(supplier_dict)

            data_column_incr = 0
            worksheet.write(data_row_incr, data_column_incr, supplier_dict['supplier_name'])
            data_column_incr+=1
            worksheet.write(data_row_incr, data_column_incr, supplier_dict['project_number'])
            data_column_incr+=1
            worksheet.write(data_row_incr, data_column_incr, supplier_dict['survey_number'])
            data_column_incr+=1
            worksheet.write(data_row_incr, data_column_incr, supplier_dict['project_status'])
            data_column_incr+=1
            worksheet.write(data_row_incr, data_column_incr, supplier_dict['respondent_pid'])
            data_column_incr+=1
            worksheet.write(data_row_incr, data_column_incr, supplier_dict['resp_start_time'])
            data_column_incr+=1
            worksheet.write(data_row_incr, data_column_incr, supplier_dict['resp_end_time'])
            data_column_incr+=1
            worksheet.write(data_row_incr, data_column_incr, supplier_dict['resp_status'])
            data_column_incr+=1

            data_row_incr+=1
        
        workbook.close()

        response = HttpResponse(in_memory.getvalue(), content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=Suppliers\' Month-Year Wise Details.xlsx'

        return response



class ResearchDefenderDetailListAPI(generics.ListAPIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ResearchDefenderDetailListSerializer


    def get_queryset(self):
        research_defender_qs = RespondentResearchDefenderDetail.objects.all()

        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        if start_date and end_date:
            research_defender_qs = research_defender_qs.filter(created_at__gte=start_date, created_at__lte=end_date)

        return research_defender_qs
    

class ProjectGroupSubJsonDataApiView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_group_num):

        project_rep_obj = RespondentProjectGroupSubSupplier.objects.filter(
            respondent__project_group_number = project_group_num).only("respondent__project_number","respondent__url_type","respondent__project_group_number","respondent__project_group_cpi","respondent__supplier_cpi","respondent__resp_status","respondent__final_detailed_reason","respondent__start_time","respondent__end_time","respondent__duration","respondent__respondenturldetail__pid","respondent__respondenturldetail__RID","respondent__respondentreconcilation__verified_at","respondent__respondenturldetail__ip_address","respondent__respondentdevicedetail", "project_group_sub_supplier__sub_supplier_org__sub_supplier_name","respondent__respondentpagedetails__last_page_seen").values(
            project_number = F("respondent__project_number"),
            url_type = F("respondent__url_type"),
            project_group_number = F("respondent__project_group_number"),
            project_group_cpi = F("respondent__project_group_cpi"),
            supplier_cpi = F("respondent__supplier_cpi"),
            sub_supplier_cpi = F("project_group_sub_supplier__cpi"),
            resp_status = F("respondent__resp_status"),
            final_detailed_reason = F("respondent__final_detailed_reason"),
            start_time = F("respondent__start_time"),
            end_time = F("respondent__end_time"),
            duration = F("respondent__duration"),
            ).annotate(SubSuppliername = F('project_group_sub_supplier__sub_supplier_org__sub_supplier_name'),
                       PID = F('respondent__respondenturldetail__pid'), RID = F('respondent__respondenturldetail__RID'),
                       Ip = F('respondent__respondenturldetail__ip_address'), last_seen = F("respondent__respondentpagedetails__last_page_seen"),
                       Device = Case(
                           When(respondent__respondentdevicedetail__mobile = True,then=Value('Mobile')),
                           When(respondent__respondentdevicedetail__tablet = True,then=Value('Tablet')),
                           When(respondent__respondentdevicedetail__desktop = True,then=Value('Desktop/Laptop'))
                        )
            ).order_by('-id')
        if project_rep_obj.exists():
            return Response(project_rep_obj)
        else:
            return Response({'message': "No data found for the provided ProjectGroup-Number"}, status=status.HTTP_404_NOT_FOUND)