from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Domain, Component, SelfReflection, ReflectionDomain, GrowthPlan, Observation, AcademicYear


admin.site.register(Observation)


class ComponentInline(admin.TabularInline):
    model = Component
    extra = 1


@admin.register(Domain)
class DomainAdmin(ImportExportModelAdmin):  # import-export enabled
    list_display = ("name", "role")
    inlines = [ComponentInline]


class ReflectionDomainInline(admin.StackedInline):
    model = ReflectionDomain
    extra = 1
    filter_horizontal = ("strengths", "growths")  # Nice UI for selecting many components


class GrowthPlanInline(admin.StackedInline):
    model = GrowthPlan
    extra = 1
    filter_horizontal = ("components_addressed",)


@admin.register(SelfReflection)
class SelfReflectionAdmin(ImportExportModelAdmin):  # import-export enabled
    list_display = ("teacher", "date_created")
    search_fields = ("teacher__user__username", "teacher__user__first_name", "teacher__user__last_name")
    inlines = [ReflectionDomainInline, GrowthPlanInline]


@admin.register(Component)
class ComponentAdmin(ImportExportModelAdmin):  # import-export enabled
    list_display = ("name", "domain")
    list_filter = ("domain",)
    search_fields = ("name",)


@admin.register(AcademicYear)
class AcademicYearAdmin(ImportExportModelAdmin):  # import-export enabled
   list_display = ("start_year", "end_year", "is_active")
   list_filter = ("start_year", "end_year")
   search_fields = ("start_year", "end_year")



@admin.register(GrowthPlan)
class GrowthPlanAdmin(ImportExportModelAdmin):  # import-export enabled
    list_display = ("goal_statement", "reflection", "evaluator_name", "date", "academic_year")
    list_filter = ("date", "academic_year")
    search_fields = ("goal_statement", "evaluator_name")
    filter_horizontal = ("components_addressed",)


@admin.register(ReflectionDomain)
class ReflectionDomainAdmin(ImportExportModelAdmin):  # import-export enabled
    list_display = ("reflection", "domain")
    filter_horizontal = ("strengths", "growths")

    def save_model(self, request, obj, form, change):
        # Prevent same component in both strengths & growths
        if set(obj.strengths.all()) & set(obj.growths.all()):
            from django.core.exceptions import ValidationError
            raise ValidationError("A component cannot be both a strength and a growth.")
        super().save_model(request, obj, form, change)
