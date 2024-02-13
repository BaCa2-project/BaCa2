from django.urls import path

from .views import (
    CourseAdmin,
    CourseTask,
    CourseTaskAdmin,
    CourseView,
    RoundEditView,
    RoundModelView,
    SubmitModelView,
    TaskModelView
)

app_name = 'course'

urlpatterns = [
    path('', CourseView.as_view(), name='course-view'),
    path('admin/', CourseAdmin.as_view(), name='course-admin'),
    path('round-edit/', RoundEditView.as_view(), name='round-edit-view'),
    path('task/<int:task_id>/', CourseTask.as_view(), name='task-view'),
    path('task/<int:task_id>/admin/', CourseTaskAdmin.as_view(), name='task-admin'),

    path('models/round/', RoundModelView.as_view(), name='round-model-view'),
    path('models/task/', TaskModelView.as_view(), name='task-model-view'),
    path('models/submit/', SubmitModelView.as_view(), name='submit-model-view'),
]
