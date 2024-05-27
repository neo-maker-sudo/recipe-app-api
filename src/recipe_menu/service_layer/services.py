import dataclasses
from typing import Optional

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
    user_id: int,
    filter_obj: domain_model.UserFilterObj,
    order_by: str,
    repo: repository.AbstractRepository,
) -> set:

    plan = domain_model.determine_prefetch_plan(filter_obj)

    try:
        user: domain_model.User = repo.get(
            {"id": user_id},
            plan=plan,
            filter_obj=filter_obj,
            order_by=order_by,
            prefetching=True,
        )

    except repo.model.DoesNotExist:
        raise domain_model.UserNotExist

    return user.recipes


def retrieve_recipe(
    id: int, repo: repository.AbstractRepository
) -> domain_model.Recipe:

    try:
        recipe: domain_model.Recipe = repo.get(
            {"id": id}, prefetch_model=["tags", "ingredients"]
        )

    except repo.model.DoesNotExist:
        raise domain_model.RecipeNotExist

    return recipe


def create_recipe(
    title: str,
    time_minutes: int,
    price: float,
    description: str,
    link: str,
    user_id: int,
    repo: repository.AbstractRepository,
    tags: Optional[list[str]] = None,
    ingredients: Optional[list[str]] = None,
) -> domain_model.Recipe:
    try:
        user = repository.UserRepository.model.objects.get(id=user_id)

    except repository.UserRepository.model.DoesNotExist:
        raise domain_model.UserNotExist

    recipe = domain_model.Recipe(
        title=title,
        description=description,
        price=price,
        time_minutes=time_minutes,
        link=link,
        tags=(
            [domain_model.Tag(name=tag["name"]) for tag in tags]
            if tags is not None
            else None
        ),
        ingredients=(
            [
                domain_model.Ingredient(name=ingredient["name"])
                for ingredient in ingredients
            ]
            if ingredients is not None
            else None
        ),
    )
    recipe.mark_user(user)
    repo.add(recipe)

    return recipe


@transaction.atomic
def update_recipe(
    id: int,
    update_fields: dict,
    user_id: int,
    repo: repository.AbstractRepository,
) -> domain_model.Recipe:
    prefetch_model = []

    if update_fields.get("tags", None) is not None:
        prefetch_model.append("tags")

    if update_fields.get("ingredients", None) is not None:
        prefetch_model.append("ingredients")

    try:
        recipe: domain_model.Recipe = repo.get(
            {"id": id}, select_related="user", prefetch_model=prefetch_model
        )

    except repo.model.DoesNotExist:
        raise domain_model.RecipeNotExist

    if not recipe.check_ownership(user_id):
        raise domain_model.RecipeNotOwnerError

    recipe.update_detail(update_fields)

    repo.update(recipe)

    return recipe


@transaction.atomic
def update_recipe_image(
    id: int,
    image_object: domain_model.RecipeImage,
    user_id: int,
    repo: repository.AbstractRepository,
) -> domain_model.Recipe:
    try:
        recipe: domain_model.Recipe = repo.get(
            {"id": id}, select_related="user"
        )

    except repo.model.DoesNotExist:
        raise domain_model.RecipeNotExist

    if not recipe.check_ownership(user_id):
        raise domain_model.RecipeNotOwnerError

    recipe.update_image_object(image_object)
    repo.update(recipe)

    return recipe


@transaction.atomic
def delete_recipe(
    id: int,
    user_id: int,
    repo: repository.AbstractRepository,
) -> None:
    recipe: domain_model.Recipe = repo.get({"id": id}, select_related="user")

    if not recipe.check_ownership(user_id):
        raise domain_model.RecipeNotOwnerError

    del recipe
    repo.delete()


def retrieve_tags(
    user_id: int,
    filter_obj: domain_model.UserFilterObj,
    order_by: str,
    repo: repository.AbstractRepository,
):
    plan = domain_model.determine_prefetch_plan(filter_obj)

    try:
        user: domain_model.User = repo.get(
            {"id": user_id},
            plan=plan,
            filter_obj=filter_obj,
            order_by=order_by,
            prefetching=True,
        )

    except repo.model.DoesNotExist:
        raise domain_model.UserNotExist

    return user.tags


@transaction.atomic
def update_tag(
    id: int,
    update_fields: dict,
    user_id: int,
    repo: repository.AbstractRepository,
):
    try:
        tag: domain_model.Tag = repo.get({"id": id}, select_related="user")

    except repo.model.DoesNotExist:
        raise domain_model.TagNotExist

    if not tag.check_ownership(user_id):
        raise domain_model.TagNotOwnerError

    tag.update_detail(update_fields)

    repo.update(tag)

    return tag


@transaction.atomic
def delete_tag(
    id: int,
    user_id: int,
    repo: repository.AbstractRepository,
) -> None:
    try:
        tag: domain_model.Tag = repo.get({"id": id}, select_related="user")

    except repo.model.DoesNotExist:
        raise domain_model.TagNotExist

    if not tag.check_ownership(user_id):
        raise domain_model.TagNotOwnerError

    del tag
    repo.delete()


def retrieve_ingredients(
    user_id: int,
    filter_obj: domain_model.UserFilterObj,
    order_by: str,
    repo: repository.AbstractRepository,
):
    plan = domain_model.determine_prefetch_plan(filter_obj)

    try:
        user: domain_model.User = repo.get(
            {"id": user_id},
            plan=plan,
            filter_obj=filter_obj,
            order_by=order_by,
            prefetching=True,
        )

    except repo.model.DoesNotExist:
        raise domain_model.UserNotExist

    return user.ingredients


@transaction.atomic
def update_ingredient(
    id: int,
    update_fields: dict,
    user_id: int,
    repo: repository.AbstractRepository,
):
    try:
        ingredient: domain_model.Ingredient = repo.get(
            {"id": id}, select_related="user"
        )

    except repo.model.DoesNotExist:
        raise domain_model.IngredientNotExist

    if not ingredient.check_ownership(user_id):
        raise domain_model.IngredientNotOwnerError

    ingredient.update_detail(update_fields)

    repo.update(ingredient)

    return ingredient


@transaction.atomic
def delete_ingredient(
    id: int,
    user_id: int,
    repo: repository.AbstractRepository,
) -> None:
    try:
        ingredient: domain_model.Ingredient = repo.get(
            {"id": id}, select_related="user"
        )

    except repo.model.DoesNotExist:
        raise domain_model.IngredientNotExist

    if not ingredient.check_ownership(user_id):
        raise domain_model.IngredientNotOwnerError

    del ingredient
    repo.delete()
