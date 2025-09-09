# reflections/management/commands/seed_test_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
import random

from accounts.models import CustomUser, Staff, Role, Department
from perf.models import (
    AcademicYear,
    SelfReflection,
    ReflectionDomain,
    GrowthPlan,
    Domain,
    Component,
)

fake = Faker()


class Command(BaseCommand):
    help = "Seed IB test users (teachers, HODs, coordinator, principal) and performance reflection data"

    def handle(self, *args, **kwargs):
        # === Roles ===
        teacher_role, _ = Role.objects.get_or_create(name="Teacher")
        hod_role, _ = Role.objects.get_or_create(name="Head of Department")
        coord_role, _ = Role.objects.get_or_create(name="Coordinator")
        principal_role, _ = Role.objects.get_or_create(name="Principal")

        # === IB Departments ===
        departments = []
        ib_departments = [
            "Studies in Language and Literature",
            "Language Acquisition",
            "Individuals and Societies",
            "Sciences",
            "Mathematics",
            "The Arts",
            "Physical and Health Education",
            "Design",
        ]
        for dept_name in ib_departments:
            dept, _ = Department.objects.get_or_create(name=dept_name)
            departments.append(dept)

        # === Create Teachers ===
        teachers = []
        if not Staff.objects.filter(role=teacher_role).exists():
            for i in range(100):
                email = f"teacher{i+1}@school.com"
                user = CustomUser.objects.create_user(email=email, password="password123")
                staff = Staff.objects.create(
                    user=user,
                    fname=fake.first_name(),
                    mname=fake.first_name() if random.random() > 0.5 else "",
                    lname=fake.last_name(),
                    staff_id=f"TCHR{i+1:03d}",
                    role=teacher_role,
                    department=random.choice(departments),
                )
                teachers.append(staff)
            self.stdout.write(self.style.SUCCESS("✅ 20 Teachers created"))
        else:
            teachers = list(Staff.objects.filter(role=teacher_role))
            self.stdout.write(self.style.WARNING("⚠️ Teachers already exist, skipping."))

        # === Create HODs for Each Department ===
        for dept in departments:
            if not Staff.objects.filter(department=dept, is_hod=True).exists():
                hod_user = CustomUser.objects.create_user(
                    email=f"hod_{dept.name.replace(' ', '_').lower()}@test.com",
                    password="password123",
                )
                Staff.objects.create(
                    user=hod_user,
                    fname=fake.first_name(),
                    lname=fake.last_name(),
                    staff_id=f"HOD_{dept.id:03d}",
                    role=hod_role,
                    department=dept,
                    is_hod=True,
                )
                self.stdout.write(self.style.SUCCESS(f"✅ HOD created for {dept.name}"))

        # === Coordinator ===
        if not Staff.objects.filter(role=coord_role).exists():
            coord_user = CustomUser.objects.create_user(
                email="coordinator@test.com", password="password123"
            )
            Staff.objects.create(
                user=coord_user,
                fname=fake.first_name(),
                lname=fake.last_name(),
                staff_id="COORD001",
                role=coord_role,
                department=random.choice(departments),
                is_pc=True,
            )
            self.stdout.write(self.style.SUCCESS("✅ Coordinator created"))

        # === Principal ===
        if not Staff.objects.filter(role=principal_role).exists():
            prin_user = CustomUser.objects.create_user(
                email="principal@test.com", password="password123"
            )
            Staff.objects.create(
                user=prin_user,
                fname=fake.first_name(),
                lname=fake.last_name(),
                staff_id="PRIN001",
                role=principal_role,
                department=random.choice(departments),
                is_vp=True,
            )
            self.stdout.write(self.style.SUCCESS("✅ Principal created"))

        # === Academic Year ===
        year, _ = AcademicYear.objects.get_or_create(
            start_year=2024, end_year=2025, defaults={"is_active": True}
        )

        # === Domains & Components ===
        domains = Domain.objects.prefetch_related("components").all()
        if not domains.exists():
            self.stdout.write(self.style.ERROR("❌ No domains found. Please seed domains/components first."))
            return

        # === Reflections & Growth Plans (no observations) ===
        for teacher in teachers:
            for r in range(5):  # create 5 reflections for each teacher
                reflection = SelfReflection.objects.create(teacher=teacher)

                # Attach 2 random domains
                for domain in random.sample(list(domains), k=min(2, domains.count())):
                    components = list(domain.components.all())
                    if not components:
                        continue

                    strengths = random.sample(components, k=min(2, len(components)))
                    growths = random.sample(components, k=min(2, len(components)))

                    rd = ReflectionDomain.objects.create(
                        reflection=reflection,
                        domain=domain,
                        next_steps=fake.sentence(),
                    )
                    rd.strengths.set(strengths)
                    rd.growths.set(growths)

                # Growth Plan
                gp = GrowthPlan.objects.create(
                    reflection=reflection,
                    academic_year=year,
                    goal_statement=fake.paragraph(nb_sentences=2),
                    indicators_of_success=fake.sentence(),
                    actions=fake.paragraph(nb_sentences=3),
                    timelines="One term",
                    resources=fake.sentence(),
                    evaluator_name=random.choice(["HOD Smith", "Coordinator Jane", "Principal Lee"]),
                    date=timezone.now().date(),
                )
                gp.components_addressed.set(
                    random.sample(list(Component.objects.all()), k=min(3, Component.objects.count()))
                )

        self.stdout.write(self.style.SUCCESS("🎉 IB Staff, 5 reflections + growth plans per teacher seeded (no observations)!"))
