from operator import truediv
from django.db import models
from Project.models import Language, ProjectGroup
from Questions.models import TranslatedAnswer, TranslatedQuestion
from employee.models import Country, EmployeeProfile

RESPONDENT_CHOICES = [
    ('1', 'Visit'),
    ('2', 'ClientSide Redirect')
]

class Visitors(models.Model):
    ip_address = models.CharField(max_length=50, null=True)
    genareted_visitor_id = models.CharField(max_length=255, null=True)
    user_agent = models.CharField(max_length=255, null=True)
    source = models.CharField(max_length=255, null=True)
    subsource = models.CharField(max_length=255, null=True,default='') # subsupplier source
    ruid = models.CharField(max_length=255,null=True)
    rsid = models.CharField(max_length=255,null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE,null=True, related_name='visitors_country_store')
    respondent_status = models.CharField(max_length=3, choices=RESPONDENT_CHOICES,default='1')
    created_at = models.DateTimeField(auto_now=True)


class VisitorURLParameters(models.Model):
    visitor = models.OneToOneField(Visitors, on_delete=models.CASCADE, related_name='url_parameter')
    url_extra_params = models.TextField(null=True, blank=True)
    rsid = models.CharField(max_length=255, null=True, blank=True)
    pub_id = models.CharField(max_length=255, null=True, blank=True)
    entry_url = models.CharField(max_length=500, null=True, blank=True)
    exit_url = models.CharField(max_length=500, null=True, blank=True)


class VisitorSurveyRedirect(models.Model):
    survey_number = models.CharField(max_length=100, null=True)
    supplier_survey_url = models.CharField(max_length=500, null=True)
    visitor_id = models.ForeignKey(Visitors, on_delete=models.CASCADE, related_name='visitor_survey_redirect', null=True)
    respondent_status = models.CharField(max_length=3, choices=RESPONDENT_CHOICES,default='3')
    priority = models.BooleanField(default=False)


class AffiliateRouterQuestions(models.Model):
    translated_question = models.ForeignKey(TranslatedQuestion, on_delete=models.CASCADE)
    languages = models.ManyToManyField(Language)
    sequence = models.IntegerField(default=1)
    client_pipeline = models.IntegerField(default=1)


    def __str__(self):
        return self.translated_question.translated_question_text

class AffiliateRouterQuestionsData(models.Model):
    visitor = models.ForeignKey(Visitors, on_delete=models.CASCADE)
    parent_question = models.ForeignKey(TranslatedQuestion, on_delete=models.CASCADE)
    parent_answers = models.ManyToManyField(TranslatedAnswer)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    extra_response_answer = models.TextField(null=True, blank=True)
    open_end_answer = models.CharField(max_length=10000,null=True, blank=True)
    received_answers_id = models.CharField(max_length=255, unique=True)
    

class RountingPriority(models.Model):
    project_group = models.OneToOneField(ProjectGroup, on_delete=models.CASCADE, null=True, blank=True)
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='routing_priority_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='routing_priority_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

class ReRoutingUser(models.Model):
    visitorId = models.CharField(max_length=255, unique=True)
    usc = models.CharField(max_length=255,default='internal')
    email = models.EmailField(max_length=80)
    created_at = models.DateTimeField(auto_now=True)

class TotalVisitorsRouts(models.Model):
    visitor = models.ForeignKey(Visitors, on_delete=models.CASCADE)
    entry_url = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True)