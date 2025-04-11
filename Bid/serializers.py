from rest_framework import serializers
from Bid.models import *
from Project.models import Project

class bidRowSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    class Meta:
        model = BidRow
        fields = ['id','bid_row_type','bid_row_country','bid_row_language','bid_row_incidence','bid_row_loi','bid_row_required_N','bid_row_feasible_N','bid_row_cpi','bid_row_total','bid_row_description','finalised_row_cpi']
        read_only_fields = ['id']
        

class bidListSerializer(serializers.ModelSerializer):
    project_details = serializers.SerializerMethodField()
    bidrow = bidRowSerializer(many=True)

    def get_project_details(self, instance):
        return Project.objects.filter(bid_id = instance.id).values('id','project_number').first()
    
    class Meta:
        model = Bid
        fields = ['id','bid_number','bid_name', 'start_date', 'end_date', 'bid_type', 'bid_description', 'bid_status', 'customer', 'client_contact','project_manager','bidrow','bid_category','bid_currency','secondary_project_manager','project_manager','project_details']
        read_only_fields = ['bid_number','project_manager', 'bid_status']
    
    def create(self, validated_data):
        bid_row = validated_data['bidrow']
        del validated_data['bidrow']
        allbids = Bid.objects.count()
        bid_serial_number = 1000+int(allbids)

        bid_number = "BPR"+str(bid_serial_number).zfill(6)
        bid_obj = Bid.objects.create(bid_number = bid_number,**validated_data,created_by = self.context['user'])
        for row in bid_row:
            BidRow.objects.create(bid = bid_obj, **row,created_by = self.context['user'])
        return bid_obj


class bidViewSerializer(serializers.ModelSerializer):
    bidrow = bidRowSerializer(many=True)

    class Meta:
        model = Bid
        fields = ['id','bid_number','bid_name', 'start_date', 'end_date', 'bid_type', 'bid_description', 'bid_status', 'customer', 'client_contact','bidrow','bid_category','bid_currency','secondary_project_manager','project_manager']
        read_only_fields = ['id','bid_number']
    
    def update(self, instance, validated_data):
        bid_row_data = validated_data.pop('bidrow')

        bid_rows = (instance.bidrow).all()
        bid_rows = list(bid_rows)
        instance.bid_name = validated_data['bid_name']
        instance.start_date = validated_data['start_date']
        instance.end_date = validated_data['end_date']
        instance.bid_type = validated_data['bid_type']
        instance.bid_description = validated_data['bid_description']
        instance.customer = validated_data['customer']
        instance.client_contact = validated_data['client_contact']
        instance.save()

        for row in bid_row_data:
            try:
                bid_row_obj = BidRow.objects.get(id=row['id'])
                bid_row_obj.finalised_row_cpi = row['finalised_row_cpi']
                bid_row_obj.bid_row_type = row['bid_row_type']
                bid_row_obj.bid_row_country = row['bid_row_country']
                bid_row_obj.bid_row_language = row['bid_row_language']
                bid_row_obj.bid_row_incidence = row['bid_row_incidence']
                bid_row_obj.bid_row_loi = row['bid_row_loi']
                bid_row_obj.bid_row_required_N = row['bid_row_required_N']
                bid_row_obj.bid_row_feasible_N = row['bid_row_feasible_N']
                bid_row_obj.bid_row_cpi = row['bid_row_cpi']
                bid_row_obj.bid_row_total = row['bid_row_total']
                bid_row_obj.bid_row_description = row['bid_row_description']
                bid_row_obj.modified_by = self.context['user']
                bid_row_obj.save()
            except:
                BidRow.objects.create(bid=instance, **row, created_by = self.context['user'])
        return instance