from django.db import models
from django.contrib.auth.models import User
from accounts.models import Staff as Teacher
from accounts.models import Role


class AcademicYear(models.Model):
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField()
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_year"]
        unique_together = ("start_year", "end_year")

    def __str__(self):
        if self.is_active:
            return f"{self.start_year}/{self.end_year} (Current)"
        return f"{self.start_year}/{self.end_year}"


class Domain(models.Model):
    name = models.CharField(max_length=200)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class Component(models.Model):
    domain = models.ForeignKey(
        Domain, on_delete=models.CASCADE, related_name="components"
    )
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.domain.name} - {self.name}"


class SelfReflection(models.Model):
    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name="reflections"
    )
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reflection - {self.teacher}"


class ReflectionDomain(models.Model):
    """Stores strengths and growths per domain in a reflection"""

    reflection = models.ForeignKey(
        SelfReflection, on_delete=models.CASCADE, related_name="reflection_domains"
    )
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)
    strengths = models.ManyToManyField(
        Component, related_name="strength_reflections", blank=True
    )
    growths = models.ManyToManyField(
        Component, related_name="growth_reflections", blank=True
    )
    next_steps = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reflection", "domain"], name="unique_reflection_domain"
            )
        ]

    def __str__(self):
        return f"{self.reflection.teacher} - {self.domain.name}"


class GrowthPlan(models.Model):
    reflection = models.ForeignKey(
        SelfReflection, on_delete=models.CASCADE, related_name="growth_plans"
    )
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    goal_statement = models.TextField()
    components_addressed = models.ManyToManyField(
        Component, related_name="growth_plans"
    )
    indicators_of_success = models.TextField()
    actions = models.TextField()
    timelines = models.CharField(max_length=150)
    resources = models.TextField(blank=True, null=True)
    evaluator_name = models.CharField(max_length=200)
    date = models.DateField()

    def __str__(self):
        return f"Growth Plan ({self.reflection.teacher} - {self.goal_statement[:30]})"


class Observation(models.Model):
    growth_plan = models.OneToOneField(
        GrowthPlan, on_delete=models.CASCADE, related_name="observation"
    )
    hod_comment = models.TextField(blank=True, null=True, verbose_name="HOD comment")
    coordinator_comment = models.TextField(blank=True, null=True)
    prin_comment = models.TextField(
        blank=True, null=True, verbose_name="Vice Principal Comment"
    )
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Observation for {self.growth_plan}"
