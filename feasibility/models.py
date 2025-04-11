from django.db import models
from django.core.validators import RegexValidator, MaxValueValidator, MinValueValidator
from Questions.models import ParentAnswer, ParentQuestion

# Create your models here.

class FeasibilityQuestionAnswerMapping(models.Model):
    question = models.ForeignKey(ParentQuestion, on_delete=models.CASCADE, null=True)
    answer = models.ForeignKey(ParentAnswer, on_delete=models.CASCADE, null=True)
    feasibilityweightage = models.FloatField(default=0, null=True, blank=True)
    feasibilitycpiweightage = models.FloatField(default=0, null=True, blank=True)
 
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['question', 'answer'], name="unique_question_answer")
            ]

class BaseCPI(models.Model):
    study_type_choices = (
        ('1', 'GenPop'),
        ('2', 'B2B'),
    )

    study_type = models.CharField(max_length=2,choices=study_type_choices, null=True, blank=True)
    min_loi = models.IntegerField(default=1,
                                validators=[
                                    MaxValueValidator(200),
                                    MinValueValidator(1)
                                ])
    max_loi = models.IntegerField(default=1,
                                validators=[
                                    MaxValueValidator(200),
                                    MinValueValidator(1)
                                ])
    min_incidence = models.IntegerField(default=100,
                                    validators=[
                                        MaxValueValidator(100),
                                        MinValueValidator(1)
                                    ])
    max_incidence = models.IntegerField(default=100,
                                    validators=[
                                        MaxValueValidator(100),
                                        MinValueValidator(1)
                                    ])
    cpi = models.FloatField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['study_type', 'min_loi', 'max_loi', 'min_incidence', 'max_incidence', 'cpi'], name="unique_study_type_cpi_loi_incidence")
            ]

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)



class BaseFeasibilityWeightage(models.Model):
    # study_type_choices = (
    #     ('1', 'GenPop'),
    #     ('2', 'B2B'),
    # )

    # study_type = models.CharField(max_length=2,choices=study_type_choices, null=True, blank=True)
    min_loi = models.IntegerField(default=1,
                                validators=[
                                    MaxValueValidator(200),
                                    MinValueValidator(1)
                                ])
    max_loi = models.IntegerField(default=1,
                                validators=[
                                    MaxValueValidator(200),
                                    MinValueValidator(1)
                                ])
    min_incidence = models.IntegerField(default=100,
                                    validators=[
                                        MaxValueValidator(100),
                                        MinValueValidator(1)
                                    ])
    max_incidence = models.IntegerField(default=100,
                                    validators=[
                                        MaxValueValidator(100),
                                        MinValueValidator(1)
                                    ])
    feasibilityWeightage = models.FloatField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['min_loi', 'max_loi', 'min_incidence', 'max_incidence', 'feasibilityWeightage'], name="unique_validation")
            ]

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)