from django.db import models
from employee.models import *
from Customer.models import *
from Project.models import Country, Language

# Create your models here.

bid_type = (
        ('1', 'Adhoc'),
        ('2', 'Tracker'),
        ('3', 'IHUT'),
        ('4', 'Community Recruit'),
        ('5', 'Panel Sourcing'),
        ('6', 'Qual'),
        ('7', 'IR Check'),
        ('8', 'Other'),
        ('9', 'Diary'),
        ('10', 'Recontact'),
        ('11', 'Wave Study'),
        ('12', 'Client Supply API Projects'),
        ('13', 'Dummy Project'),
    )

bid_status = (
        ('1', 'Draft'),
        ('2', 'Sent'),
        ('3', 'Won'),
        ('4', 'Cancel'),
    )

class Bid(models.Model):
    bid_category = (
        ('1', 'Automotive'),
        ('2', 'Beauty/Cosmetics'),
        ('3', 'Beverages - Alcoholic'),
        ('4', 'Beverages - Non Alcoholic'),
        ('5', 'Education'),
        ('6', 'Electronics/Computer/Software'),
        ('7', 'Entertainment (Movies, Music, TV, Etc)'),
        ('8', 'Fashion/Clothing'),
        ('9', 'Financial Services/Insurance'),
        ('10', 'Food/Snacks'),
        ('11', 'Gambling/Lottery'),
        ('12', 'Healthcare/Pharmaceuticals'),
        ('13', 'Home (Utilities/Appliances, ...)'),
        ('14', 'Home Entertainment (DVD,VHS)'),
        ('15', 'Home Improvement/Real Estate/Construction'),
        ('16', 'IT (Servers,Databases, Etc)'),
        ('17', 'Personal Care/Toiletries'),
        ('18', 'Pets'),
        ('19', 'Politics'),
        ('20', 'Publishing (Newspaper, Magazines, Books)'),
        ('21', 'Restaurants'),
        ('22', 'Sports/Outdoor'),
        ('23', 'Telecommunications (Phone, Cell Phone, Cable)'),
        ('24', 'Tobacco (Smokers)'),
        ('25', 'Toys'),
        ('26', 'Transportation/Shipping'),
        ('27', 'Travel'),
        ('28', 'Websites/Internet/E-Commerce'),
        ('29', 'other'),
        ('30', 'Sensitive Content'),
        ('31', 'Explicit Content'),
        ('32', 'Gaming'),
        ('33', 'HRDM'),
        ('34', 'Job/Career'),
        ('35', 'Shopping'),
        ('36', 'Parenting'),
        ('37', 'Religion'),
        ('38', 'ITDM'),
        ('39', 'Marketing/Advertising'),
        ('40', 'Other - B2B'),
        ('41', 'Ailment'),
        ('42', 'Social Media'),
        ('43', 'SBOs (Small Business Owners)'),
        ('44', 'Engineering'),
        ('45', 'Manufacturing'),
        ('46', 'Retail'),
        ('47', 'Opinion Elites'),
        ('48', 'Retail'),
    )
    bid_number = models.CharField(max_length=20)
    bid_name = models.CharField(max_length=255)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    bid_type = models.CharField(max_length=2, choices=bid_type)
    bid_description = models.TextField()
    bid_status = models.CharField(max_length=1, choices=bid_status, default='1')
    bid_won_date = models.DateField(null=True)
    
    # Relational fields

    customer = models.ForeignKey(CustomerOrganization, on_delete=models.CASCADE)
    client_contact = models.ForeignKey(ClientContact, on_delete=models.CASCADE)
    project_manager = models.ForeignKey(EmployeeProfile, on_delete = models.SET_NULL, null=True,  related_name = 'bid_project_manager')
    secondary_project_manager = models.ForeignKey(EmployeeProfile, on_delete=models.SET_NULL,null=True,blank=True)
    bid_category = models.CharField(max_length=2, choices=bid_category, default='1',null=True,blank=True)
    bid_currency = models.ForeignKey(Currency, on_delete=models.CASCADE,null=True,blank=True)
    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='bid_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='bid_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)

class BidRow(models.Model):
    bid_row_type = (
        ('1','Gen-Pop'),
        ('2','B2B Easy'),
        ('3','B2B Hard'),
        ('4','Healthcare/Ailment'),
        ('5','consumer'),
        ('6','other')

    )
    bid = models.ForeignKey(Bid, related_name='bidrow', on_delete=models.CASCADE)
    bid_row_type = models.CharField(max_length=1, choices=bid_row_type)
    bid_row_country = models.ForeignKey(Country, on_delete = models.SET_NULL, null=True, )
    bid_row_language = models.ForeignKey(Language, on_delete = models.SET_NULL, null=True, )
    bid_row_incidence = models.IntegerField(default=0)
    bid_row_loi = models.IntegerField(default=0)
    bid_row_required_N = models.IntegerField(default=0)
    bid_row_feasible_N = models.IntegerField(default=0)
    bid_row_cpi = models.FloatField(default=0)
    finalised_row_cpi = models.FloatField(default=0)
    bid_row_total = models.FloatField(default=0)
    bid_row_description = models.TextField(null=True, default="")

    # Common relation Fields
    created_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='bid_row_created_by')
    modified_by = models.ForeignKey(
        EmployeeProfile, on_delete=models.SET_NULL, null=True, related_name='bid_row_modified_by')

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)