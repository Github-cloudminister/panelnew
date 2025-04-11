from django.contrib import admin
from affiliaterouter.models import *

class VisitorsAdmin(admin.ModelAdmin):
    model = Visitors

    search_fields = (
        'source', 'subsource','ruid'
    )

    list_display = (
        'ip_address','genareted_visitor_id','user_agent','source','subsource','ruid','rsid','country','respondent_status','created_at'
    )
class VisitorSurveyRedirectAdmin(admin.ModelAdmin):
    model = VisitorSurveyRedirect

    search_fields = (
        'visitor_id__source', 'visitor_id__subsource','visitor_id__ruid'
    )

    list_display = (
        'survey_number','supplier_survey_url','visitor_id','respondent_status','priority'
    )

class VisitorURLParametersAdmin(admin.ModelAdmin):
    model = VisitorURLParameters

    search_fields = (
        'visitor__source', 'visitor__subsource','visitor__ruid'
    )

    list_display = (
        'visitor','url_extra_params','rsid','pub_id','entry_url','exit_url',
    )


admin.site.register(Visitors,VisitorsAdmin)
admin.site.register(VisitorSurveyRedirect,VisitorSurveyRedirectAdmin)
admin.site.register(AffiliateRouterQuestions)
admin.site.register(AffiliateRouterQuestionsData)
admin.site.register(VisitorURLParameters,VisitorURLParametersAdmin)

