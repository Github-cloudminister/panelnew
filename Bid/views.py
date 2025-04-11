from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from django.conf import settings
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Q
from datetime import date
# third_party module imports
from knox.auth import TokenAuthentication

# all models imports
from Bid.models import *

# Serializers import 
from Bid.serializers import *
from automated_email_notifications.email_configurations import sendEmailSendgripAPIIntegration
from feasibility.views import MyPagenumberPagination


class BidListView(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = bidListSerializer
    pagination_class = MyPagenumberPagination

    def get_queryset(self):
        try:
            pm = self.request.GET.get('pm',None)
            customer = self.request.GET.get('customer',None)
            bidstatus = self.request.GET.get('status',None)
            search = self.request.GET.get('search',None)
            queryset = Bid.objects.filter(
                Q(customer_id = customer) if customer else Q(),
                Q(bid_description__icontains = search) | Q(bid_name__icontains = search) | Q(bid_number__icontains = search) if search else Q(),
                Q(project_manager_id = pm) if pm else Q(),
                Q(bid_status = bidstatus) if bidstatus else Q()).order_by('-id')
            return queryset
        except:
            return None
    
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'user':request.user})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class BidUpdateView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = bidViewSerializer

    def get_object(self, bid_number):
        try:
            return Bid.objects.get(bid_number=bid_number)
        except:
            return None

    def get(self, request, *args, **kwargs):
        if self.get_object(kwargs['bid_number']):
            serializer = self.serializer_class(self.get_object(kwargs['bid_number']))
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'message':'Invalid Bid Number'}, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, *args, **kwargs):
        serializer = self.serializer_class(self.get_object(kwargs['bid_number']), context={'user':request.user}, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(modified_by = request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BidDeleteView(ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    
    def destroy(self, request, id):
        instance = BidRow.objects.get(id=id)
        self.perform_destroy(instance)
        return Response({'message':'It has been deleted successfully!'},status=status.HTTP_204_NO_CONTENT)


class BidSendView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            queryset = Bid.objects.get(bid_number=kwargs['bid_number'])
            if request.data['sent_to_client']=='true':
                queryset.bid_status = '2'
                queryset.save()
                return Response({'message':'Bid sent to client!'},status=status.HTTP_200_OK)
            else:
                return Response({'message':'Bid sent to PM Team!'},status=status.HTTP_200_OK)
        except:
            return Response({'message':'Bid is not available!'},status=status.HTTP_204_NO_CONTENT)


class BidSettoWonView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            queryset = Bid.objects.get(bid_number=kwargs['bid_number'])
            if Project.objects.filter(bid = queryset).exists():
                return Response({'message':'Project Already Created..!'},status=status.HTTP_400_BAD_REQUEST)
            bidrows = BidRow.objects.filter(bid=queryset).values(
                'bid_row_country__country_name','bid_row_language__language_name','bid_row_incidence','bid_row_loi','bid_row_required_N','finalised_row_cpi')
            queryset.bid_status = '3'
            projectmanager = EmployeeProfile.objects.get(id = request.data['project_manager'])
            secondary_project_manager = EmployeeProfile.objects.get(id = request.data['secondary_project_manager'])
            queryset.project_manager = projectmanager
            queryset.secondary_project_manager = secondary_project_manager
            queryset.bid_won_date = date.today()
            queryset.save()
            if settings.SERVER_TYPE == 'production':
                to_emails = list(set([projectmanager.email, secondary_project_manager.email, 'sales@panelviewpoint.com',request.user.email]))
                URL = "https://analytx.panelviewpoint.com/projects/addNew?bid_number="+str(queryset.id)
                cc_emails = 'projects@panelviewpoint.com'
            else:
                to_emails = [projectmanager.email, secondary_project_manager.email,'sanket@panelviewpoint.com']
                URL = "http://192.168.0.100:5000/projects/addNew?bid_number="+str(queryset.id)
                cc_emails = 'sahil@panelviewpoint.com'

            html_message = render_to_string('Project/bidapproved.html',{
                'redirectURL':URL,
                'bidrows':bidrows,
                'projectmanager':projectmanager.first_name,
                'secondary_project_manager':secondary_project_manager.first_name,
                'bid_name' : queryset.bid_name,
                'start_date' : queryset.start_date,
                'end_date' : queryset.end_date,
                'bid_type' : queryset.get_bid_type_display(),
                'bid_description' : queryset.bid_description,
                'customer' : queryset.customer.cust_org_name,
                'bid_category' : queryset.get_bid_category_display(),
                'bid_currency' : queryset.bid_currency.currency_name,
            })
            subject = f'Bid Won - New Project Assigned'
            sendEmailSendgripAPIIntegration(
                from_email = ('bids@panelviewpoint.com'),
                to_emails=to_emails,
                subject=subject,
                html_message=html_message,
                cc_emails = cc_emails
            )
            return Response({'message':'Bid has been set to Won!'},status=status.HTTP_200_OK)
        except:
            return Response({'message':'Bid / Project Manager is not available!'},status=status.HTTP_400_BAD_REQUEST)


class BidSettoCancelView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            queryset = Bid.objects.get(bid_number=kwargs['bid_number'])
            if Project.objects.filter(bid = queryset).exists():
                return Response({'error':'Bid not Cancel, Project Already Created'},status=status.HTTP_400_BAD_REQUEST)
            queryset.bid_status = '4'
            queryset.save()
            
            return Response({'message':'Bid has been set to Cancel!'},status=status.HTTP_200_OK)
        except:
            return Response({'message':'Bid is not available!'},status=status.HTTP_204_NO_CONTENT)