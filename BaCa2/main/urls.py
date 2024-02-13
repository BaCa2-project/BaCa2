from django.urls import path

from .views import (
    AdminView,
    CourseModelView,
    CoursesView,
    DashboardView,
    UserModelView,
    change_theme
)

app_name = 'main'

urlpatterns = [
    # -------------------------------------- Model views --------------------------------------- #
    path('models/course/', CourseModelView.as_view(), name='course-model-view'),
    path('models/user/', UserModelView.as_view(), name='user-model-view'),

    # --------------------------------------- Main views --------------------------------------- #
    path('admin/', AdminView.as_view(), name='admin'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('courses/', CoursesView.as_view(), name='courses'),

    path('change_theme', change_theme, name='change-theme'),
]
