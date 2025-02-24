import os
import sys
from django.core.wsgi import get_wsgi_application
# Add the project directory to the sys.path
sys.path.append('/var/www/sicsnasara/prod')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sig.settings_prod')

application = get_wsgi_application()
