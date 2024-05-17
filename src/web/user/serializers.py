from rest_framework import serializers


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
