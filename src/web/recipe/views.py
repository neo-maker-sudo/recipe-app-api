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

    @extend_schema()
    def patch(self, request, *args, **kwargs):
        pass

    @extend_schema()
    def delete(self, request, *args, **kwargs):
        pass
