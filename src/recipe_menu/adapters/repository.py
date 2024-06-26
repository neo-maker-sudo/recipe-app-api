from abc import ABC, abstractmethod
from typing import Union, Optional
from recipe_menu.domain import model as domain_model

from django.db import IntegrityError
from django.db.models import Prefetch
from django.apps import apps as django_apps
from django.contrib.auth import get_user_model


class AbstractRepository(ABC):

    @abstractmethod
    def get(self):
        raise NotImplementedError

    @abstractmethod
    def add(self):
        raise NotImplementedError

    @abstractmethod
    def update(self):
        raise NotImplementedError


class UserRepository(AbstractRepository):
    model = get_user_model()

    def get(
        self,
        field: dict[str, Union[str, int]],
        plan: Optional[list[Prefetch]] = None,
        filter_obj: Optional[domain_model.UserFilterObj] = None,
        order_by: Optional[Union[str, list[str]]] = None,
        prefetching: bool = False,
    ) -> domain_model.User:
        if not prefetching:
            return self.model.objects.get(**field).to_domain()

        return (
            self.model.objects.prefetch_related(*plan)
            .get(**field)
            .to_domain(
                filter_obj=filter_obj,
                order_by=order_by,
                prefetching=prefetching,
            )
        )

    def add(self, user: domain_model.User):
        try:
            return self.model().add_from_domain(user)

        except IntegrityError:
            raise domain_model.UserAlreadyExist

    def update(self, user: domain_model.User):
        self.model.update_from_domain(user)


class RecipeRepository(AbstractRepository):
    model = django_apps.get_model("core.Recipe")
    instance = None

    def get(
        self,
        field: dict[str, int],
        prefetch_model: Optional[list[str]] = None,
        select_related: Optional[str] = None,
    ) -> domain_model.Recipe:
        if select_related is not None and prefetch_model is not None:
            self.instance = (
                self.model.objects.select_related(select_related)
                .prefetch_related(*prefetch_model)
                .get(**field)
            )

        elif select_related is not None:
            self.instance = self.model.objects.select_related(
                select_related
            ).get(**field)

        elif prefetch_model is not None:
            self.instance = self.model.objects.prefetch_related(
                *prefetch_model
            ).get(**field)

        else:
            self.instance = self.model.objects.get(**field)

        return self.instance.to_domain()

    def add(self, recipe: domain_model.Recipe):
        self.instance = self.model().add_from_domain(recipe)
        return self.instance

    def update(self, recipe: domain_model.Recipe) -> None:
        if self.instance is not None:
            self.instance.update_from_domain(recipe)

    def delete(self) -> None:
        if self.instance is not None:
            self.instance.delete()


class TagRepository(AbstractRepository):
    model = django_apps.get_model("core.Tag")
    instance = None

    def get(
        self, field: dict[str, int], select_related: Optional[str] = None
    ) -> domain_model.Tag:
        if select_related is not None:
            self.instance = self.model.objects.select_related(
                select_related
            ).get(**field)

        else:
            self.instance = self.model.objects.get(**field)

        return self.instance.to_domain()

    def add(self):
        pass

    def update(self, tag: domain_model.Tag) -> None:
        if self.instance is not None:
            self.instance.update_from_domain(tag)

    def delete(self) -> None:
        if self.instance is not None:
            self.instance.delete()


class IngredientRepository(AbstractRepository):
    model = django_apps.get_model("core.Ingredient")
    instance = None

    def get(
        self, field: dict[str, int], select_related: Optional[str] = None
    ) -> domain_model.Ingredient:
        if select_related is not None:
            self.instance = self.model.objects.select_related(
                select_related
            ).get(**field)

        else:
            self.instance = self.model.objects.get(**field)

        return self.instance.to_domain()

    def add(self):
        pass

    def update(self, ingredient: domain_model.Ingredient) -> None:
        if self.instance is not None:
            self.instance.update_from_domain(ingredient)

    def delete(self) -> None:
        if self.instance is not None:
            self.instance.delete()
