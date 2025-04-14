import os
from myproject.credentials import *
from django.contrib.messages import constants as messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
SECRET_KEY = DJANGO_SECRET_KEY
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR=os.path.join(BASE_DIR,'static')


# SERVER_TYPE = 'localhost'
# SERVER_TYPE = 'staging'
SERVER_TYPE = 'production'

PROJECT_APPS = [
    'employee.apps.EmployeeConfig',
    'Bid.apps.BidConfig',
    'CompanyBankDetails.apps.CompanybankdetailsConfig',
    'ClientSupplierInvoicePayment.apps.ClientsupplierinvoicepaymentConfig',
    'Customer.apps.CustomerConfig',
    'SupplierBuyerAPI.apps.SupplierbuyerapiConfig',
    'Supplier.apps.SupplierConfig',
    'Project.apps.ProjectConfig',
    'Surveyentry.apps.SurveyentryConfig',
    'Landingpage.apps.LandingpageConfig',
    'DataDownload.apps.DatadownloadConfig',
    'Questions.apps.QuestionsConfig',
    'Prescreener.apps.PrescreenerConfig',
    'reconciliation.apps.ReconciliationConfig',
    'Logapp.apps.LogappConfig',
    'Invoice.apps.InvoiceConfig',
    'PanelIntegration.apps.PanelintegrationConfig',
    'SupplierAPI.apps.SupplierapiConfig',
    'QuestionSupplierAPI.apps.QuestionsupplierapiConfig',
    'SupplierRouter.apps.SupplierrouterConfig',
    'affiliaterouter.apps.AffiliaterouterConfig',
    'feasibility.apps.FeasibilityConfig',
    'Recontact_Section.apps.RecontactSectionConfig',
    'automated_email_notifications.apps.AutomatedEmailNotificationsConfig',
    'Supplier_Final_Ids_Email.apps.SupplierFinalIdsEmailConfig',
    'scrubsupplierids.apps.ScrubsupplieridsConfig',
    'AdminDashboard.apps.AdmindashboardConfig',
    'SupplierInvoice.apps.SupplierinvoiceConfig',
    'SupplierInviteOnProject.apps.SupplierinviteonprojectConfig',
    'ClientSupplierAPIIntegration.apps.ClientsupplierapiintegrationConfig',
    'ClientSupplierAPIIntegration.TolunaClientAPI.apps.TolunaclientapiConfig',
    'ClientSupplierAPIIntegration.ZampliaClientAPI.apps.ZampliaclientapiConfig',
    'Sales_Commission.apps.SalesCommissionConfig',
    'Ad_Panel_Dashboard.apps.AdPanelDashboardConfig',
    'InitialSetup.apps.InitialsetupConfig',
    'email_template_app.apps.EmailTemplateAppConfig',
    'AutomationAPI.apps.AutomationapiConfig',
    'Notifications.apps.NotificationsConfig',
    'backup.apps.BackupConfig',
]

DEFAULT_APPS = [
    # all apps installation
    

    # django realted modules
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'whitenoise.runserver_nostatic',

    # thrid_party modules
    'rest_framework',
    'rest_framework.authtoken',
    'knox',
    'django_user_agents',
    'corsheaders',
    'django_celery_results',
    'django_celery_beat',
]


settingsvariables = {
    'localhost' : {
        'DEBUG':True,
        'CELERY':True,
        'APP_PATH' : '3Mj4eXMf565PoJ/api-route/',
        'SUPPLIER_DASHBOARD_AUTH_KEY' : 'SSBwysDq[F@sNVDTT5qbr~Z73-j)8zWa2c=',
        'AD_PANEL_DASHBOARD_AUTH_KEY' : 'DD[w-cTSzSjVWsFj)Z3TWW~3sDsZ7853zq@',
        'AFFILIATE_ROUTER_AUTH_KEY' : '29m4EcBjGQmQZKskUKa6r5uygfzrhrfy',
        'AFFILIATE_SUPPLIER_CODE' : '7531d524040564a8',
        'PANEL_WEB_APPLICATION_URL' : 'https://panelstaging.slickservices.in/panelwebapplication/EzFUde5XZ5VktWwxmTjHhVw7XRPnTABUhSArSjxV3H/',
        'PANEL_REDIRECT_URL' : 'https://www.opinionsdeal.com/',        
        'ALLOWED_HOSTS' : ['*'],
        'AFFILIATE_ROUTER_URL' : 'http://192.168.0.5:8001/3Mj4eXMf565PoJ/api-route/affiliaterouter/',
        'SLICK_ROUTER_URL' : 'http://127.0.0.1:8005/w88cYenR1lSBrgMo/api-route/',
        'SURVEY_URL' : 'http://192.168.0.100:5005/',
        'SUPPLIER_DASHBOARD_URL' : 'http://192.168.0.100:8001/ysEYqJd7AWN7mUd6anp4nQ9Rc5a8T8CTGC6jbR/',
        'SUPPLIER_DASHBOARD_FRONTEND_URL' : 'http://192.168.0.100:8200/',
        'AD_PANEL_DASHBOARD_URL' : 'http://192.168.1.109:8009/bTPbZUMbDvdMJjtQ5OAR2mjfroO4c7fjFwnybw/',
        'AD_PANEL_DASHBOARD_FRONTEND_URL' : 'http://192.168.1.104:8500/',
        'AFFILIATE_URL' : 'http://192.168.0.7:9002/',
        'EMAIL_STATICFILE_BASE_URL' : "https://pvpstaging.slickservices.in",
        'OPINIONSDEALSNEW_BASE_URL' : 'http://192.168.0.100:8007/',
        'OPINIONSDEALSNEW_FRONTEND_URL' : 'http://192.168.0.100:4800/',
        'SUPPLIER_INVOICE_DEPLOYE_DATE' : '2024-05-01',
        'CELERY_BROKER_URL' : 'redis://localhost:6379',
        'dbdefault': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'panelviewpointsmdb',
            'USER': 'postgres',
            'PASSWORD': '12345678',
            'HOST': 'localhost',
            'PORT': '5432',
        },
        'dbsecondary': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'panelviewpointsmdb2',
            'USER': 'postgres',
            'PASSWORD': '12345678',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    },
    'staging':{
        'DEBUG':True,
        'CELERY':True,
        'APP_PATH' : '3Mj4eXMf565PoJ/api-route/',
        'SUPPLIER_DASHBOARD_AUTH_KEY' : 'SSBwysDq[F@sNVDTT5qbr~Z73-j)8zWa2c=',
        'AD_PANEL_DASHBOARD_AUTH_KEY' : 'DD[w-cTSzSjVWsFj)Z3TWW~3sDsZ7853zq@',
        'AFFILIATE_ROUTER_AUTH_KEY' : '29m4EcBjGQmQZKskUKa6r5uygfzrhrfy',
        'AFFILIATE_SUPPLIER_CODE' : '30177d1748564625',
        'PANEL_WEB_APPLICATION_URL' : 'https://panelstaging.slickservices.in/panelwebapplication/EzFUde5XZ5VktWwxmTjHhVw7XRPnTABUhSArSjxV3H/',
        'PANEL_REDIRECT_URL' : 'https://www.opinionsdeal.com/',
        'ALLOWED_HOSTS' : ['*'],
        'AFFILIATE_ROUTER_URL' : 'https://pvpstaging.slickservices.in/3Mj4eXMf565PoJ/api-route/affiliaterouter/',
        'SURVEY_URL' : 'https://pvpstaging.slickservices.in/',
        'SUPPLIER_DASHBOARD_URL' : 'https://pvpsupplierdashboard.slickservices.in/ysEYqJd7AWN7mUd6anp4nQ9Rc5a8T8CTGC6jbR/',
        'SUPPLIER_DASHBOARD_FRONTEND_URL' : 'http://192.168.0.2:5005/',
        'AD_PANEL_DASHBOARD_URL' : 'http://192.168.1.109:8003/ysEYqJd7AWN7mUd6anp4nQ9Rc5a8T8CTGC6jbR/',
        'AD_PANEL_DASHBOARD_FRONTEND_URL' : 'http://192.168.1.104:8100/',
        'AFFILIATE_URL' : 'https://pvpstagingrouter.slickservices.in/',
        'EMAIL_STATICFILE_BASE_URL' : "https://pvpstaging.slickservices.in",
        'OPINIONSDEALSNEW_BASE_URL' : 'http://127.0.0.1:8005/',
        'OPINIONSDEALSNEW_FRONTEND_URL' : 'https://opinionsdeal.com/',
        'SLICK_ROUTER_URL' : 'https://api.slickrouter.com/w88cYenR1lSBrgMo/api-route/',
        'SUPPLIER_INVOICE_DEPLOYE_DATE' : '2024-05-01',
        'CELERY_BROKER_URL' : 'redis://localhost:6379',
        'dbdefault': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'pvpstagingdb',
            'USER': 'pvpstagingdbuser',
            'PASSWORD': 'A&M?vR@@bHFyFRUT8347-W$2',
            'HOST': 'localhost',
            'PORT': '',
        },
        'dbsecondary': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'panelviewpointsmdb2',
            'USER': 'postgres',
            'PASSWORD': '12345678',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    },
    'production':{
        'DEBUG':False,
        'CELERY':True,
        'APP_PATH' : '3Mj4eXMf565PoJ/api-route/',
        'SUPPLIER_DASHBOARD_AUTH_KEY' : 'SSBwysDq[F@sNVDTT5qbr~Z73-j)8zWa2c=',
        'AD_PANEL_DASHBOARD_AUTH_KEY' : 'DD[w-cTSzSjVWsFj)Z3TWW~3sDsZ7853zq@',
        'AFFILIATE_ROUTER_AUTH_KEY' : '29m4EcBjGQmQZKskUKa6r5uygfzrhrfy',
        'AFFILIATE_SUPPLIER_CODE' : '297d8e4de123c638',
        'PANEL_WEB_APPLICATION_URL' : 'https://panelstaging.slickservices.in/panelwebapplication/EzFUde5XZ5VktWwxmTjHhVw7XRPnTABUhSArSjxV3H/',
        'PANEL_REDIRECT_URL' : 'https://www.opinionsdeal.com/',
        'ALLOWED_HOSTS' : ['*'],
        'AFFILIATE_ROUTER_URL' : "https://survey2.panelviewpoint.com/3Mj4eXMf565PoJ/api-route/affiliaterouter/",
        'SURVEY_URL' : 'https://survey4.panelviewpoint.com/',
        'SUPPLIER_DASHBOARD_URL' : 'https://enginexapi.panelviewpoint.com/ysEYqJd7AWN7mUd6anp4nQ9Rc5a8T8CTGC6jbR/',
        'SUPPLIER_DASHBOARD_FRONTEND_URL' : 'https://enginx.panelviewpoint.com/',
        'AD_PANEL_DASHBOARD_URL' : 'https://panelapi.advertozy.com/bTPbZUMbDvdMJjtQ5OAR2mjfroO4c7fjFwnybw/',
        'AD_PANEL_DASHBOARD_FRONTEND_URL' : 'https://panelboard.advertozy.com/',
        'AFFILIATE_URL' : 'https://router.panelviewpoint.com/',
        'EMAIL_STATICFILE_BASE_URL' : "https://survey2.panelviewpoint.com",
        'OPINIONSDEALSNEW_BASE_URL' : 'https://panelapi.opinionsdeal.com/',
        'OPINIONSDEALSNEW_FRONTEND_URL' : 'https://opinionsdeal.com/',
        'SLICK_ROUTER_URL' : 'https://api.slickrouter.com/w88cYenR1lSBrgMo/api-route/',
        'SUPPLIER_INVOICE_DEPLOYE_DATE' : '2024-05-01',
        'CELERY_BROKER_URL' : 'redis://192.168.153.48:6379',
        'dbdefault': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'panelview',
            'USER': 'postgres',
            'PASSWORD': 'Uw50Q2wKUVlF23MDp0s0',
            'HOST': '172.236.234.128',
            'PORT': '5432',
            'CONN_MAX_AGE': 30
        }
       
    }
}

DEBUG = settingsvariables[SERVER_TYPE]['DEBUG']
CELERY = settingsvariables[SERVER_TYPE]['CELERY']
APPEND_SLASH = False


TOLUNA_CLIENT_BASE_SETUP_URL = toluna_api_variables[SERVER_TYPE]['TOLUNA_CLIENT_BASE_SETUP_URL']
TOLUNA_CLIENT_BASE_URL = toluna_api_variables[SERVER_TYPE]['TOLUNA_CLIENT_BASE_URL']
TOLUNA_CLIENT_MEMBER_ADD_URL = toluna_api_variables[SERVER_TYPE]['TOLUNA_CLIENT_MEMBER_ADD_URL']
TOLUNA_IP_ES_URL = toluna_api_variables[SERVER_TYPE]['TOLUNA_IP_ES_URL']
TOLUNA_API_AUTH_KEY = toluna_api_variables[SERVER_TYPE]['TOLUNA_API_AUTH_KEY']
TOLUNA_PARTNER_AUTH_KEY = toluna_api_variables[SERVER_TYPE]['TOLUNA_PARTNER_AUTH_KEY']
OFFERWALL_BACKEND_BASE_URL = toluna_api_variables[SERVER_TYPE]['OFFERWALL_BACKEND_BASE_URL']
STAGING_URL = zamplia[SERVER_TYPE]['STAGING_URL']
STAGING_KEY = zamplia[SERVER_TYPE]['STAGING_KEY']
SAGO_BASEURL = sago[SERVER_TYPE]['SAGO_BASEURL']
SAGO_X_MC_SUPPLY_KEY = sago[SERVER_TYPE]['SAGO_X_MC_SUPPLY_KEY']
HMAC_KEY = zamplia[SERVER_TYPE]['HMAC_KEY']
API_KEY = zamplia[SERVER_TYPE]['API_KEY']

# Application definition
INSTALLED_APPS = PROJECT_APPS + DEFAULT_APPS

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


if DEBUG:
    import mimetypes          
    mimetypes.add_type("application/javascript", ".js", True)  

CORS_ALLOW_CREDENTIALS = False

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTH_USER_MODEL = 'employee.EmployeeProfile'

WSGI_APPLICATION = 'myproject.wsgi.application'

APP_PATH = settingsvariables[SERVER_TYPE]['APP_PATH']
SUPPLIER_DASHBOARD_AUTH_KEY = settingsvariables[SERVER_TYPE]['SUPPLIER_DASHBOARD_AUTH_KEY']
AD_PANEL_DASHBOARD_AUTH_KEY = settingsvariables[SERVER_TYPE]['AD_PANEL_DASHBOARD_AUTH_KEY']
AFFILIATE_ROUTER_AUTH_KEY = settingsvariables[SERVER_TYPE]['AFFILIATE_ROUTER_AUTH_KEY']

PANEL_WEB_APPLICATION_URL = settingsvariables[SERVER_TYPE]['PANEL_WEB_APPLICATION_URL']
SUPPLIER_INVOICE_DEPLOYE_DATE = settingsvariables[SERVER_TYPE]['SUPPLIER_INVOICE_DEPLOYE_DATE']
PANEL_REDIRECT_URL = settingsvariables[SERVER_TYPE]['PANEL_REDIRECT_URL']
# DISQO_HASH_KEY = settingsvariables[SERVER_TYPE]['DISQO_HASH_KEY']
ALLOWED_HOSTS = settingsvariables[SERVER_TYPE]['ALLOWED_HOSTS']

AFFILIATE_ROUTER_URL = settingsvariables[SERVER_TYPE]['AFFILIATE_ROUTER_URL']
SLICK_ROUTER_URL = settingsvariables[SERVER_TYPE]['SLICK_ROUTER_URL']
AFFILIATE_SUPPLIER_CODE = settingsvariables[SERVER_TYPE]['AFFILIATE_SUPPLIER_CODE']
SURVEY_URL = settingsvariables[SERVER_TYPE]['SURVEY_URL']
SUPPLIER_DASHBOARD_URL = settingsvariables[SERVER_TYPE]['SUPPLIER_DASHBOARD_URL']
SUPPLIER_DASHBOARD_FRONTEND_URL = settingsvariables[SERVER_TYPE]['SUPPLIER_DASHBOARD_FRONTEND_URL']
AFFILIATE_URL = settingsvariables[SERVER_TYPE]['AFFILIATE_URL']
EMAIL_STATICFILE_BASE_URL = settingsvariables[SERVER_TYPE]['EMAIL_STATICFILE_BASE_URL']
OPINIONSDEALSNEW_BASE_URL = settingsvariables[SERVER_TYPE]['OPINIONSDEALSNEW_BASE_URL']
OPINIONSDEALSNEW_FRONTEND_URL = settingsvariables[SERVER_TYPE]['OPINIONSDEALSNEW_FRONTEND_URL']

AD_PANEL_DASHBOARD_URL = settingsvariables[SERVER_TYPE]['AD_PANEL_DASHBOARD_URL']
AD_PANEL_DASHBOARD_FRONTEND_URL = settingsvariables[SERVER_TYPE]['AD_PANEL_DASHBOARD_FRONTEND_URL']

# Secondary DB used for backup Projects

DATABASES = {
    'default': settingsvariables[SERVER_TYPE]['dbdefault'],
    'read': settingsvariables[SERVER_TYPE]['read'],
}

DATABASE_ROUTERS = ['myproject.database_router.MyDatabaseRouter']


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
# if SERVER_TYPE in ['localhost', 'staging']:
if SERVER_TYPE in ['localhost','staging']:
    if DEBUG:
        STATICFILES_DIRS = [
            STATIC_DIR,
        ]
    else:
        STATIC_ROOT = os.path.join(BASE_DIR, 'static')
        STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

    AWS_STORAGE_BUCKET_NAME = 'pvpstatic'
    AWS_S3_REGION_NAME = 'us-west-2'

    AWS_S3_ACCESS_KEY_ID = 'AKIA2CUNLGCI7MZ5764S'
    AWS_S3_SECRET_ACCESS_KEY = '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'
    AWS_QUERYSTRING_AUTH = False


MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CELERY_BROKER_URL = settingsvariables[SERVER_TYPE]['CELERY_BROKER_URL']
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True