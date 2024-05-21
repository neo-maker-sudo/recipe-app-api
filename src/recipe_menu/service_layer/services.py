import dataclasses
from django.db import transaction
from rest_framework_simplejwt.tokens import AccessToken

from recipe_menu.adapters import repository
from recipe_menu.domain import model as domain_model


@transaction.atomic
def register(
    email: str, name: str, password: str, repo: repository.AbstractRepository
):
    user = domain_model.User(email=email, name=name, password=password)
    return repo.add(user)


def login(email: str, password: str, repo: repository.AbstractRepository):
    try:
        user = repo.get({"email": email})

    except repo.model.DoesNotExist:
        raise domain_model.UserNotExist

    if not user.check_password(password):
        raise domain_model.InvalidCredentialsError

    access_token = AccessToken.for_user(user)
    return dataclasses.asdict(
        domain_model.UserTokenCredentials(
            access_token=str(access_token), token_type="Bearer"
        )
    )


def retrieve_user(id: int, repo: repository.AbstractRepository):
    try:
        user = repo.get({"id": id})

    except repo.model.DoesNotExist:
        raise domain_model.UserNotExist

    return user


@transaction.atomic
def update_user(
    id: int, update_fields: dict, repo: repository.AbstractRepository
) -> None:
    try:
        user = repo.get({"id": id})

        domain_model.manage_profile(user, update_fields)

        repo.update(user)

    except repo.model.DoesNotExist:
        raise domain_model.UserNotExist


def retrieve_recipes(
    user_id: int, order_by: str, repo: repository.AbstractRepository
) -> set:
    try:
        user: domain_model.User = repo.get(
            {"id": user_id}, order_by=order_by, prefetch_model="recipes"
        )

    except repo.model.DoesNotExist:
        raise domain_model.UserNotExist

    return user.recipes


def retrieve_recipe(
    id: int, repo: repository.AbstractRepository
) -> domain_model.Recipe:

    try:
        recipe: domain_model.Recipe = repo.get({"id": id})

    except repo.model.DoesNotExist:
        raise domain_model.RecipeNotExist

    return recipe


def create_recipe(
    title: str,
    time_minutes: int,
    price: float,
    user_id: int,
    repo: repository.AbstractRepository,
) -> None:
    try:
        user = repository.UserRepository.model.objects.get(id=user_id)

    except repository.UserRepository.model.DoesNotExist:
        raise domain_model.UserNotExist

    recipe = domain_model.Recipe(
        title=title,
        description="",
        price=price,
        time_minutes=time_minutes,
        link="",
    )
    recipe.mark_user(user)
    repo.add(recipe)
