from django.contrib import admin
from Questions.models import ZipCodeMappingTable
from .models import *

# Register your models here.
@admin.register(ClientDBCountryLanguageMapping)
class DataAdmin(admin.ModelAdmin):
    
    list_display = ('customer','lanugage_id','country_id','toluna_client_language_id','zamplia_client_language_id','client_language_name','client_language_description','country_lang_guid')

admin.site.register(ClientQuota)
admin.site.register(ClientLayer)
admin.site.register(ClientSubQuota)
admin.site.register(ClientSurveyPrescreenerQuestions)
admin.site.register(CustomerDefaultSupplySources)
admin.site.register(ZipCodeMappingTable)
admin.site.register(CustomerDefaultSubSupplierSources)




