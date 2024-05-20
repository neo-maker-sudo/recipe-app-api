from abc import ABC, abstractmethod
from typing import Union, Optional
from recipe_menu.domain import model as domain_model

from django.db import IntegrityError
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
        order_by: Optional[Union[str, list[str]]] = None,
        prefetch_model: Optional[str] = None,
    ) -> domain_model.User:
        if prefetch_model is None:
            return self.model.objects.get(**field).to_domain()

        return (
            self.model.objects.prefetch_related(prefetch_model)
            .get(**field)
            .to_domain(using_relate=True, order_by=order_by)
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

    def get(self, field: dict[str, int]):
        return self.model.objects.get(**field).to_domain()

    def add(self):
        pass

    def update(self):
        pass
