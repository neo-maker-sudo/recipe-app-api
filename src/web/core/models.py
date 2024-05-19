from typing import Optional
from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from recipe_menu.domain import model as domain_model


class UserManager(BaseUserManager):
    """Manager for users."""

    def create_user(
        self, email: str, password: Optional[str] = None, **extra_fields
    ):
        """Create, save and return a new user."""
        if not isinstance(email, str):
            raise ValueError("email must be string data type.")

        if email == "":
            raise ValueError("User must have an email address.")

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, password: str):
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"

    @staticmethod
    def update_from_domain(user: domain_model.User):
        u = User.objects.get(id=user.id)

        if user.name is not None:
            u.name = user.name

        if user.password is not None:
            u.set_password(user.password)

        u.save()

    def add_from_domain(self, user: domain_model.User):
        user = User.objects.create_user(
            email=user.email,
            password=user.password,
            name=user.name,
        )

        return user

    def to_domain(self) -> domain_model.User:
        methods = domain_model.BaseUserMethods(
            check_password=self.check_password,
            refresh_from_db=self.refresh_from_db,
            set_password=self.set_password,
        )

        user = domain_model.User(
            email=self.email,
            name=self.name,
            password=self.password,
            methods=methods,
        )
        user.id = self.id
        return user


class Recipe(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.title
