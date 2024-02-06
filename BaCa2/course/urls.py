from django.urls import path

from .views import CourseAdmin, CourseView, RoundModelView

app_name = 'course'

urlpatterns = [
    path('<int:course_id>/', CourseView.as_view(), name='course-view'),
    path('<int:course_id>/admin/', CourseAdmin.as_view(), name='course-admin'),
    path('<int:course_id>/round/', RoundModelView.as_view(), name='round-model-view')
]
