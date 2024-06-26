from settings import *
from .keep_safe import STAGE_SECRET_KEY, STAGE_DATABASE_PASSWORD


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = STAGE_SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

SITE_NAME = 'SICS NASARA STAGE'

SITE_DOMAIN = 'sics_stage.nasaraperilburkina.org'
ALLOWED_HOSTS.append('sics_stage.nasaraperilburkina.org')
SECRET_KEY = STAGE_SECRET_KEY

DATABASES['default']['PASSWORD'] = STAGE_DATABASE_PASSWORD

CSRF_TRUSTED_ORIGINS = ['https://sics_stage.nasaraperilburkina.org']

LOGGING_BASE_DIR = '/var/log/sicsnasara/stage/'
for h in LOGGING["handlers"]:
    if 'filename' in LOGGING["handlers"][h]:
        LOGGING["handlers"][h]["filename"] = "%s%s" % (LOGGING_BASE_DIR,
                                                       LOGGING["handlers"][h]["filename"].split("/")[-1])
