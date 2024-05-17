from rest_framework import serializers


class UserSerializerIn(serializers.Serializer):
    email = serializers.EmailField(required=True)
    name = serializers.CharField(required=True)
    password = serializers.CharField(min_length=5, required=True)


class UserSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    name = serializers.CharField()
