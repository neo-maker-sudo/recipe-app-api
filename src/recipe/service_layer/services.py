from django.db import transaction
from recipe.adapters import repository
from recipe.domain import model as domain_model


@transaction.atomic
def register(
    email: str, name: str, password: str, repo: repository.AbstractRepository
):
    user = domain_model.User(email=email, name=name, password=password)
    return repo.add(user)
