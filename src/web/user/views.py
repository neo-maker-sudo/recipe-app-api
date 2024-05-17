from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import APIView
from rest_framework.response import Response

from .serializers import UserSerializerIn, UserSerializerOut
from recipe import service_layer as services
from recipe.adapters import repository
from recipe.domain import model as domain_model


class RegisterAPIView(APIView):

    @extend_schema(
        request=UserSerializerIn,
        responses={
            201: UserSerializerOut,
            400: domain_model.UserAlreadyExist.message,
        },
        methods=["POST"],
    )
    def post(self, request, *args, **kwargs):
        serializer = UserSerializerIn(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            instance = services.register(
                email=serializer.data["email"],
                name=serializer.data["name"],
                password=serializer.data["password"],
                repo=repository.UserRepository(),
            )

        except domain_model.UserAlreadyExist as exc:
            return Response(
                {"detail": exc.message}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            UserSerializerOut(instance).data, status=status.HTTP_201_CREATED
        )
