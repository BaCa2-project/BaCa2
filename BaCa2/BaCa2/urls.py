from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from main.views import BaCa2LoginView, BaCa2LogoutView, LoginRedirectView
from util.views import FieldValidationView

urlpatterns = [
    path('baca/', admin.site.urls),

    # ------------------------------------- Authentication ------------------------------------- #
    path('', LoginRedirectView.as_view(), name='login-redirect'),
    path('login/', BaCa2LoginView.as_view(), name='login'),
    path('logout/', BaCa2LogoutView.as_view(), name='logout'),

    # ------------------------------------------ Apps ------------------------------------------ #
    path('broker_api/', include('broker_api.urls')),
    path('main/', include('main.urls')),
    path('course/', include('course.urls')),

    # --------------------------------------- Auxiliary ---------------------------------------- #
    path('field_validation', FieldValidationView.as_view(), name='field-validation'),
]

urlpatterns += staticfiles_urlpatterns()
