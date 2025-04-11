from django.conf import settings
import os

DJANGO_SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY', '(_w#em{=*[794}l80(uq-ap0$+lwl=idlkc*txq%#$_48f$f&l^3-*')

def get_credential_details():
    server_type = ''
    if settings.SERVER_TYPE == "localhost":
        server_type = 'staging'
    if settings.SERVER_TYPE == "staging":
        server_type = 'staging'
    if settings.SERVER_TYPE == "production":
        server_type = 'production'

    credentials_dict = {
        "staging":{
            "research_defender_base_url": "https://staging.rtymgt.com",
            "research_defender_api_url": "https://staging.rtymgt.com/api/v2/respondents",
            "research_defender_publisher_api_key": "6d27360a-91bc-4f1f-bc60-516d3db01938",
            "research_defender_private_api_key": "68a03788-e260-4caa-ae4e-33152664d0bb",
            "supplier_id": "381f5187-2007-418d-8013-648d5c4ad02a",
            "supplier_code": "6430",
            "hashing_key":  "aZ4Lr7y63xV2MkS24G23R1kGl7Qqonp5mr6TvwTDEneO91de8pt9pc075wm0XezGD39I471pXV1jWH5514hck",
            "baseurl":  "https://www.samplicio.us"
        },
        "production":{
            "research_defender_base_url": "https://prod.rtymgt.com",
            "research_defender_api_url": "https://prod.rtymgt.com/api/v2/respondents",
            "research_defender_publisher_api_key": "f1573263-96cd-4179-b4f0-604f50834821",
            "research_defender_private_api_key": "a5c4f18a-9070-4193-8c4c-8eb5a84ebb22",
            "supplier_id": "381f5187-2007-418d-8013-648d5c4ad02a",
            "supplier_code": "6430",
            "hashing_key":  "aZ4Lr7y63xV2MkS24G23R1kGl7Qqonp5mr6TvwTDEneO91de8pt9pc075wm0XezGD39I471pXV1jWH5514hck",
            "baseurl":  "https://www.samplicio.us"

        }
    }

    return credentials_dict[server_type]


toluna_api_variables = {
    'localhost':{
        'TOLUNA_CLIENT_BASE_SETUP_URL' : 'https://tws.toluna.com',
        'TOLUNA_CLIENT_BASE_URL' : 'https://tws.toluna.com',
        'TOLUNA_CLIENT_MEMBER_ADD_URL' : 'https://tws.toluna.com',
        'TOLUNA_IP_ES_URL' : 'https://tws.toluna.com',
        'TOLUNA_API_AUTH_KEY' : 'E4016968-C760-4CF9-A887-8C50AE45F24B',
        'TOLUNA_PARTNER_AUTH_KEY' : '341007c6-1c57-4d51-a408-ec6c7c4fd22b',
        'OFFERWALL_BACKEND_BASE_URL' : 'https://opinionsdeal.com/'
    },
    'staging':{
        'TOLUNA_CLIENT_BASE_SETUP_URL' : 'https://tws.toluna.com',
        'TOLUNA_CLIENT_BASE_URL' : 'https://training.ups.toluna.com',
        'TOLUNA_CLIENT_MEMBER_ADD_URL' : 'https://training.ups.toluna.com',
        'TOLUNA_IP_ES_URL' : 'https://training.ups.toluna.com',
        'TOLUNA_API_AUTH_KEY' : '97C3119F-8DDF-4D79-BFA0-04B60D5BA62B',
        'TOLUNA_PARTNER_AUTH_KEY' : '436e3a32-f91c-4c87-bf31-ac49256c79ab',
        'OFFERWALL_BACKEND_BASE_URL' : 'https://opinionsdeal.com/'
    },
    'production':{
        'TOLUNA_CLIENT_BASE_SETUP_URL' : 'https://tws.toluna.com',
        'TOLUNA_CLIENT_BASE_URL' : 'https://tws.toluna.com',
        'TOLUNA_CLIENT_MEMBER_ADD_URL' : 'https://tws.toluna.com',
        'TOLUNA_IP_ES_URL' : 'https://tws.toluna.com',
        'TOLUNA_API_AUTH_KEY' : 'E4016968-C760-4CF9-A887-8C50AE45F24B',
        'TOLUNA_PARTNER_AUTH_KEY' : '341007c6-1c57-4d51-a408-ec6c7c4fd22b',
        'OFFERWALL_BACKEND_BASE_URL' : 'https://opinionsdeal.com/'
    }
}

zamplia = {
    'localhost':{
        'STAGING_URL' : 'https://surveysupply.zamplia.com/api/v1',
        'STAGING_KEY' : 'pU8vCeVzR6JURx8vKpygwDKKwhhIuesO',
        'HMAC_KEY' : '88cdac616c1c11eeb3546045bd60de38',
        'API_KEY' : 'pU8vCeVzR6JURx8vKpygwDKKwhhIuesO',
    },
    'staging':{
        'STAGING_URL' : 'https://surveysupplysandbox.zamplia.com/api/v1',
        'STAGING_KEY' : '8Q8oLJ6yOGQVxF8Bbdr0KZqssIRzL6IF',
        'HMAC_KEY' : 'cb5ff517622111ee9469a02bf4498ff0',
        'API_KEY' : '95d23c5c37dc11ee834a3fd2616e07d6',
    },
     'production':{
        'STAGING_URL' : 'https://surveysupply.zamplia.com/api/v1',
        'STAGING_KEY' : 'pU8vCeVzR6JURx8vKpygwDKKwhhIuesO',
        'HMAC_KEY' : '88cdac616c1c11eeb3546045bd60de38',
        'API_KEY' : 'pU8vCeVzR6JURx8vKpygwDKKwhhIuesO',
    }
}
sago = {
    'localhost':{
        'SAGO_BASEURL' : 'https://api.sample-cube.com/',
        'SAGO_X_MC_SUPPLY_KEY' : '1620:be36c725-729e-4cd9-a2b6-5d70e8a4bf72'
    },
    'staging':{
        'SAGO_BASEURL' : 'https://api.sample-cube.com/',
        'SAGO_X_MC_SUPPLY_KEY' : '1620:be36c725-729e-4cd9-a2b6-5d70e8a4bf72'

    },
     'production':{
        'SAGO_BASEURL' : 'https://api.sample-cube.com/',
        'SAGO_X_MC_SUPPLY_KEY' : '1620:be36c725-729e-4cd9-a2b6-5d70e8a4bf72'
    }
}

lucidAPIsupplier = {
        "api_key": "36D6AC41-7263-4FE7-B19D-6612818DF8C6",
        "staging_base_url": "https://api.samplicio.us",
        "production_base_url": "https://api.samplicio.us",
    }

disqAPIsupplier =  {
        "authkey": "Basic OTcyODc6YWRocDNuWTY4WHV6WmdYWQ==",
        "api_key": "adhp3nY68XuzZgXY",
        "secret_key": "Xa3txgj3xdJCiIdLXC6O3WKs8C1D4tYj",
        "staging_base_url": "https://projects-api.audience.disqo.com",
        "production_base_url": "https://projects-api.audience.disqo.com",
        "client_id": "97287",
        "supplier_id": "54637",
    }