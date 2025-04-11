# django imports
from django.db.models import Count, Sum, F, Q

# rest_framework imports
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# third_party module imports
from knox.auth import TokenAuthentication


# in-project imports
from SupplierInvoice.models import ProjectInvoicedApproved
from Surveyentry.models import *
from Project.models import *
from SupplierAPI.lucid_supplier_api.buyer_surveys import reconcile_lucid_survey
from Supplier_Final_Ids_Email.models import SupplierIdsMarks

# automated email notifications imports
from automated_email_notifications.supplier_final_ids_custom_functions import  ProjectClosureZeroCompletesNotificationEmailSend



# Create your views here.
class projectListForScrubView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        resp_data = RespondentDetailsRelationalfield.objects.filter(
            respondent__url_type='Live',
            project__scrubproject=False,
            project__project_status__in = ['Invoiced'],
            project__project_number__in = list(ProjectInvoicedApproved.objects.filter(project_invoice_status = '3').values_list('project__project_number',flat=True))
            ).values(
                project_number=F('project__project_number')
                ).annotate(
                    customer_name=F('project__project_customer__cust_org_name'),
                    reconciled_date=F('project__supplieridsmarks__reconciled_date'),
                    completes=Count('respondent__id',
                                    filter=Q(respondent__resp_status = '4')),
                                    client_rejects=Count('respondent__id', filter=Q(respondent__resp_status = '8'))
        ).order_by('project__supplieridsmarks__reconciled_date')

        return Response(resp_data, status=status.HTTP_200_OK)


class SupplierCompleteCountsView(APIView):
    def get(self,request,*args,**kwargs):
        project_number = [request.GET.get('project_number',None)]
        resp_obj = RespondentDetail.objects.select_related('respondentdetailsrelationalfield').filter(project_number__in = project_number, resp_status__in = [4,8,9], url_type = 'Live')
        resp_obj = resp_obj.values(
                'respondentdetailsrelationalfield__project_group_supplier__id',
                'respondentdetailsrelationalfield__source__supplier_name',
                'project_number',
                'project_group_number') \
                .annotate(
                    revenue = Sum('project_group_cpi',filter=Q(resp_status__in = [4,9])),
                    expense = Sum('supplier_cpi',filter=Q(resp_status = 4)),
                    completes = Count('project_number', filter=Q(resp_status = 4)),
                    completes_not_considered = Count('project_number', filter=Q(resp_status = 9)), 
                    client_rejected = Count('project_number', filter=Q(resp_status = 8)),
                    pvprejected = Count('project_number', filter=Q(resp_status = 9))
                ).order_by('project_group_number')

        return Response({'data':resp_obj}, status=status.HTTP_200_OK)


class SupplierIdRejectedView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data = request.data
        project_number = data.get('project_number')
        final_ids_available_date = data.get('final_ids_available_date')
        supplier_data = data.get('supplier_data')

        try:
            ProjectInvoicedApproved.objects.get(project__project_number = project_number,project_invoice_status = '3')
        except:
            return Response({'error':'Invoice Auditing Not Approved'}, status= status.HTTP_400_BAD_REQUEST)

        if ((project_number == None or project_number == '') or (final_ids_available_date == None or final_ids_available_date == '')):
            return Response({'error':'Some of the data are missing. Please send all required data. '}, status= status.HTTP_404_NOT_FOUND)
        
        project_scrubbed = Project.objects.filter(project_number = project_number, scrubproject = False)
        if not(project_scrubbed.exists()):
            return Response({'error':'This project is already scrubbed.'}, status= status.HTTP_404_NOT_FOUND)
        
        non_scrub_proj_supplier_id_list = []
        scrub_proj_supplier_id_list = []
        for i in supplier_data:
            try:
            # if True:
                progrp_supp = ProjectGroupSupplier.objects.get(id=i['Supplier_id'])
                resp_relationalfield_obj = RespondentDetailsRelationalfield.objects.filter(project_group_supplier=progrp_supp, respondent__url_type="Live", respondent__resp_status="4")

                count_resp_relationalfield = resp_relationalfield_obj.count()
                if int(i['Completes_rejected']) <= count_resp_relationalfield:
                    for resp_relationalfield in resp_relationalfield_obj.order_by('?')[:int(i['Completes_rejected'])]:
                        resp_relationalfield.respondent.supplier_id_rejected = True
                        resp_relationalfield.respondent.resp_status = "9"
                        resp_relationalfield.respondent.final_detailed_reason = "Manual Complete Rejected"
                        resp_relationalfield.respondent.save()
                    
                    scrub_proj_supplier_id_list.append(i['Supplier_id'])

                    if progrp_supp.supplier_org.supplier_url_code == "lucid":
                        reconcile_lucid_survey(progrp_supp)
                    # ********** END::Doing Reconciled lucid supplier status ************
                else:
                    non_scrub_proj_supplier_id_list.append(i['Supplier_id'])
            except:
                non_scrub_proj_supplier_id_list.append(i['Supplier_id'])   
                
        project_scrubbed.update(scrubproject = True)  
        
        scrub_obj = SupplierIdsMarks.objects.filter(project__project_number = project_number)
        if not scrub_obj.exists():
            project_obj = Project.objects.get(project_number = project_number)
            scrub_obj = SupplierIdsMarks.objects.create(project = project_obj, reconciled_by = request.user, scrubbed = True, final_ids_available_by = final_ids_available_date, scrubbed_date = timezone.now(),scrubbed_by = request.user,supplier_ids_approval = True,supplier_ids_approval_date = timezone.now().date(),supplier_ids_approved_by = request.user)
        else:
            scrub_obj.update(scrubbed = True, final_ids_available_by = final_ids_available_date, scrubbed_date = timezone.now(),scrubbed_by = request.user,supplier_ids_approval = True,supplier_ids_approval_date = timezone.now().date(),supplier_ids_approved_by = request.user)
        
        ProjectClosureZeroCompletesNotificationEmailSend(project_number.split(','))
        return Response({'message':'Supplier Id Rejected.!','non_scrub_proj_supplier_id_list':non_scrub_proj_supplier_id_list,'scrub_proj_supplier_id_list':scrub_proj_supplier_id_list}, status=status.HTTP_200_OK)


class ProjectSupplierRowCreateApi(APIView):

    def post(self,request):

        project_number = request.data['project_number']
        
        if project_number not in ['', None]:
            supplier_invoice_row_obj = ProjectClosureZeroCompletesNotificationEmailSend(project_number)
            return Response({"message":"Supplier row create successfully..!"}, status=status.HTTP_200_OK)
        else:
            return Response({"error":"Project number is required..!"}, status=status.HTTP_400_BAD_REQUEST)

                              
class revertScrubIdsView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        project_number = request.GET.get('project_number')
        project_list_obj = SupplierIdsMarks.objects.filter(project__project_number = project_number)
        project_list_obj.delete()


        return Response({'message':f'Revert Done for project number {project_number}.'})


class projectCompleteCountsView(APIView):
    def get(self,request,*args,**kwargs):
        start_date = request.GET.get('start_date',None)
        projectlist = list(Project.objects.filter(invoice__invoice_date__gte = start_date).values_list('project_number', flat=True))
        r = RespondentDetail.objects.select_related('respondentdetailsrelationalfield').filter(project_number__in = projectlist, resp_status__in = [4,8,9]).values('project_number','respondentdetailsrelationalfield__project__project_customer__cust_org_name').annotate(revenue = Sum('project_group_cpi',filter=Q(respondentdetailsrelationalfield__respondent__resp_status__in = [4,9])), expense = Sum('supplier_cpi',filter=Q(respondentdetailsrelationalfield__respondent__resp_status = 4)), completes = Count('project_number', filter=Q(respondentdetailsrelationalfield__respondent__resp_status = 4)), client_rejected = Count('project_number', filter=Q(respondentdetailsrelationalfield__respondent__resp_status = 8)), pvprejected = Count('project_number', filter=Q(respondentdetailsrelationalfield__respondent__resp_status = 9)))

        return Response({'data':r}, status=status.HTTP_200_OK)
    



class SubSupplierProjectListForScrubView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        resp_data = RespondentDetailsRelationalfield.objects.filter(
            source__supplier_type__in = ['5'],
            respondent__url_type = 'Live',
            project__scrubproject = True,
            project__ad_scrubproject = False,
            project__project_status__in = ['Invoiced'],
            project__project_number__in = list(ProjectInvoicedApproved.objects.filter(project_invoice_status = '3').values_list('project__project_number',flat=True))
            ).values(
                project_number = F('project__project_number')
                ).annotate(
                    customer_name = F('project__project_customer__cust_org_name'),
                    reconciled_date = F('project__supplieridsmarks__reconciled_date'),
                    completes = Count('respondent__id',
                                    filter=Q(respondent__resp_status = '4')),
                                    client_rejects=Count('respondent__id', filter=Q(respondent__resp_status = '8'))
        )

        return Response(resp_data, status=status.HTTP_200_OK)


class SubSupplierCompleteCountsView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self,request,*args,**kwargs):
        project_number = [request.GET.get('project_number',None)]

        resp_obj = RespondentProjectGroupSubSupplier.objects.select_related('respondent').filter(respondent__project_number__in = project_number, respondent__resp_status__in = [4,8,9], respondent__url_type = 'Live')
        resp_obj = resp_obj.values(
                'project_group_sub_supplier__id',
                'project_group_sub_supplier__sub_supplier_org__sub_supplier_name',
                'respondent__project_number',
                'respondent__project_group_number'
                ) \
                .annotate(
                    revenue = Sum('respondent__project_group_cpi',filter=Q(respondent__resp_status__in = [4,9])),
                    expense = Sum('respondent__supplier_cpi',filter=Q(respondent__resp_status = 4)),
                    completes = Count('respondent__project_number', filter=Q(respondent__resp_status = 4)),
                    completes_not_considered = Count('respondent__project_number', filter=Q(respondent__resp_status = 9)), 
                    client_rejected = Count('respondent__project_number', filter=Q(respondent__resp_status = 8)),
                    pvprejected = Count('respondent__project_number', filter=Q(respondent__resp_status = 9))
                )

        return Response({'data':resp_obj}, status=status.HTTP_200_OK)
    


class SubSupplierIdRejectedView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        data = request.data
        project_number = data.get('project_number')
        final_ids_available_date = data.get('final_ids_available_date')
        sub_supplier_data = data.get('sub_supplier_data')

        try:
            ProjectInvoicedApproved.objects.get(project__project_number = project_number,project_invoice_status = '3')
        except:
            return Response({'error':'Invoice Auditing Not Approved'}, status= status.HTTP_400_BAD_REQUEST)

        if ((project_number == None or project_number == '') or (final_ids_available_date == None or final_ids_available_date == '')):
            return Response({'error':'Some of the data are missing. Please send all required data. '}, status= status.HTTP_404_NOT_FOUND)
        
        project_scrubbed = Project.objects.filter(project_number = project_number, scrubproject = True)
        if not(project_scrubbed.exists()):
            return Response({'error':'This project is already scrubbed.'}, status= status.HTTP_404_NOT_FOUND)
        
        non_scrub_proj_supplier_id_list = []
        scrub_proj_supplier_id_list = []
        for i in sub_supplier_data:
            try:
            # if True:
                progrp_sub_supp = ProjectGroupSubSupplier.objects.get(id=i['Sub_Supplier_id'])
                resp_proj_grp_sub_supp_obj = RespondentProjectGroupSubSupplier.objects.filter(project_group_sub_supplier=progrp_sub_supp, respondent__url_type="Live", respondent__resp_status="4")

                count_resp_proj_grp_sub_supp = resp_proj_grp_sub_supp_obj.count()
                if int(i['Completes_rejected']) <= count_resp_proj_grp_sub_supp:
                    for resp_prj_grp_sub_supplier in resp_proj_grp_sub_supp_obj.order_by('?')[:int(i['Completes_rejected'])]:
                        resp_prj_grp_sub_supplier.respondent.supplier_id_rejected = True
                        resp_prj_grp_sub_supplier.respondent.resp_status = "9"
                        resp_prj_grp_sub_supplier.respondent.final_detailed_reason = "Manual Complete Rejected"
                        resp_prj_grp_sub_supplier.respondent.save()
                    
                    scrub_proj_supplier_id_list.append(i['Sub_Supplier_id'])

                    # if progrp_supp.supplier_org.supplier_url_code == "lucid":
                    #     reconcile_lucid_survey(progrp_supp)
                    # ********** END::Doing Reconciled lucid supplier status ************
                else:
                    non_scrub_proj_supplier_id_list.append(i['Sub_Supplier_id'])
            except Exception as e:
                non_scrub_proj_supplier_id_list.append(i['Sub_Supplier_id'])   
                
        project_scrubbed.update(ad_scrubproject = True)  
        
        # scrub_obj = SupplierIdsMarks.objects.filter(project__project_number = project_number)
        # if not scrub_obj.exists():
        #     project_obj = Project.objects.get(project_number = project_number)
        #     scrub_obj = SupplierIdsMarks.objects.create(project = project_obj, reconciled_by = request.user, scrubbed = True, final_ids_available_by = final_ids_available_date, scrubbed_date = timezone.now(),scrubbed_by = request.user,supplier_ids_approval = True,supplier_ids_approval_date = timezone.now().date(),supplier_ids_approved_by = request.user)
        # else:
        #     scrub_obj.update(scrubbed = True, final_ids_available_by = final_ids_available_date, scrubbed_date = timezone.now(),scrubbed_by = request.user,supplier_ids_approval = True,supplier_ids_approval_date = timezone.now().date(),supplier_ids_approved_by = request.user)
        
        # ProjectClosureZeroCompletesNotificationEmailSend(project_number.split(','))
        return Response({'message':'Supplier Id Rejected.!','non_scrub_proj_supplier_id_list':non_scrub_proj_supplier_id_list,'scrub_proj_supplier_id_list':scrub_proj_supplier_id_list}, status=status.HTTP_200_OK)