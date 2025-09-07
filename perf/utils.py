from .models import AcademicYear, Domain
from .forms import ReflectionDomainForm, GrowthPlanForm

def get_active_year():
    return AcademicYear.objects.get(is_active=True)



def get_reflection_forms(user=None):
    forms = []
    if user and hasattr(user, "staff"):
        role = user.staff.role  
        domains = Domain.objects.filter(role=role)
    else:
        domains = Domain.objects.none()

    for domain in domains:
        forms.append((
            f"domain_{domain.id}",
            ReflectionDomainForm,
        ))
    forms.append(("growth_plan", GrowthPlanForm))  # keep your growth plan step
    return forms



# def get_reflection_forms(): 
#     forms = [] 
#     for domain in Domain.objects.all(): forms.append((f"domain_{domain.id}", ReflectionDomainForm)) 
#     forms.append(("growth_plan", GrowthPlanForm)) 
#     return forms