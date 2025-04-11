from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from Bid.models import *
from ClientSupplierAPIIntegration.TolunaClientAPI.models import *
from ClientSupplierInvoicePayment.models import *
from CompanyBankDetails.models import *
from Invoice.models import *
from Project.models import *
from Questions.models import *
from SupplierAPI.models import *
from SupplierInvoice.models import *
from Supplier_Final_Ids_Email.models import *
from Surveyentry.models import *
from employee.models import *


# Create your views here.
class Backupdata(APIView):

    def get(self, request):
        try:
            for i in Country.objects.all():
                i.save(using='secondary')
            for i in Language.objects.all():
                i.save(using='secondary')
            for i in Currency.objects.all():
                i.save(using='secondary')
            for i in EmployeeProfile.objects.all().order_by('id'):
                i.save(using='secondary')
            for i in CompanyDetails.objects.all():
                i.save(using='secondary')
            for i in CompanyInvoiceBankDetail.objects.all().order_by('id'):
                i.save(using='secondary')
            for i in CustomerOrganization.objects.all().order_by('id'):
                i.save(using='secondary')
            for i in ClientDBCountryLanguageMapping.objects.all():
                i.save(using='secondary')
            for i in LucidCountryLanguageMapping.objects.all():
                i.save(using='secondary')
            for i in ClientContact.objects.all():
                i.save(using='secondary')
            for i in ClientPaymentReceipt.objects.all():
                i.save(using='secondary')
            for i in Bid.objects.all():
                i.save(using='secondary')
            for i in BidRow.objects.all():
                i.save(using='secondary')
            for i in SupplierOrganisation.objects.all():
                i.save(using='secondary')
            for i in SupplierContact.objects.all():
                i.save(using='secondary')
            for i in SupplierBankDetails.objects.all():
                i.save(using='secondary')
            for i in SubSupplierOrganisation.objects.all():
                i.save(using='secondary')
            for i in SubSupplierContact.objects.all():
                i.save(using='secondary')
            for i in SupplierInvoicingDetails.objects.all():
                i.save(using='secondary')
            for i in supplierFinalIdsDeploy.objects.all():
                i.save(using='secondary')

            project_number = ProjectBackup.objects.filter(Backup_status='Pending').values_list('project__project_number', flat=True)

            for i in Project.objects.filter(project_number__in = project_number):
                i.save(using='secondary')
            for i in ProjectGroup.objects.filter(project__project_number__in = project_number):
                i.save(using='secondary')
            for i in ProjectGroupSupplier.objects.filter(project_group__project__project_number__in = project_number):
                i.save(using='secondary')
            for i in ProjectGroupSubSupplier.objects.filter(project_group__project__project_number__in = project_number):
                i.save(using='secondary')
            for i in ProjectCPIApprovedManager.objects.filter(project__project_number__in = project_number):
                i.save(using='secondary')
            for i in ProjectNotesConversation.objects.filter(project__project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentDetail.objects.filter(project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentProjectDetail.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentProjectGroupSubSupplier.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentPageDetails.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentDetailsRelationalfield.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentURLDetail.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentReconcilation.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentDeviceDetail.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentSupplierDetail.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentRoutingDetail.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentResearchDefenderDetail.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in RespondentDetailTolunaFields.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in AffiliateRouterExtraURLParams.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in DisqoQueryParam.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in ResearchDefenderSearch.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in ResearchDefenderFailureReasonDataStore.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in clientBackTrackingDetails.objects.filter(respondent__project_number__in = project_number):
                i.save(using='secondary')
            for i in GEOIPAPItable.objects.filter(RespondentDetail__project_number__in = project_number):
                i.save(using='secondary')
            for i in DraftInvoice.objects.filter(project__project_number__in = project_number):
                i.save(using='secondary')
            for i in DraftInvoiceRow.objects.filter(draft_invoice__project__project_number__in = project_number):
                i.save(using='secondary')
            for i in DraftInvoiceChangesStore.objects.filter(draft_invoice__project__project_number__in = project_number):
                i.save(using='secondary')
            for i in DraftInvoiceNotes.objects.filter(draft_invoice__project__project_number__in = project_number):
                i.save(using='secondary')
            for i in Invoice.objects.filter(invoice_project__project_number__in = project_number):
                i.save(using='secondary')
            for i in InvoiceRow.objects.filter(row_project_number__project_number__in = project_number):
                i.save(using='secondary')
            for i in ClientPaymentReceiptInvoiceLinking.objects.filter(invoice__invoice_project__project_number__in = project_number):
                i.save(using='secondary')
            for i in ProjectInvoicedApproved.objects.filter(project__project_number__in = project_number):
                i.save(using='secondary')
            for i in SupplierIdsMarks.objects.filter(project__project_number__in = project_number):
                i.save(using='secondary')
            for i in SupplierInvoiceRow.objects.filter(project__project_number__in = project_number):
                i.save(using='secondary')
            for i in SupplierInvoice.objects.filter(supplierinvoicerow__project__project_number__in = project_number):
                i.save(using='secondary')
            for i in SupplierInvoicePayment.objects.filter(supplier_invoice__supplierinvoicerow__project__project_number__in = project_number):
                i.save(using='secondary')
            ProjectBackup.objects.filter(Backup_status='Pending').update(Backup_status='Backup')
            return Response({"message":"Success"},status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({"error":"Something want Wrong"},status=status.HTTP_400_BAD_REQUEST)
