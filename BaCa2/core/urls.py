from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from main.views import BaCa2LoginView, BaCa2LogoutView, LoginRedirectView
from util.views import FieldValidationView

urlpatterns = [
    path('baca/', admin.site.urls),

    # ------------------------------------- Authentication ------------------------------------- #
    path('', LoginRedirectView.as_view(), name='login-redirect'),
    path('login/', BaCa2LoginView.as_view(), name='login'),
    path('logout/', BaCa2LogoutView.as_view(), name='logout'),

    path('oidc/', include('mozilla_django_oidc.urls')),

    # ------------------------------------------ Apps ------------------------------------------ #
    path('broker_api/', include('broker_api.urls')),
    path('main/', include('main.urls')),
    path('course/<int:course_id>/', include('course.urls')),

    # --------------------------------------- Auxiliary ---------------------------------------- #
    path('field_validation', FieldValidationView.as_view(), name='field-validation'),
]

if settings.MEDIA_OFFLINE_SERVING:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
