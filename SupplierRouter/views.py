# ********* REST API Libraries **********
import hashlib
from Logapp.views import projectgroup_ad_panel_log
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from knox.auth import TokenAuthentication

# ********* in-project imports **********
from SupplierAPI.models import *
from Project.models import *
from Supplier.models import *
from Supplier.serializers import *
from SupplierAPI.serializers import *
from SupplierRouter.serializers import *
from Project.serializers import *

from SupplierAPI.permissions import *
from django.conf import settings
from django.db.models import F

# ********* third-party libraries **********
from hashlib import blake2b

# Create your views here.

class ProjectGroupRouterSupplierView(ModelViewSet):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)
    serializer_class = ProjectGroupRouterSupplierSerializer
    lookup_field = 'id'

    def get_queryset(self,project_group_id=None):
        return ProjectGroupSupplier.objects.filter(project_group = project_group_id, supplier_org__supplier_type = '3')

    def list(self, request, *args, **kwargs):
        project_group_id = kwargs['project_group_id']
        queryset = self.filter_queryset(self.get_queryset(project_group_id=project_group_id))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        project_group_id = kwargs['project_group_id']
        supplier_qs = self.filter_queryset(self.get_queryset(project_group_id))
        supplier_qs.update(supplier_status = 'Paused')

        data = request.data
        for d in data:
            try:
                supplier_obj = ProjectGroupSupplier.objects.get(supplier_org=d['supplier_org'], project_group = project_group_id)
                supplier_obj.supplier_status = 'Live'
                supplier_obj.completes = d['total_N']
                supplier_obj.clicks = d['clicks']
                supplier_obj.cpi = d['cpi']
                supplier_obj.supplier_completeurl = supplier_obj.supplier_org.supplier_completeurl
                supplier_obj.supplier_terminateurl = supplier_obj.supplier_org.supplier_terminateurl
                supplier_obj.supplier_quotafullurl = supplier_obj.supplier_org.supplier_quotafullurl
                supplier_obj.supplier_securityterminateurl = supplier_obj.supplier_org.supplier_securityterminateurl
                supplier_obj.supplier_internal_terminate_redirect_url = supplier_obj.supplier_org.supplier_internal_terminate_redirect_url
                supplier_obj.supplier_terminate_no_project_available = supplier_obj.supplier_org.supplier_terminate_no_project_available
                supplier_obj.supplier_postbackurl = supplier_obj.supplier_org.supplier_postbackurl
                supplier_obj.save(force_update=True)
                
            except:
                serializer = self.serializer_class(data=d)
                if serializer.is_valid(raise_exception=True):
                    serializer_data = serializer.save(created_by=request.user)
                    serializer_data.supplier_survey_url = serializer_data.project_group.project_group_surveyurl+"&source="+str(serializer_data.supplier_org.id)+"&PID=%%PID%%"
                    sup_obj = SupplierOrganisation.objects.get(id=serializer_data.supplier_org.id)
                    serializer_data.supplier_completeurl = sup_obj.supplier_completeurl
                    serializer_data.supplier_terminateurl = sup_obj.supplier_terminateurl
                    serializer_data.supplier_quotafullurl = sup_obj.supplier_quotafullurl
                    serializer_data.supplier_securityterminateurl = sup_obj.supplier_securityterminateurl
                    serializer_data.supplier_internal_terminate_redirect_url = sup_obj.supplier_internal_terminate_redirect_url
                    serializer_data.supplier_terminate_no_project_available = sup_obj.supplier_terminate_no_project_available
                    serializer_data.supplier_postbackurl = sup_obj.supplier_postbackurl
                    serializer_data.completes = d['total_N']
                    serializer_data.save(force_update=True)
        
        return Response(status=status.HTTP_200_OK)


class RouterSupplierRespondentDetailView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = RouterSupplierRespondentDetailSerializer

    def get(self, request, project_group_num, supplier_id):
        try:
            instance = RespondentDetail.objects.filter(
            source=supplier_id, respondentdetailsrelationalfield__project_group=project_group_num)

            total_visits = instance.count()
            incompletes = instance.filter(resp_status=3).count()
            completes = instance.filter(resp_status=4).count()
            terminates = instance.filter(resp_status=5).count()
            quota_full = instance.filter(resp_status=6).count()
            security_terminate = instance.filter(resp_status=7).count()
            starts = incompletes + completes + terminates + quota_full + security_terminate
            try:
                incidence = (completes/(completes + terminates + quota_full))*100
            except ZeroDivisionError:
                incidence = 0

            survey_details = instance.filter(resp_status=4, url_type='Live')
            get_median = float(median_value(survey_details, 'duration'))
            median_LOI = round(get_median, 0)
            revenue = instance.filter(resp_status=4, url_type='Live').aggregate(Sum("project_group_cpi"))
            expense = instance.filter(resp_status=4, url_type='Live').aggregate(Sum("supplier_cpi"))
            if revenue['project_group_cpi__sum'] == None or expense['supplier_cpi__sum'] == None or revenue['project_group_cpi__sum'] == 0 or expense['supplier_cpi__sum'] == 0:
                margin = 0
            else:
                margin = (revenue['project_group_cpi__sum'] - expense['supplier_cpi__sum']) / revenue['project_group_cpi__sum']

            supplier_stats = {
                "total_visits": total_visits,
                "starts": starts,
                "completes": completes,
                "incompletes": incompletes,
                "quota_full": quota_full,
                "terminates": terminates,
                "security_terminate": security_terminate,
                "incidence": incidence,
                "median_LOI": median_LOI,
                "revenue": revenue['project_group_cpi__sum'],
                "expense": expense['supplier_cpi__sum'],
                "margin": round(margin*100, 2)
            }

            
            return Response({"supplier_statistics":supplier_stats}, status=status.HTTP_200_OK)
        except:
            return Response({'message':'Supplier Not Available!'},status=status.HTTP_204_NO_CONTENT)
        

class ProjectGroupADPanelSupplier(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def get(self, request, project_group_id):

        projct_grp_sub_supplier = ProjectGroupSupplier.objects.only('id','project_group','clicks','cpi','supplier_org','completes').filter(project_group = project_group_id, supplier_org__supplier_type = '5')\
        .values(
            'id',
            'project_group',
            'clicks',
            'cpi',
            supplier_id = F('supplier_org'),
            total_N = F('completes'),
                )
        
        return Response(projct_grp_sub_supplier, status=status.HTTP_200_OK)
    

    def post(self, request, project_group_id):

        data = request.data
        ad_enabled = data['ad_enable_panel']
        cpi = data.get('cpi',0)
        completes = data.get('total_N',0)
        clicks = data.get('clicks',0)
        project_group = ProjectGroup.objects.get(id = project_group_id)
        suppgrp = SupplierOrganisation.objects.get(supplier_type = '5')
        project_grp_supplier = ProjectGroupSubSupplier.objects.filter(project_group_id=project_group.id)
        project_grp_supplier.update(sub_supplier_status = 'Paused')
        
        if project_group.project_group_status != "Booked":
            if ad_enabled == True:
                obj, created = ProjectGroupSupplier.objects.update_or_create(project_group = project_group, supplier_org = suppgrp, defaults={'project_group':project_group, 'supplier_org':suppgrp, 'completes':completes, 'clicks':clicks, 'cpi': cpi ,'supplier_status':'Live','supplier_survey_url':project_group.project_group_surveyurl+"&source="+str(suppgrp.id)+"&PID=%%PID%%",'supplier_completeurl':suppgrp.supplier_completeurl,'supplier_terminateurl':suppgrp.supplier_terminateurl,'supplier_quotafullurl':suppgrp.supplier_quotafullurl,'supplier_securityterminateurl':suppgrp.supplier_securityterminateurl,'supplier_postbackurl':suppgrp.supplier_postbackurl,'supplier_internal_terminate_redirect_url':suppgrp.supplier_internal_terminate_redirect_url,'supplier_terminate_no_project_available':suppgrp.supplier_terminate_no_project_available})

                for d in data['sub_supplier']:

                    try:
                        grp_sub_supplier = ProjectGroupSubSupplier.objects.get(sub_supplier_org = d['sub_supplier_org'], project_group_id = project_group.id)
                        grp_sub_supplier.sub_supplier_status = "Live"
                        grp_sub_supplier.completes = d['total_N']
                        grp_sub_supplier.clicks = d['clicks']
                        grp_sub_supplier.cpi = d['cpi']
                        grp_sub_supplier.sub_supplier_completeurl = grp_sub_supplier.sub_supplier_completeurl
                        grp_sub_supplier.sub_supplier_terminateurl = grp_sub_supplier.sub_supplier_terminateurl
                        grp_sub_supplier.sub_supplier_quotafullurl = grp_sub_supplier.sub_supplier_quotafullurl
                        grp_sub_supplier.sub_supplier_securityterminateurl = grp_sub_supplier.sub_supplier_securityterminateurl
                        grp_sub_supplier.sub_supplier_postbackurl = grp_sub_supplier.sub_supplier_postbackurl
                        grp_sub_supplier.sub_supplier_internal_terminate_redirect_url = grp_sub_supplier.sub_supplier_internal_terminate_redirect_url
                        grp_sub_supplier.sub_supplier_terminate_no_project_available = grp_sub_supplier.sub_supplier_terminate_no_project_available
                        grp_sub_supplier.save(force_update=True)
                        project_group.ad_enable_panel = True
                        project_group.save(force_update=True)
                        projectgroup_ad_panel_log(True,False,project_group.id,grp_sub_supplier.id,request.user)
                    
                    except:
                        sup_obj = SubSupplierOrganisation.objects.get(id=d['sub_supplier_org'])
                        projcvt_grp_sub_supplier = ProjectGroupSubSupplier.objects.create(project_group_id = project_group.id,project_group_supplier_id = obj.id,sub_supplier_org_id = sup_obj.id,completes = d['total_N'],clicks = d['clicks'], cpi = d['cpi'])

                        projcvt_grp_sub_supplier.sub_supplier_survey_url = obj.supplier_survey_url.replace("PID=%%PID%%",f"sub_sup={str(projcvt_grp_sub_supplier.sub_supplier_org.sub_supplier_code)}&PID=%%PID%%")
                        projcvt_grp_sub_supplier.sub_supplier_completeurl = sup_obj.sub_supplier_completeurl 
                        projcvt_grp_sub_supplier.sub_supplier_terminateurl = sup_obj.sub_supplier_terminateurl 
                        projcvt_grp_sub_supplier.sub_supplier_quotafullurl = sup_obj.sub_supplier_quotafullurl 
                        projcvt_grp_sub_supplier.sub_supplier_securityterminateurl = sup_obj.sub_supplier_securityterminateurl 
                        projcvt_grp_sub_supplier.sub_supplier_postbackurl = sup_obj.sub_supplier_postbackurl 
                        projcvt_grp_sub_supplier.sub_supplier_internal_terminate_redirect_url = sup_obj.sub_supplier_internal_terminate_redirect_url 
                        projcvt_grp_sub_supplier.sub_supplier_terminate_no_project_available = sup_obj.sub_supplier_terminate_no_project_available
                        projcvt_grp_sub_supplier.save() 

                        project_group.ad_enable_panel = True
                        project_group.save(force_update=True)

                        projectgroup_ad_panel_log(True,False,project_group.id,projcvt_grp_sub_supplier.id,request.user)
                if data['sub_supplier'] == []:
                    projectgroup_ad_panel_log(False,True,project_group.id,'',request.user)

            else:
                ProjectGroupSupplier.objects.filter(project_group = project_group).update(supplier_status = 'Paused')
                
                project_group.ad_enable_panel = False
                project_group.save(force_update=True, update_fields=['ad_enable_panel'])

                projectgroup_ad_panel_log(False,True,project_group.id,'',request.user)
        
            return Response({"message":"AD Panel Update Successfully..!"},status=status.HTTP_200_OK)
        else:
            return Response({"error":"Please Survey Live First.!"}, status=status.HTTP_400_BAD_REQUEST)
        

class SubSupplierAddMultipleSurveyAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):

        data = request.data
        # ad_enabled = data['ad_enable_panel']
        cpi = data.get('cpi',0)
        completes = data.get('total_N',0)
        clicks = data.get('clicks',0)
        project_group_id = data.get('project_group_id')
        sub_supplier_id = data.get('sub_supplier_id')
        sub_supplier_completeurl = data.get('sub_supplier_completeurl')
        sub_supplier_terminateurl = data.get('sub_supplier_terminateurl')
        sub_supplier_quotafullurl = data.get('sub_supplier_quotafullurl')
        sub_supplier_securityterminateurl = data.get('sub_supplier_securityterminateurl')
        sub_supplier_postbackurl = data.get('sub_supplier_postbackurl')
        sub_supplier_internal_terminate_redirect_url = data.get('sub_supplier_internal_terminate_redirect_url')
        sub_supplier_terminate_no_project_available = data.get('sub_supplier_terminate_no_project_available')

        try:
            suppgrp = SupplierOrganisation.objects.get(supplier_type = '5')
        except:
            return Response({"error":"Please Create A New Supplier AD Panel-Type-5.!"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            for survey_id in project_group_id:
                project_grp_obj = ProjectGroup.objects.get(id = survey_id)
                project_grp_obj.ad_enable_panel = True
                project_grp_obj.save()

                obj, created = ProjectGroupSupplier.objects.update_or_create(project_group = project_grp_obj, supplier_org = suppgrp, defaults={'project_group':project_grp_obj, 'supplier_org':suppgrp, 'completes':completes, 'clicks':clicks, 'cpi': cpi ,'supplier_status':'Live','supplier_survey_url':project_grp_obj.project_group_surveyurl+"&source="+str(suppgrp.id)+"&PID=%%PID%%",'supplier_completeurl':suppgrp.supplier_completeurl,'supplier_terminateurl':suppgrp.supplier_terminateurl,'supplier_quotafullurl':suppgrp.supplier_quotafullurl,'supplier_securityterminateurl':suppgrp.supplier_securityterminateurl,'supplier_postbackurl':suppgrp.supplier_postbackurl,'supplier_internal_terminate_redirect_url':suppgrp.supplier_internal_terminate_redirect_url,'supplier_terminate_no_project_available':suppgrp.supplier_terminate_no_project_available})

                sup_obj = SubSupplierOrganisation.objects.get(id=sub_supplier_id)
                projcvt_grp_sub_supplier, prjct_grp_sub_supp_created = ProjectGroupSubSupplier.objects.update_or_create(
                    project_group_id = project_grp_obj.id,project_group_supplier_id = obj.id,sub_supplier_org_id = sup_obj.id, 
                    defaults={
                        'completes' : completes,
                        'clicks' : clicks,
                        'cpi' : cpi,
                    })

                if prjct_grp_sub_supp_created:
                    projcvt_grp_sub_supplier.sub_supplier_survey_url = obj.supplier_survey_url.replace("PID=%%PID%%",f"sub_sup={str(projcvt_grp_sub_supplier.sub_supplier_org.sub_supplier_code)}&PID=%%PID%%")

                projcvt_grp_sub_supplier.sub_supplier_completeurl = sub_supplier_completeurl 
                projcvt_grp_sub_supplier.sub_supplier_terminateurl = sub_supplier_terminateurl 
                projcvt_grp_sub_supplier.sub_supplier_quotafullurl = sub_supplier_quotafullurl 
                projcvt_grp_sub_supplier.sub_supplier_securityterminateurl = sub_supplier_securityterminateurl 
                projcvt_grp_sub_supplier.sub_supplier_postbackurl = sub_supplier_postbackurl 
                projcvt_grp_sub_supplier.sub_supplier_internal_terminate_redirect_url = sub_supplier_internal_terminate_redirect_url 
                projcvt_grp_sub_supplier.sub_supplier_terminate_no_project_available = sub_supplier_terminate_no_project_available
                projcvt_grp_sub_supplier.save()

            return Response({"message":"AD Panel Update Successfully..!"},status=status.HTTP_200_OK)
        except:
            return Response({'error':'Something went wrong!'}, status=status.HTTP_400_BAD_REQUEST)

