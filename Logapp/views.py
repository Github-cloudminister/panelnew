from Logapp.models import *

def employee_login_Log(login_by):
    EmployeeLoginLog.objects.create(login_by = login_by)

def project_log(created_data,updated_data,status,project_id,created_by):
    created_by = created_by if created_by else None
    ProjectLog.objects.create(created_data = created_data,updated_data = updated_data,status = status,project_id = project_id,created_by = created_by)
    return "Success"

def project_error_log(error_description,created_by):
    created_by = created_by if created_by else None
    ProjectErrorLog.objects.create(error_description = error_description,created_by= created_by)
    return "Success"

def project_group_error_log(error_description,created_by):
    created_by = created_by if created_by else None
    ProjectGroupErrorLog.objects.create(error_description = error_description,created_by= created_by)
    return "Success"

def projectgroup_log(created_data,updated_data,status,projectgroup_id,created_by):
    created_by = created_by if created_by else None
    ProjectGroupLog.objects.create(created_data = created_data,updated_data = updated_data,status = status,projectgroup_id = projectgroup_id,created_by = created_by)
    return "Success"

def projectgroupsupplier_log(created_data,updated_data,project_group_supplier,supplier,projectgroup,status,created_by):
    created_by = created_by if created_by else None
    ProjectGroupSupplierLog.objects.create(created_data = created_data,updated_data = updated_data,supplier_id = supplier,projectgroup_id = projectgroup,status = status,project_group_supplier = project_group_supplier,created_by = created_by)
    return "Success"

def draft_invoice_log(created_data,updated_data,id,status,created_by):
    created_by = created_by if created_by else None
    id = id if id else None
    DraftInvoiceLog.objects.create(created_data = created_data,updated_data = updated_data,status = status,draftinvoice = id, created_by = created_by)
    return "Success"

def invoice_log(created_data,updated_data,id,status,created_by):
    created_by = created_by if created_by else None
    id = id if id else None
    InvoiceLog.objects.create(created_data = created_data,updated_data = updated_data,status = status,invoice = id, created_by = created_by)
    return "Success"

def supplier_invoice_log(created_data,updated_data,supplierinvoice_id,supplier_code,ip):
    SupplierInvoiceLogs.objects.create(created_data = created_data,updated_data = updated_data,supplierinvoice_id = supplierinvoice_id,supplier_code = supplier_code,ip_address = ip)
    return "Success"

def surveyentry_log(error_description,glsid):
    SurveyEntryLog.objects.create(error_description=error_description,glsid = glsid)
    return "Success"

def routerexception_log(visitor_id,error):
    RouterException.objects.create(visitor = visitor_id,detailed_reason = error)
    return "Success"

def supplier_log(created_data,updated_data,supplier,created_by):
    SupplierLog.objects.create(created_data = created_data,updated_data = updated_data,supplier_id = supplier,created_by =created_by)
    return "Success"

def supplier_enable_disable_log(add_enabled,remove_enabled,supplier,created_by):
    SupplierEnableDisableLog.objects.create(add_enabled = add_enabled,remove_enabled = remove_enabled,supplier_id = supplier,created_by =created_by)
    return "Success"

def sub_supplier_log(created_data,updated_data,sub_supplier,created_by):
    SubSupplierLog.objects.create(created_data = created_data,updated_data = updated_data,sub_supplier_id = sub_supplier,created_by =created_by)
    return "Success"

def sub_supplier_enable_disable_log(add_enabled,remove_enabled,sub_supplier,created_by):
    SubSupplierEnableDisableLog.objects.create(add_enabled = add_enabled,remove_enabled = remove_enabled,sub_supplier_id = sub_supplier,created_by =created_by)
    return "Success"

def customer_log(created_data,updated_data,customer,created_by):
    CustomerLog.objects.create(created_data = created_data,updated_data = updated_data,customer_id = customer,created_by = created_by)
    return "Success"

def projectgroupprescreener_log(add_questions,removed_questions,projectgroup_pescreener,projectgroup,created_by):
    ProjectGroupPrescreenerLogs.objects.create(add_questions = add_questions,removed_questions = removed_questions,projectgroup_pescreener_id = projectgroup_pescreener,projectgroup_id = projectgroup, created_by = created_by)

def projectgroup_panel_log(panel_enabled,panel_disabled,projectgroup,created_by):
    ProjectGroupPanelLog.objects.create(panel_enabled = panel_enabled,panel_disabled = panel_disabled,projectgroup_id = projectgroup,created_by = created_by)

def projectgroup_ad_panel_log(adpanel_enabled,adpanel_disabled,projectgroup,projectgroupsubsupplier,created_by):
    created_by = created_by if created_by else None
    projectgroupsubsupplier = projectgroupsubsupplier if projectgroupsubsupplier else None
    ProjectGroupADPanelLog.objects.create(adpanel_enabled = adpanel_enabled,adpanel_disabled = adpanel_disabled,projectgroup_id = projectgroup,projectgroupsubsupplier_id = projectgroupsubsupplier,created_by = created_by)

def project_reconciliation_log(project,reconciliation,error,created_by):
    ProjectReconciliationLog.objects.create(project_id = project,reconciliation = reconciliation,error = error,created_by = created_by)


def project_supplier_cpi_update_log(old_cpi,new_cpi,source,project_number,project_group_number,created_by):
    ProjectSupplierCPIUpdateLog.objects.create(old_cpi = old_cpi,new_cpi = new_cpi,source = source,project_number = project_number,project_group_number = project_group_number,created_by = created_by)