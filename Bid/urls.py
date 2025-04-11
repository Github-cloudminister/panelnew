from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path
from Bid.views import *

app_name = 'Bid'

urlpatterns = [

    path('bidlist', BidListView.as_view({'get':'list','post':'create'})),

    path('bid/<str:bid_number>', BidUpdateView.as_view()),

    path('bid-row/delete/<int:id>', BidDeleteView.as_view({'delete':'destroy'})),

    path('bid/send/<str:bid_number>', BidSendView.as_view()),

    path('bid/set-to-won/<str:bid_number>', BidSettoWonView.as_view()),
    
    path('bid/status/cancel/<str:bid_number>', BidSettoCancelView.as_view()),

]

urlpatterns = format_suffix_patterns(urlpatterns)
