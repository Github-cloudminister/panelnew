from django.conf import settings
import requests


# Just For Temporary Testing Purposes for more info check the "third-party-credentials.txt" file from project root directory
# def list_surveys_func():
#     base_url = f'{settings.THEORM_REACH_BASE_URL}/surveys?enc={settings.THEORM_REACH_ENCODING}'
#     headers = {
#     "Content-Type": "application/json",
#     "X-Api-Key": settings.THEORM_REACH_API_KEY
#     }
#     response = requests.get(base_url, headers=headers)
#     return response.json()