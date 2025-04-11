from rest_framework import serializers
from CompanyBankDetails.models import *


class CompanyDetailSerializer(serializers.ModelSerializer):
    company_country_name = serializers.CharField(source='company_country.country_name', read_only=True)
    class Meta:
        model = CompanyDetails
        fields = ['id','company_name','company_contact_number','company_address1','company_address2','company_city','company_state','company_country','company_country_name','company_zipcode','company_email','company_website','company_tax_number','company_cin_number','company_pan_number','company_local_currency','company_invoice_prefix_local_currency','company_invoice_prefix_international_currency','company_invoice_suffix_local_currency','company_invoice_suffix_international_currency']

class CompanyInvoiceBankDetailSerializer(serializers.ModelSerializer):
    company_address_detail = CompanyDetailSerializer(source='company_details', read_only=True)
    account_type_name = serializers.SerializerMethodField()

    class Meta:
        model = CompanyInvoiceBankDetail
        fields = ['id','account_number', 'ifsc_code', 'bank_name', 'bank_address', 'swift_code', 'account_type', 'account_type_name', 'company_iban_number', 'company_routing_number', 'created_by', 'modified_by','company_details' ,'company_address_detail']
        read_only_fields = ['account_type_name', 'created_by', 'modified_by']
        extra_kwargs = {
            'account_number': {
                'required': True,
                'allow_null': False,
                'allow_blank': False,
                'error_messages': {
                    'null': 'This field should not be null or blank.'
                }
            },
            'ifsc_code': {
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field should not be null or blank.'
                }
            },
            'bank_name': {
                'required': True,
                'allow_null': False,
                'allow_blank': False,
                'error_messages': {
                    'null': 'This field should not be null or blank.'
                }
            },
            'bank_address': {
                'required': True,
                'allow_null': False,
                'allow_blank': False,
                'error_messages': {
                    'null': 'This field should not be null or blank.'
                }
            },
            'swift_code': {
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field should not be null or blank.'
                }
            },
            'account_type': {
                'required': True,
                'allow_null': False,
                'allow_blank': False,
                'error_messages': {
                    'null': 'This field should not be null or blank.'
                }
            },
            'company_iban_number': {
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field should not be null or blank.'
                }
            },
            'company_routing_number': {
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field should not be null or blank.'
                }
            },
        }

    def get_account_type_name(self, instance):
        return instance.get_account_type_display()