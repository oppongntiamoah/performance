from django.urls import path, include
from .views import (
    ReflectionWizard,
    dashboard,
    reflection_detail,
    department_members,
    reflections_list,
    growthplan_create,
    growthplan_edit,
    reflection_edit,
    teacher_reflections,
    growth_plan_detail,
)
from django.shortcuts import render
from django.contrib.auth import views as auth_views
from .utils import get_reflection_forms

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path(
        "reflection/add/",
        ReflectionWizard.as_view(get_reflection_forms()),
        name="add_reflection",
    ),
    path(
        "reflection/success/",
        lambda request: render(request, "reflections/success.html"),
        name="reflection_success",
    ),
    path("reflections/<int:pk>/", reflection_detail, name="reflection_detail"),
    path("teachers/", department_members, name="department_members"),
    path("reflections/", reflections_list, name="reflections_list"),
    path("reflections/<int:pk>/edit/", reflection_edit, name="reflection_edit"),
    
    
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    path("gp/<int:reflection_id>/add/", growthplan_create, name="growthplan_create"),
    path("gp/<int:pk>/edit/", growthplan_edit, name="growthplan_edit"),
    # path("<int:pk>/delete/", growthplan_delete, name="growthplan_delete"),
    path("teacher/<int:teacher_id>/reflections/", teacher_reflections, name="teacher_reflections"),
    path("gp/<int:pk>/", growth_plan_detail, name="growth_plan_detail"),
]
