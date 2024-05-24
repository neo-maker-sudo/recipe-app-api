from rest_framework import serializers


class RecipeTagsSerailizerIn(serializers.Serializer):
    name = serializers.CharField()


class RecipeTagsSerailizerOut(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class RecipeIngredientsSerializerIn(serializers.Serializer):
    name = serializers.CharField()


class RecipeIngredientsSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class RecipeListSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    time_minutes = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=5, decimal_places=2)
    link = serializers.CharField()
    tags = RecipeTagsSerailizerOut(many=True, required=False)
    ingredients = RecipeIngredientsSerializerOut(many=True, required=False)


class RecipeDetailSerializerOut(RecipeListSerializerOut):
    description = serializers.CharField()
    tags = RecipeTagsSerailizerOut(many=True, required=False)
    ingredients = RecipeIngredientsSerializerOut(many=True, required=False)


class RecipeCreateSerializerIn(serializers.Serializer):
    title = serializers.CharField()
    time_minutes = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=5, decimal_places=2)
    description = serializers.CharField(allow_blank=True)
    link = serializers.CharField(allow_blank=True)
    tags = RecipeTagsSerailizerIn(many=True, required=False)
    ingredients = RecipeIngredientsSerializerIn(many=True, required=False)


class RecipeCreateSerializerOut(serializers.Serializer):
    title = serializers.CharField()
    time_minutes = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=5, decimal_places=2)
    description = serializers.CharField()
    link = serializers.CharField()


class RecipeDetailPatchSerializerIn(serializers.Serializer):
    title = serializers.CharField(required=False)
    time_minutes = serializers.IntegerField(required=False)
    price = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False
    )
    description = serializers.CharField(allow_blank=True, required=False)
    link = serializers.CharField(allow_blank=True, required=False)
    tags = RecipeTagsSerailizerIn(many=True, required=False)
    ingredients = RecipeIngredientsSerializerIn(many=True, required=False)


class TagListSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class TagDetailPatchSerializerIn(serializers.Serializer):
    name = serializers.CharField()


class TagDetailPatchSerializerOut(serializers.Serializer):
    name = serializers.CharField()


class IngredientListSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class IngredientDetailPatchSerializerIn(serializers.Serializer):
    name = serializers.CharField()


class IngredientDetailPatchSerializerOut(serializers.Serializer):
    name = serializers.CharField()
