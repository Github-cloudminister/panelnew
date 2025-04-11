import django_filters
from Invoice.models import DraftInvoice, DraftInvoiceRow



class DraftInvoiceListProjectsFilterSet(django_filters.FilterSet):
    projects = django_filters.BaseInFilter(field_name='project__project_number')
    customers = django_filters.BaseInFilter(field_name='project__project_customer__id')
    status = django_filters.CharFilter(field_name='project__project_status')

    class Meta:
        model = DraftInvoice
        fields = ['projects','customers','status']


class DraftInvoiceFilterSet(django_filters.FilterSet):
    projects = django_filters.BaseInFilter(field_name='project__project_number')
    customers = django_filters.BaseInFilter(field_name='invoice_to_customer__id')
    currency_ids = django_filters.BaseInFilter(field_name='invoice_currency__id')
    ids = django_filters.BaseInFilter(field_name='id')
    status = django_filters.CharFilter(field_name='project__project_status')
    ba_approved = django_filters.CharFilter(field_name='BA_approved')
    accountant_approved = django_filters.CharFilter(field_name='Accountant_approved')

    class Meta:
        model = DraftInvoice
        fields = ['projects','customers','status','draft_approved','ids','currency_ids','ba_approved','accountant_approved']
       

class DraftInvoiceRowFilterSet(django_filters.FilterSet):
    project_number = django_filters.BaseInFilter(field_name='draft_invoice__project__project_number')

    class Meta:
        model = DraftInvoiceRow
        fields = ['project_number']