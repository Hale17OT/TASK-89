"""URL routes for system policy management."""
from django.urls import path

from . import views_policy

urlpatterns = [
    path("", views_policy.policy_list, name="policy-list"),
    path("<str:key>/", views_policy.policy_update, name="policy-update"),
]
