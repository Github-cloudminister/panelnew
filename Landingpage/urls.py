from django.urls import path
from Landingpage import views

app_name = 'Landingpage'
urlpatterns = [
    
    path('landingpage', views.capture_status),

    path('landingpage-api', views.CaptureStatusLandingPageAPIFunc),
    
    path('postback/statusCapture', views.postbackTracking.as_view()),
]
