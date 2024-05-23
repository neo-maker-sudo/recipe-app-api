from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
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
    RecipeCreateSerializerOut,
    RecipeDetailPatchSerializerIn,
    TagListSerializerOut,
    TagDetailPatchSerializerIn,
    TagDetailPatchSerializerOut,
)
from recipe_menu.domain import model as domain_model


class RecipeListAPIView(APIView):
    authentication_classes = [JWTStatelessUserAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request="",
        responses={
            200: RecipeListSerializerOut,
            401: "",
        },
        methods=["GET"],
    )
    def get(self, request, *args, **kwargs):
        order_by = request.query_params.get("o", "-id")

        recipes = services.retrieve_recipes(
            user_id=request.user.id,
            order_by=order_by,
            repo=repository.UserRepository(),
        )

        return Response(
            RecipeListSerializerOut(recipes, many=True).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=RecipeCreateSerializerIn,
        responses={
            201: RecipeCreateSerializerOut,
            401: "",
        },
        methods=["POST"],
    )
    def post(self, request, *args, **kwargs):
        serializer = RecipeCreateSerializerIn(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.create_recipe(
            title=serializer.validated_data.get("title"),
            time_minutes=serializer.validated_data.get("time_minutes"),
            price=serializer.validated_data.get("price"),
            description=serializer.validated_data.get("description"),
            link=serializer.validated_data.get("link"),
            tags=serializer.validated_data.get("tags"),
            user_id=request.user.id,
            repo=repository.RecipeRepository(),
        )

        return Response(
            "OK",
            status=status.HTTP_201_CREATED,
        )


class RecipeDetailAPIView(APIView):
    authentication_classes = [JWTStatelessUserAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request="",
        responses={
            200: RecipeDetailSerializerOut,
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
            RecipeDetailSerializerOut(recipe).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=RecipeDetailPatchSerializerIn,
        responses={
            200: RecipeDetailSerializerOut,
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
            RecipeDetailSerializerOut(recipe).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request="",
        responses={
            204: RecipeDetailSerializerOut,
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


class TagsListAPIView(APIView):
    authentication_classes = [JWTStatelessUserAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request="",
        responses={
            200: TagListSerializerOut,
            401: "",
        },
        methods=["GET"],
    )
    def get(self, request, *args, **kwargs):
        order_by = request.query_params.get("o", "-name")

        tags = services.retrieve_tags(
            user_id=request.user.id,
            order_by=order_by,
            repo=repository.UserRepository(),
        )

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
            tag = services.update_recipe(
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
