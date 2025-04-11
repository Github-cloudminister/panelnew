from django.urls import path

from Customer import views

urlpatterns = [

    # Customer Organization urls
    path('customer', views.CustomerView.as_view()),

    path('customer/<int:customer_id>', views.CustomerUpdateView.as_view()),

    # Customer Contact urls
    path('client-contact', views.ClientContactView.as_view()),

    path('client-contact/<int:client_contact_id>',views.ClientContactUpdateView.as_view()),

    # Client Contacts list according to Customer Organization urls
    path('customer/client/<int:customer_id>',views.ClientDetailCustomerView.as_view()),

    # Currency urls
    path('currency', views.CurrencyView.as_view())

]