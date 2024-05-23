from typing import Optional, Union
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
    def update_from_domain(user: domain_model.User) -> None:
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

    def to_domain(
        self,
        using_relate: bool = False,
        order_by: Optional[Union[str, list[str]]] = None,
        prefetch_model: Optional[str] = None,
    ) -> domain_model.User:
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

        # if prefetch_model is recipes__tags:
        # user list recipe and recipe need to list its mark tags
        # so relation will be:
        # User -> Recipe (one to many), Recipe -> Tag (many to many)
        if using_relate and prefetch_model == "recipes__tags":
            user._recipes = [
                recipe.to_domain()
                for recipe in self.recipes.all().order_by(order_by)
            ]

        # if prefetch_model is tags:
        # user retrieve all of tags being created.
        if using_relate and prefetch_model == "tags":
            user._tags = [
                tag.to_domain() for tag in self.tags.all().order_by(order_by)
            ]

        # if prefetch_model is ingredients:
        # user retrieve all of ingredients being created.
        if using_relate and prefetch_model == "ingredients":
            user._ingredients = [
                ingredient.to_domain()
                for ingredient in self.ingredients.all().order_by(order_by)
            ]

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
        related_name="recipes",
    )

    tags = models.ManyToManyField("Tag")
    ingredients = models.ManyToManyField("Ingredient")

    def __str__(self) -> str:
        return self.title

    def _get_or_create_tag(self, recipe: domain_model.Recipe) -> None:
        for tag in recipe.tags:
            tag_obj, _ = Tag.objects.get_or_create(
                user=self.user,
                **tag,
            )
            self.tags.add(tag_obj)

    def update_from_domain(self, recipe: domain_model.Recipe) -> None:
        self.title = recipe.title
        self.description = recipe.description
        self.time_minutes = recipe.time_minutes
        self.price = recipe.price
        self.link = recipe.link

        if self.tags.exists():
            self.tags.clear()
            self._get_or_create_tag(recipe)

        else:
            self._get_or_create_tag(recipe)

        self.save()

    def to_domain(self) -> domain_model.Recipe:
        recipe = domain_model.Recipe(
            title=self.title,
            description=self.description,
            time_minutes=self.time_minutes,
            price=self.price,
            link=self.link,
            tags=(
                [tag.to_domain() for tag in self.tags.all()]
                if self.tags.exists()
                else []
            ),
        )

        recipe.id = self.id
        recipe.user = self.user

        return recipe

    def add_from_domain(
        self, recipe: domain_model.Recipe
    ) -> domain_model.Recipe:
        instance = Recipe.objects.create(
            title=recipe.title,
            description=recipe.description,
            time_minutes=recipe.time_minutes,
            price=recipe.price,
            link=recipe.link,
            user=recipe.user,
        )

        for tag in recipe.tags:
            tag_obj, _ = Tag.objects.get_or_create(
                user=recipe.user,
                **tag,
            )
            instance.tags.add(tag_obj)

        return instance


class Tag(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tags",
    )

    def __str__(self):
        return self.name

    def update_from_domain(self, tag: domain_model.Tag) -> None:
        self.name = tag.name
        self.save()

    def to_domain(self) -> domain_model.Tag:
        tag = domain_model.Tag(name=self.name)

        tag.id = self.id
        tag.user = self.user

        return tag


class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="ingredients",
    )

    def __str__(self):
        return self.name

    def to_domain(self):
        ingredient = domain_model.Ingredient(id=self.id, name=self.name)
        ingredient.user = self.user

        return ingredient
