from rest_framework import serializers


class RecipeTagsSerailizer(serializers.Serializer):
    name = serializers.CharField()


class RecipeListSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    time_minutes = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=5, decimal_places=2)
    link = serializers.CharField()
    tags = RecipeTagsSerailizer(many=True, required=False)


class RecipeDetailSerializerOut(RecipeListSerializerOut):
    description = serializers.CharField()
    tags = RecipeTagsSerailizer(many=True, required=False)


class RecipeCreateSerializerIn(serializers.Serializer):
    title = serializers.CharField()
    time_minutes = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=5, decimal_places=2)
    description = serializers.CharField(allow_blank=True)
    link = serializers.CharField(allow_blank=True)
    tags = RecipeTagsSerailizer(many=True, required=False)


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


class TagListSerializerOut(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()


class TagDetailPatchSerializerIn(serializers.Serializer):
    name = serializers.CharField()


class TagDetailPatchSerializerOut(serializers.Serializer):
    name = serializers.CharField()
