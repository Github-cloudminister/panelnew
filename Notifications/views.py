from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import status
from django.db.models import Count, Q, F

from Notifications.models import *


from knox.auth import TokenAuthentication
from datetime import date, datetime


class EmployeeNotificationListAPI(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):

        count = self.request.GET.get('count')
        if count == 'yes':
            notification_count = EmployeeNotifications.objects.filter(created_for = request.user, is_viewed = False).count()
            return Response({'notification_count':notification_count}, status=status.HTTP_200_OK)
        else:
            notification_obj = EmployeeNotifications.objects.filter(created_for = request.user, is_viewed = False).values(
                'id',
                'description',
                'project_id',
                'project_group_id',
                user_for = F('created_for__first_name'),
                user_to = F('created_by__first_name'),
                project_number = F('project__project_number'),
                date_time = F('created_at'),
            ).order_by('-id')

            return Response(notification_obj, status=status.HTTP_200_OK)
    

    def post(self, request):

        data = request.data

        notification_id = data.get('notification_id')

        notification_obj = EmployeeNotifications.objects.filter(id__in = notification_id)

        notification_obj.update(is_viewed = True, viewed_at = datetime.now())

        return Response({"message":"Notification as view Successfully.!"}, status=status.HTTP_200_OK)



