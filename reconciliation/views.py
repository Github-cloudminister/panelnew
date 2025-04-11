from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from Invoice.models import DraftInvoice
from Logapp.views import project_reconciliation_log
from Supplier_Final_Ids_Email.models import *
from Surveyentry.models import *
from Project.models import *
from automated_email_notifications.project_custom_functions import update_status
from .models import *

# third_party module imports
from knox.auth import TokenAuthentication
import datetime
import asyncio


class ReconciliationView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def put(self, request, project_number):
        detail_rid = request.data['rids']

        try:
            project_obj = Project.objects.get(project_number = project_number)
            if project_obj.project_status != 'Closed':
                return Response({'error':'Either close this Survey or it has been reconciled already...!'}, status=status.HTTP_400_BAD_REQUEST)
            
            project_obj.project_revenue_month = datetime.date.today().month
            project_obj.project_revenue_year = datetime.date.today().year
            project_obj.project_status = "Reconciled"
            project_obj.save()
            SupplierIdsMarks_obj = SupplierIdsMarks.objects.create(project = project_obj, reconciled_by = request.user)

            respondent_data = RespondentDetail.objects.filter(project_number=project_number)
            for respondent in respondent_data:
                try:
                    reconcile = RespondentReconcilation(respondent=respondent, verified='1', previous_status=respondent.resp_status, previous_final_detailed_reason = respondent.final_detailed_reason, verified_by = request.user)
                    reconcile.save()
                except:
                    pass
                    
                try:
                    if respondent.respondenturldetail.RID in detail_rid:
                        respondent.final_detailed_reason='Accounted'

                        #********************** Temporary Comment this code *****************************
                        # if respondent.resp_status == '4':
                        #     respondent.final_detailed_reason='Accounted'
                        # else:
                        #     respondent.final_detailed_reason='Not Accounted'
                        #     respondent.resp_status='9'
                        #********************** Temporary Comment this code *****************************
                        respondent.resp_status='4'
                        respondent.save()

                    else:
                        if respondent.resp_status == '4':
                            respondent.resp_status='8'
                            respondent.final_detailed_reason='RID rejected by client'
                            respondent.save()

                except Exception as e:
                    if respondent.resp_status == '4':
                        respondent.resp_status='8'
                        respondent.final_detailed_reason='RID rejected by client'
                        respondent.save()
            
            update_status(project_obj.id, "Reconciled", action='change-project-status',user=request.user)
            project_reconciliation_log(project_obj.id,True,'',request.user)
            # CREATE THIS TABLE WHENEVER PROJECT GOES TO RECONCILED STATUS FOR FUTURE RECONCILIATION APPROVAL BY THE OUR EMPLOYEE
            return Response({'Success':'Project Reconciled successfully'}, status=status.HTTP_200_OK)
                
        except Exception as e:
            project_reconciliation_log('',False,f"{project_number}-{e}",request.user)
            return Response({'error':'Something went wrong. Please try again!'}, status=status.HTTP_400_BAD_REQUEST)


class VerifyReconciliationRIDDataView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self,request, project_number):
        rid_details = request.data['rids']

        respondent_data = RespondentDetail.objects.filter(project_number = project_number,respondenturldetail__RID__in = rid_details)
        respondent_data2 = respondent_data.filter(project_number = project_number).values_list('respondenturldetail__RID',flat=True)

        un_matching_data_2 = list(set(rid_details).symmetric_difference(set(respondent_data2)))
        un_match_data_count = len(un_matching_data_2)
        msg = f"You have {len(un_matching_data_2)} unmatch rids"
        un_match_data = un_matching_data_2
        total_rids = len(rid_details)
        match_data_count = respondent_data2.count()
        return Response({"un_match_count":un_match_data_count,"msg":msg,"un_match_data":un_match_data,"match_count":match_data_count,"total_rids":total_rids}, status=status.HTTP_200_OK)


class RevertReconciliationView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def post(self, request, *args, **kwargs):
        project_number=request.data.get('project_number')
        if not project_number:
            return Response({'error':'Project number is not available.'}, status=status.HTTP_406_NOT_ACCEPTABLE)
        project_obj = Project.objects.filter(project_number=project_number, project_status__in=['Reconciled','ReadyForAudit','ReadyForInvoice'])

        if not project_obj:
            return Response({'error': 'Project is not reconciled...!'}, status=status.HTTP_400_BAD_REQUEST)
        
        project_obj.update(scrubproject = False)
        update_status(project_obj.first().id, 'Closed', action='change-project-status',user=request.user)

        resp_reconcilation = RespondentReconcilation.objects.filter(respondent__project_number=project_number)
        for resp_reconcilation_obj in resp_reconcilation:
            resp_reconcilation_obj.respondent.resp_status = resp_reconcilation_obj.previous_status
            resp_reconcilation_obj.respondent.final_detailed_reason = resp_reconcilation_obj.previous_final_detailed_reason
            resp_reconcilation_obj.respondent.save()

        #DELETE THE DRAFTINVOICE CREATED FOR THIS PROJECT
        DraftInvoice.objects.filter(project__project_number=project_number).delete()
        resp_reconcilation.delete()
        SupplierIdsMarks_obj = SupplierIdsMarks.objects.filter(project__project_number=project_number)
        SupplierIdsMarks_obj.delete()
        ProjectCPIApprovedManager.objects.filter(project__project_number = project_number).delete()
        return Response({'msg': 'Reconciliation reverted successfully...!','project_status':'Closed'}, status=status.HTTP_200_OK)
