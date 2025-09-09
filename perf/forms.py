from django import forms
from .models import ReflectionDomain, GrowthPlan, Component
from .models import Observation

class ReflectionDomainForm(forms.ModelForm):
    strengths = forms.ModelMultipleChoiceField(
        queryset=Component.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"})
    )
    growths = forms.ModelMultipleChoiceField(
        queryset=Component.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"})
    )

    class Meta:
        model = ReflectionDomain
        fields = ["strengths", "growths", "next_steps"]
        widgets = {
            "next_steps": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        domain = kwargs.pop("domain", None)
        super().__init__(*args, **kwargs)
        if domain:
            self.fields["strengths"].queryset = Component.objects.filter(domain=domain)
            self.fields["growths"].queryset = Component.objects.filter(domain=domain)

    def clean(self):
        cleaned_data = super().clean()
        strengths = set(cleaned_data.get("strengths", []))
        growths = set(cleaned_data.get("growths", []))

        if strengths & growths:
            raise forms.ValidationError("Please ensure a component is not both Strength and Growth.")
        return cleaned_data


class GrowthPlanForm(forms.ModelForm):
    class Meta:
        model = GrowthPlan
        fields = [
            "academic_year",
            "goal_statement",
            "components_addressed",
            "indicators_of_success",
            "actions",
            "timelines",
            "resources",
            "evaluator_name",
            "date",
        ]
        widgets = {
            "academic_year": forms.Select(attrs={"class": "form-control"}),
            "goal_statement": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "components_addressed": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            "indicators_of_success": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "actions": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "timelines": forms.TextInput(attrs={"class": "form-control"}),
            "resources": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "evaluator_name": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        growth_components = kwargs.pop("growth_components", None)
        super().__init__(*args, **kwargs)
        if growth_components is not None:
            self.fields["components_addressed"].queryset = growth_components






class ObservationForm(forms.ModelForm):
    class Meta:
        model = Observation
        fields = ["hod_comment", "coordinator_comment", "prin_comment"]
