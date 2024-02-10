from django.urls import path

from .views import CourseAdmin, CourseView, RoundModelView, TaskModelView

app_name = 'course'

urlpatterns = [
    path('', CourseView.as_view(), name='course-view'),
    path('admin/', CourseAdmin.as_view(), name='course-admin'),
    path('models/round/', RoundModelView.as_view(), name='round-model-view'),
    path('models/task/', TaskModelView.as_view(), name='task-model-view')
]
