from django.http import HttpResponse
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

# rest_framework imports
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

# third_party module imports
from knox.auth import TokenAuthentication
import pandas as pd
import csv

# in-project imports
from .models import *
from .serializers import *
from Project.models import ProjectGroup



class RecontactFileAPIView(APIView):

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, project_group_number):
    
        resp_obj = Recontact.objects.filter(project_group__project_group_number=project_group_number)

        if True:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=' + str(project_group_number) + '.csv'
            writer = csv.writer(response)
            
            header = ["PID", "RID", "URL", "Project_Group"]
            
            count = 0
            for resp in resp_obj:
                try:
                    old_id_data = resp.pid
                except:
                    old_id_data = 'N/A'
                try:
                    new_id_data = resp.rid
                except:
                    new_id_data = 'N/A'
                try:
                    url_data = resp.url
                except:
                    url_data = 'N/A'
                project_group_data = project_group_number
                    
                content = [old_id_data, new_id_data, url_data, project_group_data]
                if count == 0:
                    writer.writerow(header)
                    count += 1
                writer.writerow(content)
            return response           


    def post(self, request, project_group_number):
        
        try:
            project_group_number_obj = ProjectGroup.objects.get(project_group_number=project_group_number, project_group_client_url_type="3")
                        
            file_obj = request.FILES['file']
            
            if not file_obj.name.endswith('.csv'):
                return Response({'error':'Please upload a CSV file format..!'}, status=status.HTTP_200_OK)
            
            csv_read_obj = pd.read_csv(file_obj)
            
            same_id_uploading = {"data": []}

            recontact_object_create_count = 0

            for i,j in csv_read_obj.iterrows():    
                recontact_qs = Recontact.objects.filter(Q(pid=j["PID"]) | Q(rid=j["RID"]), Q(project_group = project_group_number_obj)).exists()
                
                if recontact_qs:
                    response = {
                        'PID' : j["PID"],
                        'RID' : j["RID"],
                        'URL' : j["URL"],
                    }
                    same_id_uploading["data"].append(response)
                else: 
                    Recontact.objects.create(pid=j["PID"], rid=j["RID"], url=j["URL"], project_group=project_group_number_obj)
                    recontact_object_create_count = recontact_object_create_count + 1
                    
            
            return Response({'msg': 'Uploaded Successful..!', "recontact_objects_created":recontact_object_create_count, "duplicate_count" : len(same_id_uploading['data']), 'duplicates':same_id_uploading}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'error':"Project Group Number not found or Client url type is not set to Recontact.!"}, status=status.HTTP_400_BAD_REQUEST)