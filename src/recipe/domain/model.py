from dataclasses import dataclass
from typing import Optional, Callable


class UserAlreadyExist(Exception):
    message = "使用者已存在"


@dataclass(frozen=True)
class BaseUserMethods:
    check_password: Callable


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
