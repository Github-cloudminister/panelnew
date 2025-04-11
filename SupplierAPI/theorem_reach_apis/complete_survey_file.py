from django.conf import settings
import requests


# Just For Temporary Testing Purposes for more info check the "third-party-credentials.txt" file from project root directory
# def complete_survey_func():
#     survey_id = 'c16c04e5-6c04-489d-86ba-6a11f4cca590'
#     base_url = f'{settings.THEORM_REACH_BASE_URL}/surveys/{survey_id}/complete?enc={settings.THEORM_REACH_ENCODING}'
#     headers = {
#     "Content-Type": "application/json",
#     "X-Api-Key": settings.THEORM_REACH_API_KEY
#     }
#     response = requests.post(base_url, headers=headers, data={})
#     return response.json()