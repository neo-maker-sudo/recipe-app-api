from typing import Optional
from django.db import models  # noqa
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from recipe.domain import model as domain_model


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

    def add_from_domain(self, user: domain_model.User):
        user = User.objects.create_user(
            email=user.email,
            password=user.password,
            name=user.name,
        )

        return user

    def to_domain(self) -> domain_model.User:
        methods = domain_model.BaseUserMethods(
            check_password=self.check_password
        )

        user = domain_model.User(
            email=self.email,
            name=self.name,
            password=self.password,
            methods=methods,
        )
        user.id = self.id
        return user
