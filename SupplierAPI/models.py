from django.db import models

from Project.models import Language
from employee.models import Country

# Create your models here.


class LucidCountryLanguageMapping(models.Model):
    lanugage_id = models.ForeignKey(Language, on_delete=models.CASCADE)
    country_id = models.ForeignKey(Country, on_delete=models.CASCADE)
    lucid_country_lang_id = models.CharField(max_length=100, unique=True)
    lucid_language_code = models.CharField(max_length=100, unique=True)
    lucid_language_name = models.CharField(max_length=300, unique=True)


    def __str__(self):
        return '{}-{}'.format(self.country_id.country_name, self.lanugage_id.language_code)


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['lanugage_id', 'country_id'], name="unique_language_country")
            ]
