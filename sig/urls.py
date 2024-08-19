

from django.contrib import admin
from    . import settings
from django.urls import include, path
from scuelo.admin import sics_site
from django.conf.urls.static import static
from  scuelo.views  import  login_view

urlpatterns = [
    path('', login_view, name='login'),
    path('admin/', admin.site.urls),
    path('sics/', sics_site.urls),
    path('accounts/', include('accounts.urls')),
    path("homepage/", include('scuelo.urls')),
     path('reports/', include('report_builder.urls'))
    
] + static(settings.STATIC_URL)
