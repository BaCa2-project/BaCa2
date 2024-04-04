from django.urls import path

from .views import (
    CourseTask,
    CourseView,
    ResultModelView,
    RoundEditView,
    RoundModelView,
    SubmitModelView,
    SubmitSummaryView,
    TaskEditView,
    TaskModelView
)

app_name = 'course'

urlpatterns = [
    path('', CourseView.as_view(), name='course-view'),
    path('round-edit/', RoundEditView.as_view(), name='round-edit-view'),
    path('task/<int:task_id>/', CourseTask.as_view(), name='task-view'),
    path('task/<int:task_id>/edit/', TaskEditView.as_view(), name='task-edit-view'),
    path('submit/<int:submit_id>/', SubmitSummaryView.as_view(), name='submit-summary-view'),

    path('models/round/', RoundModelView.as_view(), name='round-model-view'),
    path('models/task/', TaskModelView.as_view(), name='task-model-view'),
    path('models/submit/', SubmitModelView.as_view(), name='submit-model-view'),
    path('models/result/', ResultModelView.as_view(), name='result-model-view')
]
