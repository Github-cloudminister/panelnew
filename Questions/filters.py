import django_filters
from Questions.models import ParentQuestion



class ParentQuestionsFilter(django_filters.FilterSet):
    text = django_filters.CharFilter(field_name='parent_question_text', lookup_expr='icontains')
    number = django_filters.CharFilter(field_name='parent_question_number', lookup_expr='icontains')

    class Meta:
        model = ParentQuestion
        fields = ['id']