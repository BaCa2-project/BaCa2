from django.contrib import admin

from .models import Course, User


class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_superuser', 'is_active', 'date_joined', 'last_login']


admin.site.register(User, UserAdmin)
admin.site.register(Course)
