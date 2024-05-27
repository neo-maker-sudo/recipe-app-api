from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import (
    JWTStatelessUserAuthentication,
)

from recipe_menu import service_layer as services
from recipe_menu.adapters import repository
from recipe.serializers import (
    RecipeListSerializerOut,
    RecipeDetailSerializerOut,
    RecipeCreateSerializerIn,
    RecipeDetailPatchSerializerIn,
    RecipeDetailPatchSerializerOut,
    RecipeUploadImageSerializerIn,
    RecipeUploadImageSerializerOut,
    TagListSerializerOut,
    TagDetailPatchSerializerIn,
    TagDetailPatchSerializerOut,
    IngredientListSerializerOut,
    IngredientDetailPatchSerializerIn,
    IngredientDetailPatchSerializerOut,
)
from recipe_menu.domain import model as domain_model


class RecipeListAPIView(APIView):
    authentication_classes = [JWTStatelessUserAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request="",
        responses={
            200: RecipeListSerializerOut,
            400: domain_model.UserNotExist,
            401: "",
        },
        methods=["GET"],
        parameters=[
            OpenApiParameter(
                "tags",
                OpenApiTypes.STR,
                description="Comma separated list of tag IDs to filter",
            ),
            OpenApiParameter(
                "ingredients",
                OpenApiTypes.STR,
                description="Comma separated list of ingredient IDs to filter",
            ),
        ],
    )
    def get(self, request, *args, **kwargs):
        order_by = request.query_params.get("o", "-id")

        try:
            recipes = services.retrieve_recipes(
                user_id=request.user.id,
                filter_obj=domain_model.UserFilterObj(
                    model=domain_model.UserFilterModel.RECIPES,
                    tags=request.query_params.get("tags", None),
                    ingredients=request.query_params.get("ingredients", None),
                ),
                order_by=order_by,
                repo=repository.UserRepository(),
            )

        except domain_model.UserNotExist as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response(
            RecipeListSerializerOut(
                recipes, many=True, context={"request": request}
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=RecipeCreateSerializerIn,
        responses={
            201: RecipeDetailSerializerOut,
            401: "",
        },
        methods=["POST"],
    )
    def post(self, request, *args, **kwargs):
        serializer = RecipeCreateSerializerIn(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipe = services.create_recipe(
            title=serializer.validated_data.get("title"),
            time_minutes=serializer.validated_data.get("time_minutes"),
            price=serializer.validated_data.get("price"),
            description=serializer.validated_data.get("description"),
            link=serializer.validated_data.get("link"),
            tags=serializer.validated_data.get("tags"),
            ingredients=serializer.validated_data.get("ingredients"),
            user_id=request.user.id,
            repo=repository.RecipeRepository(),
        )

        return Response(
            RecipeDetailSerializerOut(recipe).data,
            status=status.HTTP_201_CREATED,
        )


class RecipeDetailAPIView(APIView):
    authentication_classes = [JWTStatelessUserAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request="",
        responses={
            200: RecipeDetailSerializerOut,
            400: domain_model.RecipeNotExist,
            401: "",
        },
        methods=["GET"],
    )
    def get(self, request, *args, **kwargs):
        id = kwargs.get("recipe_id", None)

        try:
            recipe = services.retrieve_recipe(
                id=id,
                repo=repository.RecipeRepository(),
            )

        except domain_model.RecipeNotExist as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response(
            RecipeDetailSerializerOut(
                recipe, context={"request": request}
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=RecipeDetailPatchSerializerIn,
        responses={
            200: RecipeDetailPatchSerializerOut,
            400: domain_model.RecipeNotExist,
            401: "",
            404: domain_model.RecipeNotOwnerError,
        },
        methods=["PATCH"],
    )
    def patch(self, request, *args, **kwargs):
        id = kwargs.get("recipe_id", None)

        serializer = RecipeDetailPatchSerializerIn(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            recipe = services.update_recipe(
                id=id,
                update_fields={
                    "title": serializer.validated_data.get("title"),
                    "time_minutes": serializer.validated_data.get(
                        "time_minutes"
                    ),
                    "price": serializer.validated_data.get("price"),
                    "description": serializer.validated_data.get(
                        "description"
                    ),
                    "link": serializer.validated_data.get("link"),
                    "tags": serializer.validated_data.get("tags"),
                    "ingredients": serializer.validated_data.get(
                        "ingredients"
                    ),
                },
                user_id=request.user.id,
                repo=repository.RecipeRepository(),
            )

        except (
            domain_model.RecipeNotExist,
            domain_model.RecipeNotOwnerError,
        ) as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response(
            RecipeDetailPatchSerializerOut(recipe).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request="",
        responses={
            204: "OK",
            400: domain_model.RecipeNotExist,
            401: "",
            404: domain_model.RecipeNotOwnerError,
        },
        methods=["DELETE"],
    )
    def delete(self, request, *args, **kwargs):
        id = kwargs.get("recipe_id", None)

        try:
            services.delete_recipe(
                id=id,
                user_id=request.user.id,
                repo=repository.RecipeRepository(),
            )

        except (
            domain_model.RecipeNotExist,
            domain_model.RecipeNotOwnerError,
        ) as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response("OK", status=status.HTTP_204_NO_CONTENT)


class RecipeUploadImageAPIView(APIView):
    authentication_classes = [JWTStatelessUserAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=RecipeUploadImageSerializerIn,
        responses={
            200: RecipeUploadImageSerializerOut,
            400: domain_model.RecipeNotExist,
            401: "",
            404: domain_model.RecipeNotOwnerError,
        },
        methods=["PATCH"],
    )
    def patch(self, request, *args, **kwargs):
        id = kwargs.get("recipe_id", None)

        serializer = RecipeUploadImageSerializerIn(data=request.FILES)
        serializer.is_valid(raise_exception=True)

        try:
            recipe = services.update_recipe_image(
                id=id,
                image_object=domain_model.RecipeImage(
                    image=serializer.validated_data.get("image")
                ),
                user_id=request.user.id,
                repo=repository.RecipeRepository(),
            )

        except (
            domain_model.RecipeNotExist,
            domain_model.RecipeNotOwnerError,
        ) as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response(
            RecipeUploadImageSerializerOut(
                recipe, context={"request": request}
            ).data,
            status=status.HTTP_200_OK,
        )


class TagsListAPIView(APIView):
    authentication_classes = [JWTStatelessUserAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request="",
        responses={
            200: TagListSerializerOut,
            400: domain_model.UserNotExist,
            401: "",
        },
        methods=["GET"],
    )
    def get(self, request, *args, **kwargs):
        order_by = request.query_params.get("o", "-name")

        try:
            tags = services.retrieve_tags(
                user_id=request.user.id,
                filter_obj=domain_model.UserFilterObj(
                    model=domain_model.UserFilterModel.TAGS,
                    tags=request.query_params.get("tags", None),
                ),
                order_by=order_by,
                repo=repository.UserRepository(),
            )

        except domain_model.UserNotExist as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response(
            TagListSerializerOut(tags, many=True).data,
            status=status.HTTP_200_OK,
        )


class TagDetailAPIView(APIView):
    @extend_schema(
        request=TagDetailPatchSerializerIn,
        responses={
            200: TagDetailPatchSerializerOut,
            400: domain_model.TagNotExist,
            401: "",
            404: domain_model.TagNotOwnerError,
        },
        methods=["PATCH"],
    )
    def patch(self, request, *args, **kwargs):
        id = kwargs.get("tag_id", None)

        serializer = TagDetailPatchSerializerIn(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            tag = services.update_tag(
                id=id,
                update_fields={
                    "name": serializer.validated_data.get("name"),
                },
                user_id=request.user.id,
                repo=repository.TagRepository(),
            )

        except (
            domain_model.TagNotExist,
            domain_model.TagNotOwnerError,
        ) as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response(
            TagDetailPatchSerializerOut(tag).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request="",
        responses={
            204: "OK",
            400: domain_model.TagNotExist,
            401: "",
            404: domain_model.TagNotOwnerError,
        },
        methods=["DELETE"],
    )
    def delete(self, request, *args, **kwargs):
        id = kwargs.get("tag_id", None)

        try:
            services.delete_tag(
                id=id,
                user_id=request.user.id,
                repo=repository.TagRepository(),
            )

        except (
            domain_model.TagNotExist,
            domain_model.TagNotOwnerError,
        ) as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response("OK", status=status.HTTP_204_NO_CONTENT)


class IngredientListAPIView(APIView):
    authentication_classes = [JWTStatelessUserAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request="",
        responses={
            200: IngredientListSerializerOut,
            400: domain_model.UserNotExist,
            401: "",
        },
        methods=["GET"],
    )
    def get(self, request, *args, **kwargs):
        order_by = request.query_params.get("o", "-name")

        try:
            ingredients = services.retrieve_ingredients(
                user_id=request.user.id,
                filter_obj=domain_model.UserFilterObj(
                    model=domain_model.UserFilterModel.INGREDIENTS,
                    ingredients=request.query_params.get("ingredients", None),
                ),
                order_by=order_by,
                repo=repository.UserRepository(),
            )

        except domain_model.UserNotExist as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response(
            IngredientListSerializerOut(ingredients, many=True).data,
            status=status.HTTP_200_OK,
        )


class IngredientDetailAPIView(APIView):

    @extend_schema(
        request=IngredientDetailPatchSerializerIn,
        responses={
            200: IngredientDetailPatchSerializerOut,
            400: domain_model.IngredientNotExist,
            401: "",
            404: domain_model.IngredientNotOwnerError,
        },
        methods=["PATCH"],
    )
    def patch(self, request, *args, **kwargs):
        id = kwargs.get("ingredient_id", None)

        serializer = IngredientDetailPatchSerializerIn(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ingredient = services.update_ingredient(
                id=id,
                update_fields={
                    "name": serializer.validated_data.get("name"),
                },
                user_id=request.user.id,
                repo=repository.IngredientRepository(),
            )

        except (
            domain_model.IngredientNotExist,
            domain_model.IngredientNotOwnerError,
        ) as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response(
            IngredientDetailPatchSerializerOut(ingredient).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request="",
        responses={
            204: "OK",
            400: domain_model.IngredientNotExist,
            401: "",
            404: domain_model.IngredientNotOwnerError,
        },
        methods=["DELETE"],
    )
    def delete(self, request, *args, **kwargs):
        id = kwargs.get("ingredient_id", None)

        try:
            services.delete_ingredient(
                id=id,
                user_id=request.user.id,
                repo=repository.IngredientRepository(),
            )

        except (
            domain_model.IngredientNotExist,
            domain_model.IngredientNotOwnerError,
        ) as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response("OK", status=status.HTTP_204_NO_CONTENT)
