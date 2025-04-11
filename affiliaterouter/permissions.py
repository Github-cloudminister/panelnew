from django.conf import settings

from rest_framework.permissions import BasePermission

class AffiliateRouterAuthPermission(BasePermission):
    def has_permission(self, request, view):
        auth_token = request.META.get('HTTP_AUTHORIZATION')
        if auth_token != None:
            if settings.AFFILIATE_ROUTER_AUTH_KEY in auth_token.split('Token '):
                return True
        return False