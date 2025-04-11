from django.core.validators import RegexValidator
from rest_framework import serializers
from Supplier.models import *


class SubSupplierListSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubSupplierOrganisation
        fields = [
            'id', 'sub_supplier_code', 'sub_supplier_name', 'sub_supplier_complete_url', 'sub_supplier_terminate_url', 'sub_supplier_quotafull_url', 'sub_supplier_securityterminate_url', 'sub_supplier_postback_url', 'sub_supplier_internal_terminate_redirect_url', 'sub_supplier_terminate_no_project_available',
            'sub_supplier_payment_details', 'sub_supplier_address1', 'sub_supplier_address2', 'sub_supplier_city', 'sub_supplier_state', 'sub_supplier_country',
            'sub_supplier_zip', 'sub_supplier_status', 'sub_supplier_rate_model', 'sub_supplier_rate', 'max_authorized_cpi', 'sub_supplier_TAX_id', 'max_completes_on_diy', 'sub_supplier_routerurl','sub_supplier_quality_type'
            ]
        read_only_fields = ['sub_supplier_code', 'sub_supplier_routerurl']
        extra_kwargs = {
            'sub_supplier_complete_url': {
                'source': 'sub_supplier_completeurl',
            },
            'sub_supplier_terminate_url': {
                'source': 'sub_supplier_terminateurl',
            },
            'sub_supplier_quotafull_url': {
                'source': 'sub_supplier_quotafullurl',
            },
            'sub_supplier_securityterminate_url': {
                'source': 'sub_supplier_securityterminateurl',
            },
            'sub_supplier_postback_url':{
                'source': 'sub_supplier_postbackurl',
            },
            'sub_supplier_payment_details': {
                'source': 'sub_supplier_paymentdetails',
                'required':False,
            },
            'sub_supplier_address1': {
                'required':False,
            },
            'max_completes_on_diy': {
                'required':False,
            },
            'sub_supplier_address2': {
                'required':False,
            },
            'sub_supplier_city': {
                'required':False,
            },
            'sub_supplier_state': {
                'required':False,
            },
            'sub_supplier_country': {
                'required':True,
            },
            'sub_supplier_zip': {
                'required':False,
            },
            'sub_supplier_TAX_id': {
                'required':False,
            },
            'sub_supplier_routerurl': {
                'required':False,
            },
        }


class SupplierAPIAdditionalfieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierAPIAdditionalfield
        fields = ['enable_routing', 'enable_hash', 'hash_variable_name', 'hash_security_key']

class SupplierSerializer(serializers.ModelSerializer):
    additional_field = SupplierAPIAdditionalfieldSerializer(source='supplierapiadditionalfield', required=False)

    class Meta:
        model = SupplierOrganisation
        fields = [
            'id', 'supplier_code', 'supplier_name', 'supplier_complete_url', 'supplier_terminate_url', 'supplier_quotafull_url', 'supplier_securityterminate_url', 'supplier_postback_url', 'supplier_internal_terminate_redirect_url', 'supplier_terminate_no_project_available',
            'supplier_payment_details', 'supplier_address1', 'supplier_address2', 'supplier_city', 'supplier_state', 'supplier_country',
            'supplier_zip', 'supplier_status', 'supplier_type', 'supplier_rate_model', 'supplier_rate', 'additional_field','max_authorized_cpi', 'supplier_TAX_id', 'max_completes_on_diy', 'supplier_routerurl','supplier_quality_type','company_bank_detail','supplier_currency','cpi_calculation_method'
            ]
        read_only_fields = ['supplier_code', 'supplier_routerurl']
        extra_kwargs = {
            'supplier_complete_url': {
                'source': 'supplier_completeurl',
            },
            'supplier_terminate_url': {
                'source': 'supplier_terminateurl',
            },
            'supplier_quotafull_url': {
                'source': 'supplier_quotafullurl',
            },
            'supplier_securityterminate_url': {
                'source': 'supplier_securityterminateurl',
            },
            'supplier_postback_url':{
                'source': 'supplier_postbackurl',
            },
            'supplier_payment_details': {
                'source': 'supplier_paymentdetails',
                'required':False,
            },
            'supplier_address1': {
                'required':False,
            },
            'max_completes_on_diy': {
                'required':False,
            },
            'supplier_address2': {
                'required':False,
            },
            'supplier_city': {
                'required':False,
            },
            'supplier_state': {
                'required':False,
            },
            'supplier_country': {
                'required':True,
            },
            'supplier_zip': {
                'required':False,
            },
            'supplier_TAX_id': {
                'required':False,
            },
            'supplier_routerurl': {
                'required':False,
            },
        }

    def create(self, validated_data):
        additional_field_data = validated_data.pop('supplierapiadditionalfield', {})
        apisupplier_org_obj = SupplierOrganisation.objects.create(**validated_data)
        SupplierAPIAdditionalfield.objects.create(supplier=apisupplier_org_obj, **additional_field_data)
        return apisupplier_org_obj


class SupplierUpdateSerializer(serializers.ModelSerializer):
    additional_field = SupplierAPIAdditionalfieldSerializer(source='supplierapiadditionalfield', required=False)

    class Meta:
        model = SupplierOrganisation
        fields = [
            'id', 'supplier_code', 'supplier_name', 'supplier_complete_url', 'supplier_terminate_url', 'supplier_quotafull_url', 'supplier_securityterminate_url', 'supplier_postback_url', 'supplier_internal_terminate_redirect_url', 'supplier_terminate_no_project_available',
            'supplier_payment_details', 'supplier_address1', 'supplier_address2', 'supplier_city', 'supplier_state', 'supplier_country',
            'supplier_zip', 'supplier_status', 'supplier_type', 'supplier_rate_model', 'supplier_rate', 'additional_field','max_authorized_cpi', 'supplier_TAX_id', 'max_completes_on_diy','supplier_quality_type','company_bank_detail','supplier_currency',
            'cpi_calculation_method'
            ]
        read_only_fields = ['supplier_code', 'supplier_type']
        extra_kwargs = {
            'supplier_complete_url': {
                'source': 'supplier_completeurl',
            },
            'supplier_terminate_url': {
                'source': 'supplier_terminateurl',
            },
            'supplier_quotafull_url': {
                'source': 'supplier_quotafullurl',
            },
            'supplier_securityterminate_url': {
                'source': 'supplier_securityterminateurl',
            },
            'supplier_postback_url':{
                'source': 'supplier_postbackurl',
            },
            'supplier_payment_details': {
                'source': 'supplier_paymentdetails',
                'required':False,
            },
            'supplier_address1': {
                'required':False,
            },
            'supplier_address2': {
                'required':False,
            },
            'max_completes_on_diy': {
                'required':False,
            },
            'supplier_city': {
                'required':False,
            },
            'supplier_state': {
                'required':False,
            },
            'supplier_country': {
                'required':True,
            },
            'supplier_zip': {
                'required':False,
            },
            'supplier_TAX_id': {
                'required':False,
            },
        }

    def update(self, instance, validated_data):
        additional_field_data = validated_data.pop('supplierapiadditionalfield', {})
        
        instance = super().update(instance, validated_data)

        supp_additional_field_obj,supp_additional_field_obj_created = SupplierAPIAdditionalfield.objects.get_or_create(supplier=instance)
        if additional_field_data.get('enable_routing'):
            supp_additional_field_obj.enable_routing = additional_field_data['enable_routing']
        else:
            supp_additional_field_obj.enable_routing = False
        if additional_field_data.get('enable_hash'):
            supp_additional_field_obj.enable_hash = additional_field_data['enable_hash']
        else:
            supp_additional_field_obj.enable_hash = False
        if additional_field_data.get('hash_security_key','') != '':
            supp_additional_field_obj.hash_security_key = additional_field_data['hash_security_key']
        if additional_field_data.get('hash_variable_name','') != '':
            supp_additional_field_obj.hash_variable_name = additional_field_data['hash_variable_name']
        supp_additional_field_obj.save()
        return instance


class SupplierContactSerializer(serializers.ModelSerializer):

    contact_number = serializers.CharField(
        source='supplier_contactnumber',
        required=False,
        allow_null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,13}$',
                            message="Contact number must be in the format of '+123456789'. Up to 13 digits allowed.")],
    )

    class Meta:
        model = SupplierContact
        fields = [
            "id", 'first_name', 'last_name', 'email', 'contact_number', 'supplier_id', 'supplier_contact_status','send_supplier_updates','send_final_ids', 'supplier_dashboard_registration'
        ]
        extra_kwargs = {
            'email': {
                'source': 'supplier_email',
            },
            'first_name': {
                'source': 'supplier_firstname',
            },
            'last_name': {
                'source': 'supplier_lastname',
            },
        }


class SupplierContactUpdateSerializer(serializers.ModelSerializer):

    contact_number = serializers.CharField(
        source='supplier_contactnumber',
        required=False,
        allow_null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,13}$',
                            message="Contact number must be in the format of '+123456789'. Up to 13 digits allowed.")],
    )

    class Meta:
        model = SupplierContact
        fields = [
            "id", 'first_name', 'last_name', 'email', 'contact_number', 'supplier_id', 'supplier_contact_status','send_supplier_updates','send_final_ids'
        ]
        extra_kwargs = {
            'email': {
                'source': 'supplier_email',
            },
            'first_name': {
                'source': 'supplier_firstname',
            },
            'last_name': {
                'source': 'supplier_lastname',
            },
        }


class SubSupplierContactListSerializer(serializers.ModelSerializer):

    contact_number = serializers.CharField(
        source='subsupplier_contactnumber',
        required=False,
        allow_null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,13}$',
                            message="Contact number must be in the format of '+123456789'. Up to 13 digits allowed.")],
    )

    class Meta:
        model = SubSupplierContact
        fields = [
            "id", 'first_name', 'last_name', 'email', 'contact_number', 'subsupplier_id', 'subsupplier_contact_status','subsend_supplier_updates','subsend_final_ids', 'subsupplier_dashboard_registration'
        ]
        extra_kwargs = {
            'email': {
                'source': 'subsupplier_email',
            },
            'first_name': {
                'source': 'subsupplier_firstname',
            },
            'last_name': {
                'source': 'subsupplier_lastname',
            },
        }


class SupplierOrgAuthKeyDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = SupplierOrgAuthKeyDetails
        fields = [
            'id','supplierOrg','authkey','api_key','secret_key','staging_base_url','production_base_url','client_id','supplier_id'
            ]



class SupplierBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierBankDetails
        fields = '__all__'


class SupplierInvoicingDetailsSerializer(serializers.ModelSerializer):
    bank_details = SupplierBankDetailsSerializer(source='supplier_bank_detail', read_only=True)

    class Meta:
        model = SupplierInvoicingDetails
        fields = '__all__'


    def create(self, validated_data):
        bank_details_dict = self.context['request'].data.get('bank_details')
        invoice_details_obj = super().create(validated_data)
        if bank_details_dict:
            bank_details_dict.update({'supplier_inv_detail':invoice_details_obj})
            SupplierBankDetails.objects.create(**bank_details_dict)
        return invoice_details_obj

class SubSupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSupplierOrganisation
        fields = ["id","supplier_org_id","sub_supplier_code","sub_supplier_name","max_completes_on_diy","sub_supplier_address1","sub_supplier_address2","sub_supplier_city","sub_supplier_state","sub_supplier_country","sub_supplier_zip","sub_supplier_TAX_id","sub_supplier_completeurl","sub_supplier_terminateurl","sub_supplier_quotafullurl","sub_supplier_securityterminateurl","sub_supplier_postbackurl","sub_supplier_routerurl","sub_supplier_rate_model","sub_supplier_rate","sub_supplier_paymentdetails","sub_supplier_status","sub_supplier_internal_terminate_redirect_url","sub_supplier_terminate_no_project_available","sub_supplier_url_code","max_authorized_cpi","sub_supplier_quality_type"]
        read_only_fields = ['sub_supplier_code', 'sub_supplier_routerurl']
        extra_kwargs = {
            'sub_supplier_country': {
                'required':True,
            }
        }

class SubSupplierContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSupplierContact
        fields = ["id","subsupplier_firstname","subsupplier_lastname","subsupplier_contactnumber","subsupplier_contact_status","subsend_supplier_updates","subsupplier_dashboard_registration","subsend_final_ids","subsupplier_email_notify","subsupplier_email","subsupplier_mail_sent","subsupplier_id"]



