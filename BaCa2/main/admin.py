from django.contrib import admin
from .models import User, Course
from django.contrib.sites.models import Site
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import (SocialAccount,
                                          SocialApp,
                                          SocialToken)


class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_staff', 'is_superuser', 'is_active', 'date_joined', 'last_login']


admin.site.register(User, UserAdmin)
admin.site.register(Course)

admin.site.unregister(EmailAddress)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialToken)
admin.site.unregister(Site)
