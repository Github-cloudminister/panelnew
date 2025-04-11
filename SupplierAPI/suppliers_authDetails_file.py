from Supplier.models import SupplierOrgAuthKeyDetails

def supplier_authDetails_func(supplierOrg_id, **kwargs):
    SupplierOrgAuthKeyDetails.objects.update_or_create(supplierOrg_id=supplierOrg_id,
                        defaults={'authkey': kwargs.get('authkey',''), 'api_key': kwargs.get('api_key',''), 'secret_key': kwargs.get('secret_key',''), 'staging_base_url': kwargs.get('staging_base_url',''), 'production_base_url': kwargs.get('production_base_url',''), 'client_id': kwargs.get('client_id',''), 'supplier_id': kwargs.get('supplier_id','')})
