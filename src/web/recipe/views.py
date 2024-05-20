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
    RecipeListSerializerIn,
    RecipeListSerializerOut,
    RecipeDetailSerializerOut,
)
from recipe_menu.domain import model as domain_model


class RecipeListAPIView(APIView):

    @extend_schema(
        request=RecipeListSerializerIn,
        responses={
            200: RecipeListSerializerOut,
            401: RecipeListSerializerIn.invalid_token_msg,
        },
        methods=["GET"],
    )
    def get(self, request, *args, **kwargs):
        order_by = request.query_params.get("o", "-id")

        serializer = RecipeListSerializerIn(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        recipes = services.retrieve_recipes(
            user_id=serializer.validated_data.get("user_id"),
            order_by=order_by,
            repo=repository.UserRepository(),
        )

        return Response(
            RecipeListSerializerOut(recipes, many=True).data,
            status=status.HTTP_200_OK,
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
