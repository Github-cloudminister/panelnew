from rest_framework import serializers
from .models import Recontact

class RecontactSectionSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Recontact
        fields = '__all__'
    
