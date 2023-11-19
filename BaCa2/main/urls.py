from django.urls import path
from .views import (CourseModelView,
                    UserModelView,

                    DashboardView,
                    CoursesView,
                    JsonView,
                    AdminView,
                    FieldValidationView,

                    change_theme)

app_name = 'main'

urlpatterns = [
    # Model management views
    path('models/course', CourseModelView.as_view(), name='course-model-view'),
    path('models/user', UserModelView.as_view(), name='user-model-view'),

    path('admin', AdminView.as_view(), name='admin'),
    path('dashboard', DashboardView.as_view(), name='dashboard'),
    path('courses', CoursesView.as_view(), name='courses'),

    path('json/<str:model_name>-<str:access_mode>', JsonView.as_view(), name='json'),
    path('field_validation', FieldValidationView.as_view(), name='field-validation'),

    path('change_theme', change_theme, name='change-theme'),
]
