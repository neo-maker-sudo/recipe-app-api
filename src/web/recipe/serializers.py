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
    image = serializers.SerializerMethodField("get_image_url", required=False)
    tags = RecipeTagsSerailizerOut(many=True, required=False)
    ingredients = RecipeIngredientsSerializerOut(many=True, required=False)

    def get_image_url(self, model):
        if model.image is None:
            return None

        try:
            return self.context["request"].build_absolute_uri(model.image.url)

        except ValueError:
            pass


class RecipeDetailSerializerOut(RecipeListSerializerOut):
    description = serializers.CharField()


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


class RecipeDetailPatchSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    time_minutes = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=5, decimal_places=2)
    link = serializers.CharField()
    tags = RecipeTagsSerailizerOut(many=True, required=False)
    ingredients = RecipeIngredientsSerializerOut(many=True, required=False)


class RecipeUploadImageSerializerIn(serializers.Serializer):
    image = serializers.ImageField(required=True)


class RecipeUploadImageSerializerOut(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    image = serializers.SerializerMethodField("get_image_url")

    def get_image_url(self, model):
        if model.image.name is None:
            return None

        return self.context["request"].build_absolute_uri(model.image.url)


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
