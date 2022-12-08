from django.contrib import admin

# Register your models here.
from .models import Question, Choice

# admin.site.register(Question)

admin.site.register(Choice)

@admin.register(Question)
class AdminQuestion(admin.ModelAdmin):
    list_display = ['pk', 'question_text', 'pub_date']
    search_fields = ['question_text', ]
    date_hierarchy = 'pub_date'
    list_filter = ['question_text', ]
