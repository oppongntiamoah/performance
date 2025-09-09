from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import Group
from django.contrib.auth.models import PermissionsMixin
from django.conf import settings



class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        user = self.create_user(email, password)
        user.is_admin = True
        user.is_staff = True
        user.save(using=self._db)
        return user




class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_superuser or super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        return self.is_superuser or super().has_module_perms(app_label)

    @property
    def is_superuser(self):
        return self.is_admin
    


    @property
    def is_staff_user(self):
        return hasattr(self, 'staff') and not self.is_admin


class Role(models.Model):
    name = models.CharField(unique=True, max_length=150)
    

    def __str__(self):
        return self.name



class Department(models.Model):
    name = models.CharField(unique=True, max_length=150)
    

    def __str__(self):
        return self.name


class Staff(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff",
    )
    

    fname = models.CharField(max_length=50)
    mname = models.CharField(max_length=50, null=True, blank=True)
    lname = models.CharField(max_length=50)
    staff_id = models.CharField(max_length=50, unique=True)
    role = models.ForeignKey(
        "Role", related_name="staff_roles", on_delete=models.CASCADE, null=True, blank=True
    )
    department = models.ForeignKey(
        "Department", related_name="staff_members", on_delete=models.CASCADE
    )
    # employment_date = models.DateField(verbose_name="Employment start date")
    date_added = models.DateTimeField(auto_now_add=True)
    # bank_account = models.CharField(max_length=50, blank=True, null=True)
    # bank_name = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_hod = models.BooleanField(default=False)
    is_pc = models.BooleanField(default=False, help_text="Program Coordinator")
    is_vp = models.BooleanField(default=False, help_text="Vice Principal")

    class Meta:
        ordering = ["fname", "lname"]
        indexes = [
            models.Index(fields=["user"]),
        ]
    

    def full_name(self):
        f= f"{self.fname} {self.mname or ''} {self.lname}"
        return f.strip()

    def __str__(self):
        return f"{self.fname} {self.mname or ''} {self.lname}"

