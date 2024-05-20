from dataclasses import dataclass
from typing import Optional, Callable
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
        self._recipes = set()

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


class RecipeNotExist(Exception):
    message = "食譜不存在"
    status_code = status.HTTP_400_BAD_REQUEST


class Recipe:

    def __init__(
        self,
        title: str,
        description: str,
        time_minutes: int,
        price: float,
        link: str,
    ):
        self.id = None
        self.title = title
        self.description = description
        self.time_minutes = time_minutes
        self.price = price
        self.link = link
