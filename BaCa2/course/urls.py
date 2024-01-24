from django.urls import path
from .views import CourseView, CourseAdmin

app_name = 'course'

urlpatterns = [
    path('<int:course_id>/', CourseView.as_view(), name='course-view'),
    path('<int:course_id>/admin/', CourseAdmin.as_view(), name='course-admin'),
]