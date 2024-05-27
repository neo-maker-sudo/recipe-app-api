from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.authentication import (
    JWTStatelessUserAuthentication,
)
from rest_framework_simplejwt.exceptions import (
    InvalidToken,
)


class UserSerializerIn(serializers.Serializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True)
    password = serializers.CharField(min_length=5, required=True)


class UserSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()


class LoginSerializerIn(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        style={"input_type": "password"},
        min_length=5,
        required=True,
        trim_whitespace=False,
    )


class LoginSerializerOut(serializers.Serializer):
    access_token = serializers.CharField()
    token_type = serializers.CharField(default="Bearer")


class ManageUserGetSerializerIn(serializers.Serializer):
    invalid_token_msg = "Token contained no recognizable user identification"

    def validate(self, attrs):
        request = self.context.get("request")

        jwt_authenticator = JWTStatelessUserAuthentication()
        result = jwt_authenticator.authenticate(request)

        if result is None:
            raise InvalidToken(_(self.invalid_token_msg))

        token_user, payload = result
        attrs["user_id"] = payload["user_id"]
        return attrs


class ManageUserGetSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()


class ManageUserPatchSerializerIn(serializers.Serializer):
    invalid_token_msg = "Token contained no recognizable user identification"

    name = serializers.CharField(required=False)
    password = serializers.CharField(
        min_length=5,
        required=False,
    )
