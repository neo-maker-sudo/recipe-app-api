from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_simplejwt.authentication import (
    JWTStatelessUserAuthentication,
)
from rest_framework_simplejwt.exceptions import (
    InvalidToken,
)


class JWTAuthSerializer(serializers.Serializer):
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


class RecipeListSerializerIn(JWTAuthSerializer):

    def validate(self, attrs):
        return super().validate(attrs)


class RecipeListSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    time_minutes = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=5, decimal_places=2)
    link = serializers.CharField()


class RecipeDetailSerializerOut(RecipeListSerializerOut):
    description = serializers.CharField()
