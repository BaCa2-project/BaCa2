from django.urls import path

from .views import (
    AdminView,
    AnnouncementEditView,
    AnnouncementModelView,
    CourseModelView,
    CoursesView,
    DashboardView,
    DevelopmentTimelineView,
    PermissionModelView,
    ProfileView,
    RoleModelView,
    RoleView,
    UserModelView,
    change_password,
    change_theme
)

app_name = 'main'

urlpatterns = [
    # -------------------------------------- Model views --------------------------------------- #
    path('models/course/', CourseModelView.as_view(), name='course-model-view'),
    path('models/user/', UserModelView.as_view(), name='user-model-view'),
    path('models/role/', RoleModelView.as_view(), name='role-model-view'),
    path('models/permission/', PermissionModelView.as_view(), name='permission-model-view'),
    path('models/announcement/', AnnouncementModelView.as_view(), name='announcement-model-view'),

    # --------------------------------------- Main views --------------------------------------- #
    path('admin/', AdminView.as_view(), name='admin'),
    path('announcement/<int:announcement_id>/', AnnouncementEditView.as_view(),
         name='announcement-edit'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('dev_timeline/', DevelopmentTimelineView.as_view(), name='dev-timeline'),
    path('courses/', CoursesView.as_view(), name='courses'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('role/<int:role_id>/', RoleView.as_view(), name='role'),

    path('change_theme', change_theme, name='change-theme'),
    path('change_password', change_password, name='change-password'),
]
