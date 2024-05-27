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
        prefetching: bool = False,
        filter_obj: Optional[domain_model.UserFilterObj] = None,
        order_by: Optional[Union[str, list[str]]] = None,
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

        if not prefetching:
            return user

        if filter_obj.model == domain_model.UserFilterModel.RECIPES:
            user._recipes = [
                recipe.to_domain()
                for recipe in self.recipes.filter(
                    self._recipes_queryset(
                        tags=filter_obj.tags,
                        ingredients=filter_obj.ingredients,
                    )
                ).order_by(order_by)
            ]

        elif filter_obj.model == domain_model.UserFilterModel.TAGS:
            user._tags = [
                tag.to_domain()
                for tag in self.tags.filter(
                    self._tags_queryset(filter_obj.tags)
                ).order_by(order_by)
            ]

        elif filter_obj.model == domain_model.UserFilterModel.INGREDIENTS:
            user._ingredients = [
                ingredient.to_domain()
                for ingredient in self.ingredients.filter(
                    self._ingredients_queryset(filter_obj.ingredients)
                ).order_by(order_by)
            ]

        return user

    def _recipes_queryset(
        self, tags: Union[list[str], None], ingredients: Union[list[str], None]
    ):
        q = models.Q()

        if tags is not None:
            q |= models.Q(tags__id__in=tags)

        if ingredients is not None:
            q |= models.Q(ingredients__id__in=ingredients)

        return q

    def _tags_queryset(self, tags: Union[list[str], None]):
        q = models.Q()

        if tags is not None:
            q |= models.Q(tags__id__in=tags)

        return q

    def _ingredients_queryset(self, ingredients: Union[list[str], None]):
        q = models.Q()

        if ingredients is not None:
            q |= models.Q(ingredients__id__in=ingredients)

        return q


class Recipe(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_minutes = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    link = models.CharField(max_length=255, blank=True)

    image = models.ImageField(
        upload_to=settings.RECIPE_MODEL_IMAGEFIELD_LOCATION, null=True
    )

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
        self.image = recipe.image_object.image

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
            image_object=domain_model.RecipeImage(self.image),
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

    def add_from_domain(self, recipe: domain_model.Recipe) -> "Recipe":
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
