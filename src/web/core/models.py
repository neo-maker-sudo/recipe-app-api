import os
import uuid

from typing import Optional, Union
from django.conf import settings
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from recipe_menu.domain import model as domain_model


def recipe_image_file_path(instance, filename: str) -> str:
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{ext}"

    return os.path.join("uploads", "recipe", filename)


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

    image = models.ImageField(upload_to=recipe_image_file_path, null=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
    )

    tags = models.ManyToManyField("Tag")
    ingredients = models.ManyToManyField("Ingredient")

    def __str__(self) -> str:
        return self.title

    def _get_or_create_instance(
        self,
        domain_models: list[str],
        model: Union["Tag", "Ingredient"],
        relate_user,
        relate_manager,
    ) -> None:
        # domain_models:
        # is new value being insert into db, like: {"name": "tag1"}
        # relate_manager:
        # for add recipe relation instance (tag, ingredients)
        for entry in domain_models:
            obj, _ = model.objects.get_or_create(
                user=relate_user, **entry.to_dict()
            )
            entry.id = obj.id
            relate_manager.add(obj)

    def update_from_domain(self, recipe: domain_model.Recipe) -> None:
        self.title = recipe.title
        self.description = recipe.description
        self.time_minutes = recipe.time_minutes
        self.price = recipe.price
        self.link = recipe.link

        if self.tags.exists() and recipe.update_tags:
            self.tags.clear()

        if self.ingredients.exists() and recipe.update_ingredients:
            self.ingredients.clear()

        if recipe.update_tags:
            self._get_or_create_instance(
                domain_models=recipe.tags,
                model=Tag,
                relate_user=self.user,
                relate_manager=self.tags,
            )

        if recipe.update_ingredients:
            self._get_or_create_instance(
                domain_models=recipe.ingredients,
                model=Ingredient,
                relate_user=self.user,
                relate_manager=self.ingredients,
            )

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
                else None
            ),
            ingredients=(
                [
                    ingredient.to_domain()
                    for ingredient in self.ingredients.all()
                ]
                if self.ingredients.exists()
                else None
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

        self._get_or_create_instance(
            domain_models=recipe.tags,
            model=Tag,
            relate_user=recipe.user,
            relate_manager=instance.tags,
        )
        self._get_or_create_instance(
            domain_models=recipe.ingredients,
            model=Ingredient,
            relate_user=recipe.user,
            relate_manager=instance.ingredients,
        )

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

    def update_from_domain(self, ingredient: domain_model.Ingredient) -> None:
        self.name = ingredient.name
        self.save()

    def to_domain(self):
        ingredient = domain_model.Ingredient(id=self.id, name=self.name)
        ingredient.user = self.user

        return ingredient
