from django.contrib import admin
from Invoice.models import *

# Register your models here.
admin.site.register(Invoice)
admin.site.register(InvoiceRow)


@admin.register(DraftInvoice)
class DraftInvoiceAdmin(admin.ModelAdmin):
    search_fields = ('project__project_number',)
    

admin.site.register(InvoicePaymentReminderEmail)
admin.site.register(DraftInvoiceChangesStore)