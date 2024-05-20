from rest_framework import serializers


class RecipeListSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    time_minutes = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=5, decimal_places=2)
    link = serializers.CharField()


class RecipeDetailSerializerOut(RecipeListSerializerOut):
    description = serializers.CharField()
