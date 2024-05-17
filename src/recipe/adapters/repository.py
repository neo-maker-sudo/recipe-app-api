from abc import ABC, abstractmethod
from recipe.domain import model as domain_model

from django.db import IntegrityError
from django.contrib.auth import get_user_model


class AbstractRepository(ABC):

    @abstractmethod
    def get(self):
        raise NotImplementedError

    @abstractmethod
    def add(self):
        raise NotImplementedError


class UserRepository(AbstractRepository):
    model = get_user_model()

    def get(self, email: str):
        return self.model.objects.get(email=email).to_domain()

    def add(self, user: domain_model.User):
        try:
            return self.model().add_from_domain(user)

        except IntegrityError:
            raise domain_model.UserAlreadyExist
