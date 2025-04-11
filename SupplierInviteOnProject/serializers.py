# django imports
from django.db import models
from django.db.models import fields

# rest-framework imports
from rest_framework import serializers

# in-project imports
from SupplierInviteOnProject.models import *

class SupplierInviteDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierInviteDetail
        fields = ['id', 'supplier_invite', 'supplier_org', 'supplier_contact', 'budget']

class SupplierInviteSerializer(serializers.ModelSerializer):
    supplier_invite_detail = SupplierInviteDetailSerializer(source='supplierinvitedetail', many=True)

    class Meta:
        model = SupplierInvite
        fields = ['id', 'project', 'completes', 'incidence', 'loi', 'country', 'message', 'supplier_invite_detail']

    def create(self, validated_data):
        supplier_invite_detail_data = validated_data.pop('supplierinvitedetail', [])
        supplier_invite_obj = super().create(validated_data)
        for supplier_invite_detail in  supplier_invite_detail_data:
            supplier_contact_list = supplier_invite_detail.pop('supplier_contact', '')
            supplier_contact_id_list = [supplier_contact.id for supplier_contact in supplier_contact_list]
            supp_invite_dtl_obj = SupplierInviteDetail.objects.create(supplier_invite = supplier_invite_obj, **supplier_invite_detail)
            supp_invite_dtl_obj.supplier_contact.add(supplier_contact_id_list)
        return supplier_invite_obj


class SuppliersMidfieldUpdateSerializer(serializers.ModelSerializer):
    supplier_contacts = serializers.PrimaryKeyRelatedField(source='supplier_org.suppliercontact_set', many=True, read_only=True)
    class Meta:
        model = ProjectGroupSupplier
        fields = ['supplier_org', 'supplier_contacts']
