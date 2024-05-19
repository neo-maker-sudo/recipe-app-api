from abc import ABC, abstractmethod
from typing import Union
from recipe_menu.domain import model as domain_model

from django.db import IntegrityError
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

    def get(self, field: dict[str, Union[str, int]]) -> domain_model.User:
        return self.model.objects.get(**field).to_domain()

    def add(self, user: domain_model.User):
        try:
            return self.model().add_from_domain(user)

        except IntegrityError:
            raise domain_model.UserAlreadyExist

    def update(self, user: domain_model.User):
        self.model.update_from_domain(user)
