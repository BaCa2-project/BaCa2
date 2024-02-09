from django.urls import path

from .views import CourseAdmin, CourseView, RoundModelView

app_name = 'course'

urlpatterns = [
    path('', CourseView.as_view(), name='course-view'),
    path('admin/', CourseAdmin.as_view(), name='course-admin'),
    path('models/round/', RoundModelView.as_view(), name='round-model-view')
]
