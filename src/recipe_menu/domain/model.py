from dataclasses import dataclass
from typing import Optional, Callable, Union
from rest_framework import status


def manage_profile(user, update_fields):
    user.manage_profile(update_fields)
    return update_fields


class UserAlreadyExist(Exception):
    message = "使用者已存在"
    status_code = status.HTTP_400_BAD_REQUEST


class UserNotExist(Exception):
    message = "信箱或密碼錯誤"
    status_code = status.HTTP_400_BAD_REQUEST


class InvalidCredentialsError(Exception):
    message = "信箱或密碼錯誤"
    status_code = status.HTTP_400_BAD_REQUEST


@dataclass(frozen=True)
class BaseUserMethods:
    check_password: Callable
    refresh_from_db: Callable
    set_password: Callable


@dataclass(frozen=True)
class UserTokenCredentials:
    access_token: str
    token_type: str


class User:
    def __init__(
        self,
        email: str,
        name: str,
        methods: Optional[BaseUserMethods] = None,
        password: Optional[str] = None,
    ):
        self.email = email
        self.name = name
        self.password = password
        # add extra_methods attribute for using django original User model method
        self.methods = methods
        self._recipes = None
        self._tags = None
        self._ingredients = None

    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return False

        return other.email == self.email

    def __hash__(self) -> int:
        return hash(self.email)

    def __repr__(self):
        return f"<User {self.email}>"

    def check_password(self, raw_password) -> bool:
        return self.methods.check_password(raw_password)

    def manage_profile(self, update_fields):
        if (name := update_fields.get("name", None)) is not None:
            self.name = name

        if (password := update_fields.get("password", None)) is not None:
            self.password = password

    @property
    def recipes(self):
        return self._recipes

    @property
    def tags(self):
        return self._tags

    @property
    def ingredients(self):
        return self._ingredients


class RecipeNotExist(Exception):
    message = "食譜不存在"
    status_code = status.HTTP_400_BAD_REQUEST


class RecipeNotOwnerError(Exception):
    message = "不存在的食譜"
    status_code = status.HTTP_404_NOT_FOUND


class Recipe:

    def __init__(
        self,
        title: str,
        description: str,
        time_minutes: int,
        price: float,
        link: str,
        tags: Union[list["Tag"], None],
        ingredients: Union[list["Ingredient"], None],
    ):
        self.id = None
        self.title = title
        self.description = description
        self.time_minutes = time_minutes
        self.price = price
        self.link = link
        self.user = None
        self.tags = tags if tags is not None else []
        self.update_tags = False
        self.ingredients = ingredients if ingredients is not None else []
        self.update_ingredients = False

    def mark_user(self, user) -> None:
        self.user = user

    def check_ownership(self, user_id: int) -> bool:
        if self.user.id != user_id:
            return False

        return True

    def update_detail(self, update_fields: dict) -> None:
        title = update_fields.get("title", None)
        description = update_fields.get("description", None)
        time_minutes = update_fields.get("time_minutes", None)
        price = update_fields.get("price", None)
        link = update_fields.get("link", None)
        tags = update_fields.get("tags", None)
        ingredients = update_fields.get("ingredients", None)

        if self.title != title and title is not None:
            self.title = title

        if self.description != description and description is not None:
            self.description = description

        if self.time_minutes != time_minutes and time_minutes is not None:
            self.time_minutes = time_minutes

        if self.price != price and price is not None:
            self.price = price

        if self.link != link and link is not None:
            self.link = link

        if tags is not None:
            self.update_tags = True
            self.tags = [Tag(name=tag["name"]) for tag in tags]

        if ingredients is not None:
            self.update_ingredients = True
            self.ingredients = [
                Ingredient(name=ingredient["name"])
                for ingredient in ingredients
            ]


class TagNotExist(Exception):
    message = "標籤不存在"
    status_code = status.HTTP_400_BAD_REQUEST


class TagNotOwnerError(Exception):
    message = "不存在的標籤"
    status_code = status.HTTP_404_NOT_FOUND


class Tag:
    def __init__(self, name: str) -> None:
        self.id = None
        self.name = name
        self.user = None

    def __eq__(self, other) -> bool:
        if not isinstance(other, Tag):
            return False

        return other.name == self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def to_dict(self):
        return {
            "name": self.name,
        }

    def check_ownership(self, user_id: int) -> bool:
        if self.user.id != user_id:
            return False

        return True

    def update_detail(self, update_fields: dict) -> None:
        name = update_fields.get("name", None)

        if self.name != name and name is not None:
            self.name = name


class IngredientNotExist(Exception):
    message = "原料不存在"
    status_code = status.HTTP_400_BAD_REQUEST


class IngredientNotOwnerError(Exception):
    message = "不存在的原料"
    status_code = status.HTTP_404_NOT_FOUND


class Ingredient:
    def __init__(self, name: str, id: Optional[int] = None):
        self.id = id
        self.name = name
        self.user = None

    def __eq__(self, other) -> bool:
        if not isinstance(other, Ingredient):
            return False

        return other.name == self.name

    def __hash__(self) -> int:
        return hash(self.name)

    def to_dict(self):
        return {
            "name": self.name,
        }

    def check_ownership(self, user_id: int) -> bool:
        if self.user is None or self.user.id != user_id:
            return False

        return True

    def update_detail(self, update_fields: dict) -> None:
        name = update_fields.get("name", None)

        if self.name != name and name is not None:
            self.name = name
