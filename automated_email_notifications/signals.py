from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from automated_email_notifications.models import CounterDetails
from Project.models import Project, ProjectGroup
 
 
@receiver(pre_save, sender=ProjectGroup)
def project_group_status_paused(sender, instance, **kwargs):

    if instance.project_group_status == "Paused":
        CounterDetails.objects.filter(project_group=instance).update(project_group_counter=0)

@receiver(post_save, sender=ProjectGroup)
def project_group_status_paused(sender, instance, **kwargs):

    if instance.project_group_status == "Paused":
        CounterDetails.objects.filter(project_group=instance).update(project_group_counter=0)


        
