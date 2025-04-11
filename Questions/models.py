from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from ClientSupplierAPIIntegration.TolunaClientAPI.models import ClientDBCountryLanguageMapping

from employee.models import EmployeeProfile
from Project.models import Language


class QuestionCategory(models.Model):

    # Fields
    category = models.CharField(max_length=100)
    category_id = models.IntegerField(null=True,blank=True)
    category_description = models.CharField(max_length=100, null=True)
    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete = models.SET_NULL, null=True, related_name = 'questioncat_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete = models.SET_NULL, null=True, related_name = 'questioncat_modified_by')
    
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.category


# While creating this object, make sure to check signal as well. We are creating same object in Translated Question as well. 
# Signal code in same file at the end
class ParentQuestion(models.Model):

    question_type_choices = (
        ("SS","Single Select"),
        ("MS","Multi Select"),
        ("NU","Numeric"),
        ("OE","Open End"),
        ("IN","Info"),
        ("DT","Date"), #toluna API specific Field
        ("CT","ComputedType"),#toluna API specific Field
        ("CTZIP","ComputedTypezip"),#toluna API specific Field
        ("ZIP","zip"),#toluna API specific Field
        ("FU","File Upload")
    )
    question_prescreener_type = (
        ('Custom', 'Custom'),
        ('Standard', 'Standard'),
        ('API', 'API'),
        ('TolunaAPI','TolunaAPI')
    )


    parent_question_number = models.CharField(max_length=80, default="")
    parent_question_text = models.CharField(max_length=1000, default="")
    internal_parent_question_text = models.CharField(max_length=1000, default="")
    parent_question_type = models.CharField(max_length=50, choices=question_type_choices, default="SS")
    parent_question_category = models.ForeignKey(QuestionCategory, on_delete=models.CASCADE, default="",null=True)
    parent_question_prescreener_type = models.CharField(max_length=10, default="Custom", choices=question_prescreener_type)
    status = models.BooleanField(default=True)
    is_routable = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    apidbcountrylangmapping = models.ForeignKey(ClientDBCountryLanguageMapping, on_delete = models.SET_NULL,null=True,default=None)
    toluna_question_id = models.CharField(max_length=80, null=True, blank=True, default="")
    toluna_is_routable = models.BooleanField(default=False)
    toluna_question_category_id = models.CharField(max_length=80, null=True, blank=True, default="")
    disqo_question_key = models.CharField(max_length=80, null=True, blank=True, default="")
    disqo_question_id = models.CharField(max_length=80, null=True, blank=True, default="")
    zamplia_question_id = models.CharField(max_length=80, null=True, blank=True, default="")
    sago_question_id = models.CharField(max_length=85,null=True, default='')
    lucid_question_id = models.CharField(max_length=80, null=True, blank=True, default="")
    zamplia_is_routable = models.BooleanField(default=False)
    created_by = models.ForeignKey(EmployeeProfile, on_delete = models.SET_NULL, null=True, related_name='question_created_by')
    modified_by = models.ForeignKey(EmployeeProfile, on_delete = models.SET_NULL, null=True, related_name='question_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.parent_question_text)

    class Meta:
        ordering = ('-id',)


# While creating this object, make sure to check signal as well. We are creating same object in Translated Answers as well. 
# Signal code in same file at the end
class ParentAnswer(models.Model):

    parent_answer_text = models.CharField(max_length=1000,null=True)
    parent_answer_id = models.CharField(max_length=85, default='')
    parent_question = models.ForeignKey(ParentQuestion, on_delete=models.CASCADE,null=True)
    sequence = models.IntegerField(default=1)
    numeric_min_range = models.IntegerField(default=0, null=True, blank=True)
    numeric_max_range = models.IntegerField(default=99999, null=True, blank=True)
    parent_answer_status = models.BooleanField(default=True)
    exclusive = models.BooleanField(default=False)
    internal_question_id = 	models.CharField(max_length=85,null=True, default='')
    toluna_answer_id = models.CharField(max_length=85,null=True, default='')
    answer_internal_name = models.CharField(max_length=1000,null=True, default='')
    toluna_question_id = models.CharField(max_length=85, null=True, default='')
    disqo_answer_id = models.CharField(max_length=85,null=True, default='')
    disqo_question_key = models.CharField(max_length=85,null=True, default='')
    disqo_question_id = models.CharField(max_length=85,null=True, default='')
    zamplia_answer_id = models.CharField(max_length=85,null=True, default='')
    zamplia_question_id = models.CharField(max_length=85,null=True, default='')
    sago_question_id = models.CharField(max_length=85,null=True, default='')
    sago_answer_id = models.CharField(max_length=85,null=True, default='')
    lucid_answer_id = models.CharField(max_length=85,null=True, default='')
    lucid_question_id = models.CharField(max_length=85,null=True, default='')
    created_by = models.ForeignKey(EmployeeProfile, on_delete = models.SET_NULL, null=True, related_name = 'answer_created_by')
    modified_by = models.ForeignKey(EmployeeProfile, on_delete = models.SET_NULL, null=True, related_name = 'answer_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.parent_answer_text)

    class Meta:
        ordering = ('id',)


class TranslatedQuestion(models.Model):

    question_type_choices = (
        ("SS","Single Select"),
        ("MS","Multi Select"),
        ("NU","Numeric"),
        ("OE","Open End"),
        ("IN","Info"),
        ("DT","Date"), #toluna API specific Field
        ("CT","ComputedType"),#toluna API specific Field
        ("CTZIP","ComputedTypezip"),#toluna API specific Field
        ("ZIP","zip"),#toluna API specific Field
        ("FU","File Upload"),
    )
    question_prescreener_type = (
        ('Custom', 'Custom'),
        ('Standard', 'Standard'),
    )
    parent_question_type = models.CharField(max_length=50, choices=question_type_choices, default="SS")
    parent_question_prescreener_type = models.CharField(max_length=10,default="Custom", choices=question_prescreener_type)
    translated_question_text = models.CharField(max_length=1000, default="",null=True)
    internal_question_text = models.CharField(max_length=1000, default="",null=True)
    status = models.BooleanField(default=True)
    apidbcountrylangmapping = models.ForeignKey(ClientDBCountryLanguageMapping, on_delete = models.SET_NULL,null=True,default=None)
    lang_code = models.ForeignKey(Language, on_delete=models.CASCADE,null=True)
    parent_question = models.ForeignKey(ParentQuestion, on_delete=models.CASCADE,null=True)
    parent_question_category = models.ForeignKey(QuestionCategory, on_delete=models.CASCADE, default="",null=True)
    is_active = models.BooleanField(default=True)
    Internal_question_id = models.CharField(max_length=80, null=True, blank=True, default="")
    sago_question_id = models.CharField(max_length=85,null=True, default='')
    toluna_question_id = models.CharField(max_length=80, null=True, blank=True, default="")
    toluna_is_routable = models.BooleanField(default=False)
    toluna_question_category_id = models.CharField(max_length=80, null=True, blank=True, default="")
    disqo_question_key = models.CharField(max_length=80, null=True, blank=True, default="")
    disqo_question_id = models.CharField(max_length=80, null=True, blank=True, default="")
    zamplia_question_id = models.CharField(max_length=80, null=True, blank=True, default="")
    lucid_question_id = models.CharField(max_length=80, null=True, blank=True, default="")
    zamplia_is_routable = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        EmployeeProfile, on_delete = models.SET_NULL, null=True, related_name = 'transquestion_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete = models.SET_NULL, null=True, related_name = 'transquestion_modified_by')
    
    created_at = models.DateTimeField(auto_now_add = True, editable = False)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return str(self.translated_question_text)

    class Meta:
        ordering = ('-id',)


class TranslatedAnswer(models.Model):

    translated_answer = models.CharField(max_length=1000,null=True)
    parent_answer = models.ForeignKey(ParentAnswer, on_delete=models.CASCADE,null=True)
    translated_parent_question = models.ForeignKey(TranslatedQuestion, on_delete=models.CASCADE,null=True)
    translated_answer_status = models.BooleanField(default=True)
    internal_answer_id = models.CharField(max_length=85,null=True, default='')
    internal_question_id = 	models.CharField(max_length=85,null=True, default='')
    toluna_answer_id = models.CharField(max_length=85,null=True, default='')
    answer_internal_name = models.CharField(max_length=1000,null=True, default='')
    toluna_question_id = models.CharField(max_length=85, null=True, default='')
    disqo_answer_id = models.CharField(max_length=85,null=True, default='')
    disqo_question_key = models.CharField(max_length=85,null=True, default='')
    disqo_question_id = models.CharField(max_length=85,null=True, default='')
    zamplia_answer_id = models.CharField(max_length=85,null=True, default='')
    zamplia_question_id = models.CharField(max_length=85,null=True, default='')
    sago_question_id = models.CharField(max_length=85,null=True, default='')
    sago_answer_id = models.CharField(max_length=85,null=True, default='')
    lucid_answer_id = models.CharField(max_length=85,null=True, default='')
    lucid_question_id = models.CharField(max_length=85,null=True, default='')
    created_by = models.ForeignKey(EmployeeProfile, on_delete = models.SET_NULL, null=True, related_name = 'transanswer_created_by')
    modified_by = models.ForeignKey(EmployeeProfile, on_delete = models.SET_NULL, null=True, related_name = 'transanswer_modified_by')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.translated_answer + '--' + self.translated_parent_question.translated_question_text)

    class Meta:
        ordering = ('id',)

class ZipCodeMappingTable(models.Model):
    zipcode = models.CharField(max_length=255)
    parent_answer_id = models.ForeignKey(TranslatedAnswer, on_delete=models.CASCADE,null=True)

@receiver(post_save, sender=ParentQuestion)
def translate_question_if_create(sender, instance, created, **kwargs):
    languages = Language.objects.get(language_code='en')
    if created:
        TranslatedQuestion.objects.create(parent_question=instance, translated_question_text=instance, lang_code=languages, created_by=instance.created_by)

@receiver(post_save, sender=ParentAnswer)
def translate_answer_if_create(sender, instance, created, **kwargs):
    translate = TranslatedQuestion.objects.filter(parent_question=instance.parent_question).first()
    if created:
        TranslatedAnswer.objects.create(parent_answer=instance, translated_answer=instance, translated_parent_question=translate, translated_answer_status=True, created_by=instance.created_by)