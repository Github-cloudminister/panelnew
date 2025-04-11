from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import *

class CustomerSerializer(serializers.ModelSerializer):
    sales_person_id_name = serializers.SerializerMethodField()
    country_name = serializers.CharField(source="cust_org_country.country_name", read_only = True)
    currency_name = serializers.CharField(source="customer_invoice_currency.currency_name", read_only = True)

    def get_sales_person_id_name(self,obj):
        return f"{obj.sales_person_id.first_name} {obj.sales_person_id.last_name}" 

    class Meta:
        model = CustomerOrganization
        fields = [
            'id', 'organization_name', 'customer_organization_type', 'currency', 'currency_name', 
            'address_1', 'address_2', 'city', 'state', 'country', 'country_name', 'pincode', 'taxVAT_number', 'website', 'other_details', 
            'ship_to_address_1', 'ship_to_address_2', 'ship_to_city', 'ship_to_state', 'ship_to_country', 'ship_to_pincode', 
            'sales_person_id', 'sales_person_id_name', 'company_invoice_bank_detail', 'created_at','payment_terms','invoice_currency', 'cpi_calculation_method', 'threat_potential_score'
        ]
        extra_kwargs = {
            'organization_name': {
                'source': 'cust_org_name',
                'required':True,
                'allow_null': False,
                'allow_blank': False,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'customer_organization_type': {
                'required':True,
                'allow_null': False,
                'allow_blank': False,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'currency': {
                'required':True,
                'allow_null': False,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'address_1': {
                'source': 'cust_org_address_1',
                'required':True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'address_2': {
                'source': 'cust_org_address_2',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'city': {
                'source': 'cust_org_city',
                'required':True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'state': {
                'source': 'cust_org_state',
                'required':True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'country': {
                'source': 'cust_org_country',
                'required':True,
                'allow_null': False,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'pincode': {
                'source': 'cust_org_zip',
                'required':True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'taxVAT_number':{
                'source':'cust_org_TAXVATNumber',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'website':{
                'source':'cust_org_website',
                'required':True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'other_details': {
                'source': 'cust_org_other',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'ship_to_address_1': {
                'source': 'cust_org_ship_to_address_1',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },            
            'ship_to_address_2': {
                'source': 'cust_org_ship_to_address_2',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },            
            'ship_to_city': {
                'source': 'cust_org_ship_to_city',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },            
            'ship_to_state': {
                'source': 'cust_org_ship_to_state',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },            
            'ship_to_country': {
                'source': 'cust_org_ship_to_country',
                'required': True,
                'allow_null': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },
            'ship_to_pincode': {
                'source': 'cust_org_ship_to_zip',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or balnk.'
                },
            },            
            'sales_person_id': {
                'required': True,
                'allow_null': False,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                }
            },
            'payment_terms': {
                'required': True,
            },
            'invoice_currency': {
                'source': 'customer_invoice_currency',
            },
            'company_invoice_bank_detail': {
                'required': True,
                'allow_null': False,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                }
            },
            'sales_person_id_name':{
                'read_only': True
            }
        }


class CustomerUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerOrganization
        fields = [
            'id', 'organization_name', 'customer_organization_type', 'currency', 
            'address_1', 'address_2', 'city', 'state', 'country', 'pincode', 'taxVAT_number', 'website', 'other_details', 
            'ship_to_address_1', 'ship_to_address_2', 'ship_to_city', 'ship_to_state', 'ship_to_country', 'ship_to_pincode', 
            'sales_person_id', 'company_invoice_bank_detail', 'created_at','payment_terms','invoice_currency','cpi_calculation_method','threat_potential_score'
        ]
        extra_kwargs = {
            'organization_name': {
                'source': 'cust_org_name',
                'required':True,
                'allow_null': False,
                'allow_blank': False,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'customer_organization_type': {
                'required':True,
                'allow_null': False,
                'allow_blank': False,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'address_1': {
                'source': 'cust_org_address_1',
                'required':True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'address_2': {
                'source': 'cust_org_address_2',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'city': {
                'source': 'cust_org_city',
                'required':True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'state': {
                'source': 'cust_org_state',
                'required':True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'country': {
                'source': 'cust_org_country',
                'required':True,
                'allow_null': False,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'pincode': {
                'source': 'cust_org_zip',
                'required':True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'taxVAT_number':{
                'source':'cust_org_TAXVATNumber',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'website':{
                'source':'cust_org_website',
                'required':True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'other_details': {
                'source': 'cust_org_other',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'ship_to_address_1': {
                'source': 'cust_org_ship_to_address_1',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },            
            'ship_to_address_2': {
                'source': 'cust_org_ship_to_address_2',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },            
            'ship_to_city': {
                'source': 'cust_org_ship_to_city',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },            
            'ship_to_state': {
                'source': 'cust_org_ship_to_state',
                'required': True,
                'allow_null': False,
                'allow_blank': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },            
            'ship_to_country': {
                'source': 'cust_org_ship_to_country',
                'required': True,
                'allow_null': True,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                },
            },
            'ship_to_pincode': {
                'source': 'cust_org_ship_to_zip',
            },
            'payment_terms': {
                'allow_null':True
            },
            'invoice_currency': {
                'source': 'customer_invoice_currency',
            },
            'other_details': {
                'source': 'cust_org_other',
                'required': False,
                'allow_null':True,
            },
            'company_invoice_bank_detail': {
                'required': True,
                'allow_null': False,
                'error_messages': {
                    'null': 'This field may not be null or blank.'
                }
            }
        }


class ClientContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = ClientContact
        fields = [
            'id', 'client_firstname', 'client_lastname', 'client_email', 'client_contact_number', 'customer_id', 'client_status',
        ]
        extra_kwargs = {
            'client_contact_number': {
                'source':'client_contactnumber',
                'required':False,
                'allow_null':True,
            },
        }


class CurrencySerializer(serializers.ModelSerializer):

    currency_iso = serializers.CharField(
        validators=[UniqueValidator(queryset=Currency.objects.all())],
        required=True
    )

    class Meta:
        model = Currency
        fields = ['id', 'currency_name', 'currency_iso']
