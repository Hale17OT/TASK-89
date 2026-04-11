from django.urls import path

from . import views_users

urlpatterns = [
    path("", views_users.user_list, name="user-list"),
    path("<uuid:pk>/", views_users.user_detail, name="user-detail"),
    path("<uuid:pk>/disable/", views_users.user_disable, name="user-disable"),
    path("<uuid:pk>/enable/", views_users.user_enable, name="user-enable"),
]
