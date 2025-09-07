from formtools.wizard.views import SessionWizardView
from django.shortcuts import redirect, render, get_object_or_404
from .models import (
    SelfReflection,
    Domain,
    ReflectionDomain,
    GrowthPlan,
    Component,
    Observation,
)
from .forms import ReflectionDomainForm, GrowthPlanForm, ObservationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from accounts.models import Staff as Teacher
from django.contrib import messages
from .utils import get_reflection_forms

@login_required
def dashboard(request):
    user = request.user

    # HOD dashboard
    if hasattr(user, "staff") and user.staff.is_hod:
        hod = user.staff
        department = hod.department

        # All staff in HOD’s department
        dept_members = department.staff_members.filter(is_active=True)

        # Reflections from department members
        reflections = SelfReflection.objects.filter(teacher__in=dept_members)

        # Count total reflections

        total_teachers = dept_members.count()
        teachers_with_reflections = reflections.values("teacher").distinct().count()

        reflections = list(reflections[:5])
        total_reflections = len(reflections)

        # Completion percentage
        reflection_completion = (
            (teachers_with_reflections / total_teachers) * 100
            if total_teachers > 0
            else 0
        )

        # Growth plan stats
        growth_plans = GrowthPlan.objects.filter(reflection__in=reflections)
        completed_growth_plans = growth_plans.count()

        # Observation status
        obs_pending = growth_plans.filter(observation__isnull=True).count()
        obs_completed = growth_plans.filter(observation__isnull=False).count()

        # Aggregate strengths & growths across department
        strength_counts = (
            ReflectionDomain.objects.filter(reflection__in=reflections)
            .values("domain__name")
            .annotate(total=Count("strengths"))
            .order_by("-total")
        )

        growth_counts = (
            ReflectionDomain.objects.filter(reflection__in=reflections)
            .values("domain__name")
            .annotate(total=Count("growths"))
            .order_by("-total")
        )

        context = {
            "hod": hod,
            "department": department,
            "dept_members": dept_members,
            "reflections": reflections,
            "total_reflections": total_reflections,
            "total_teachers": total_teachers,
            "teachers_with_reflections": teachers_with_reflections,
            "reflection_completion": round(reflection_completion, 1),
            "growth_plans": growth_plans,
            "completed_growth_plans": completed_growth_plans,
            "obs_pending": obs_pending,
            "obs_completed": obs_completed,
            "strength_counts": strength_counts,
            "growth_counts": growth_counts,
        }

        return render(request, "reflections/hod_dashboard.html", context)

    # PC/vp dashboard → only reflections with HOD observations
    elif hasattr(user, "staff") and (user.staff.is_pc or user.staff.is_vp):
        vp = request.user.staff

        # All staff across school
        all_staff = Teacher.objects.filter(is_active=True)

        # Reflections from all staff
        reflections = SelfReflection.objects.all()

        # Count totals
        total_teachers = all_staff.count()
        teachers_with_reflections = reflections.values("teacher").distinct().count()

        reflections = list(reflections[:5])  # latest 5 reflections
        total_reflections = len(reflections)

        # Completion percentage
        reflection_completion = (
            (teachers_with_reflections / total_teachers) * 100
            if total_teachers > 0
            else 0
        )

        # Growth plan stats (all)
        growth_plans = GrowthPlan.objects.filter(reflection__in=reflections)
        completed_growth_plans = growth_plans.count()

        # Observation status
        obs_pending = growth_plans.filter(observation__isnull=True).count()
        obs_completed = growth_plans.filter(observation__isnull=False).count()

        # Aggregate strengths & growths across all reflections
        strength_counts = (
            ReflectionDomain.objects.filter(reflection__in=reflections)
            .values("domain__name")
            .annotate(total=Count("strengths"))
            .order_by("-total")
        )

        growth_counts = (
            ReflectionDomain.objects.filter(reflection__in=reflections)
            .values("domain__name")
            .annotate(total=Count("growths"))
            .order_by("-total")
        )

        context = {
            "total_teachers": total_teachers,
            "teachers_with_reflections": teachers_with_reflections,
            "total_reflections": total_reflections,
            "reflection_completion": reflection_completion,
            "completed_growth_plans": completed_growth_plans,
            "obs_pending": obs_pending,
            "obs_completed": obs_completed,
            "strength_counts": strength_counts,
            "growth_counts": growth_counts,
        }

        return render(request, "reflections/pc_dashboard.html", context)

    # Default → Teacher dashboard
    else:
        teacher = request.user.staff  # Assuming logged-in teacher

        # Reflections
        reflections = SelfReflection.objects.filter(teacher=teacher)
        total_reflections = reflections.count()

        # Domains covered
        domains_covered = (
            ReflectionDomain.objects.filter(reflection__in=reflections)
            .values("domain__name")
            .distinct()
            .count()
        )

        # Strengths and Growths
        strengths_count = (
            ReflectionDomain.objects.filter(reflection__in=reflections)
            .annotate(strengths_num=Count("strengths"))
            .aggregate(total=Count("strengths_num"))["total"]
        )
        growths_count = (
            ReflectionDomain.objects.filter(reflection__in=reflections)
            .annotate(growths_num=Count("growths"))
            .aggregate(total=Count("growths_num"))["total"]
        )

        # Growth Plans
        growth_plans = GrowthPlan.objects.filter(reflection__in=reflections)
        total_growth_plans = growth_plans.count()
        observed_plans = growth_plans.filter(observation__isnull=False).count()

        # Most common strengths and growths components
        top_strengths = (
            Component.objects.filter(strength_reflections__reflection__in=reflections)
            .annotate(count=Count("strength_reflections"))
            .order_by("-count")[:5]
        )
        top_growths = (
            Component.objects.filter(growth_reflections__reflection__in=reflections)
            .annotate(count=Count("growth_reflections"))
            .order_by("-count")[:5]
        )

        context = {
            "total_reflections": total_reflections,
            "domains_covered": domains_covered,
            "strengths_count": strengths_count,
            "growths_count": growths_count,
            "total_growth_plans": total_growth_plans,
            "observed_plans": observed_plans,
            "top_strengths": top_strengths,
            "top_growths": top_growths,
            "reflections": reflections,
        }

        return render(
            request,
            "reflections/teacher_dashboard.html",
            context,
        )


# views.py
class ReflectionWizard(SessionWizardView):
    template_name = "reflections/reflection_wizard.html"

    def get_form_list(self):
        # ✅ Dynamically load based on logged-in user
        return dict(get_reflection_forms(self.request.user))

    def get_form_kwargs(self, step=None):
        kwargs = super().get_form_kwargs(step)

        # For domain steps → pass the domain instance
        if step and step.startswith("domain_"):
            domain_id = int(step.split("_")[1])
            kwargs["domain"] = Domain.objects.get(id=domain_id)

        # For the growth_plan step → restrict to chosen growths
        if step == "growth_plan":
            all_growths = []
            for step_key in self.get_form_list().keys():
                if step_key.startswith("domain_"):
                    data = self.get_cleaned_data_for_step(step_key)
                    if data and "growths" in data:
                        all_growths.extend(data["growths"])
            kwargs["growth_components"] = Component.objects.filter(
                id__in=[g.id for g in all_growths]
            )

        return kwargs

    def done(self, form_list, **kwargs):
        teacher = self.request.user.staff  # accounts.Staff
        reflection = SelfReflection.objects.create(teacher=teacher)

        # Save ReflectionDomain entries
        for step, form in zip(self.get_form_list().keys(), form_list):
            if step.startswith("domain_"):
                domain_id = int(step.split("_")[1])
                domain = Domain.objects.get(id=domain_id)
                rd = ReflectionDomain.objects.create(
                    reflection=reflection,
                    domain=domain,
                    next_steps=form.cleaned_data["next_steps"],
                )
                rd.strengths.set(form.cleaned_data["strengths"])
                rd.growths.set(form.cleaned_data["growths"])

        # Save Growth Plan
        growth_plan_form = form_list[-1]
        gp = growth_plan_form.save(commit=False)
        gp.reflection = reflection
        gp.save()
        growth_plan_form.save_m2m()

        return redirect("reflection_success")


@login_required
def reflection_detail(request, pk):
    reflection = get_object_or_404(SelfReflection, pk=pk)

    # Role checks
    staff = getattr(request.user, "staff", None)
    is_hod = staff and staff.is_hod
    is_pc = staff and staff.is_pc
    is_prin = staff and staff.is_vp  # your field is is_vp, but saving to prin_comment

    if request.method == "POST" and (is_hod or is_pc or is_prin):
        growth_plan_id = request.POST.get("growth_plan_id")
        growth_plan = get_object_or_404(GrowthPlan, pk=growth_plan_id)

        observation, created = Observation.objects.get_or_create(
            growth_plan=growth_plan
        )
        form = ObservationForm(request.POST, instance=observation)

        if form.is_valid():
            obs = form.save(commit=False)  # get instance but don't overwrite yet
            existing_obs = Observation.objects.get(pk=obs.pk)  # get current DB version

            if is_hod:
                obs.hod_comment = form.cleaned_data.get(
                    "hod_comment", existing_obs.hod_comment
                )
                obs.coordinator_comment = existing_obs.coordinator_comment
                obs.prin_comment = existing_obs.prin_comment

            elif is_pc:
                obs.coordinator_comment = form.cleaned_data.get(
                    "coordinator_comment", existing_obs.coordinator_comment
                )
                obs.hod_comment = existing_obs.hod_comment
                obs.prin_comment = existing_obs.prin_comment

            elif is_prin:  # principal / vice principal
                obs.prin_comment = form.cleaned_data.get(
                    "prin_comment", existing_obs.prin_comment
                )
                obs.hod_comment = existing_obs.hod_comment
                obs.coordinator_comment = existing_obs.coordinator_comment

            obs.save()

            return redirect("reflection_detail", pk=reflection.pk)
    else:
        form = ObservationForm()

    return render(
        request,
        "reflections/reflection_detail.html",
        {
            "reflection": reflection,
            "form": form,
            "is_hod": is_hod,
            "is_pc": is_pc,
            "is_prin": is_prin,
        },
    )


@login_required
def department_members(request):
    teacher = get_object_or_404(Teacher, user=request.user)

    # If VP or Principal → see all staff
    if teacher.is_vp or teacher.is_pc:
        members = Teacher.objects.all()
        department = None  # optional, since it's all departments

    # If HOD → see only their department staff
    elif teacher.is_hod:
        department = teacher.department
        members = Teacher.objects.filter(department=department)

    # Otherwise → forbid access
    else:
        return HttpResponseForbidden("You do not have permission to view this page.")

    context = {
        "department": department,
        "members": members,
    }
    return render(request, "reflections/members.html", context)


@login_required
def reflections_list(request):
    user = request.user

    # HOD → see reflections only for teachers in their department
    if hasattr(user, "staff") and user.staff.is_hod:
        dept = user.staff.department
        reflections = SelfReflection.objects.filter(
            teacher__department=dept
        ).select_related("teacher", "teacher__department")

    # VP or PC → see all reflections across departments
    elif hasattr(user, "staff") and (user.staff.is_pc or user.staff.is_vp):
        reflections = SelfReflection.objects.select_related(
            "teacher", "teacher__department"
        )

    # Teachers → see only their own reflections
    else:
        reflections = SelfReflection.objects.filter(teacher__user=user)

    return render(
        request, "reflections/reflections_list.html", {"reflections": reflections}
    )


@login_required
def growthplan_create(request, reflection_id):
    reflection = get_object_or_404(SelfReflection, id=reflection_id)

    # Collect all growth components chosen in this reflection
    selected_components = Component.objects.filter(
        growth_reflections__reflection=reflection
    ).distinct()

    if request.method == "POST":
        form = GrowthPlanForm(request.POST, growth_components=selected_components)
        if form.is_valid():
            growthplan = form.save(commit=False)
            growthplan.reflection = reflection
            growthplan.save()
            form.save_m2m()  # ✅ ensures ManyToMany components are saved
            messages.success(request, "Growth Plan created successfully.")
            return redirect("growthplan_detail", pk=growthplan.id)
    else:
        form = GrowthPlanForm(growth_components=selected_components)

    return render(
        request,
        "growthplans/growthplan_form.html",
        {"form": form, "reflection": reflection},
    )


@login_required
def growthplan_edit(request, pk):
    """Edit growth plan only if there’s no observation"""
    plan = get_object_or_404(GrowthPlan, pk=pk)

    if hasattr(plan, "observation"):
        messages.error(
            request, "You cannot edit this plan because it already has an observation."
        )
        return redirect("growthplan_list")

    if request.method == "POST":
        form = GrowthPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Growth Plan updated successfully.")
            return redirect("growthplan_list")
    else:
        form = GrowthPlanForm(instance=plan)

    return render(request, "growthplans/growthplan_form.html", {"form": form})


from django.forms import modelformset_factory


@login_required
def reflection_edit(request, pk):
    reflection = get_object_or_404(SelfReflection, pk=pk, teacher=request.user.staff)

    # Collect all domain instances for this reflection
    domains = Domain.objects.all()
    reflection_domains = {
        rd.domain_id: rd for rd in reflection.reflection_domains.all()
    }

    # Split growth plans into editable vs locked
    editable_growthplans = reflection.growth_plans.filter(observation__isnull=True)
    locked_growthplans = reflection.growth_plans.filter(observation__isnull=False)

    # Formset only for editable ones
    GrowthPlanFormSet = modelformset_factory(
        GrowthPlan, form=GrowthPlanForm, extra=0, can_delete=True
    )

    domain_forms = []
    if request.method == "POST":
        valid = True
        for domain in domains:
            instance = reflection_domains.get(domain.id)
            form = ReflectionDomainForm(
                request.POST,
                prefix=f"domain_{domain.id}",
                instance=instance,
                domain=domain,
            )
            domain_forms.append((domain, form))
            if not form.is_valid():
                valid = False

        # growth plan formset (only editable ones)
        formset = GrowthPlanFormSet(
            request.POST,
            queryset=editable_growthplans,
            form_kwargs={
                "growth_components": Component.objects.filter(
                    id__in=reflection.reflection_domains.values_list(
                        "growths", flat=True
                    )
                )
            },
        )

        if valid and formset.is_valid():
            # Save domains
            for domain, form in domain_forms:
                rd = form.save(commit=False)
                rd.reflection = reflection
                rd.domain = domain
                rd.save()
                form.save_m2m()

            # Save editable growth plans
            instances = formset.save(commit=False)
            for gp in instances:
                gp.reflection = reflection
                gp.save()
            formset.save_m2m()

            # Handle deletes
            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, "Reflection updated successfully.")
            return redirect("reflection_detail", pk=reflection.pk)

    else:
        for domain in domains:
            instance = reflection_domains.get(domain.id)
            form = ReflectionDomainForm(
                prefix=f"domain_{domain.id}",
                instance=instance,
                domain=domain,
            )
            domain_forms.append((domain, form))

        formset = GrowthPlanFormSet(
            queryset=editable_growthplans,
            form_kwargs={
                "growth_components": Component.objects.filter(
                    id__in=reflection.reflection_domains.values_list(
                        "growths", flat=True
                    )
                )
            },
        )

    return render(
        request,
        "reflections/reflection_edit.html",
        {
            "reflection": reflection,
            "domain_forms": domain_forms,
            "growthplan_formset": formset,
            "editable_growthplans": editable_growthplans,
            "locked_growthplans": locked_growthplans,  # 🚀 pass read-only ones
        },
    )
