from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import (
    JWTStatelessUserAuthentication,
)

from .serializers import (
    UserSerializerIn,
    UserSerializerOut,
    LoginSerializerIn,
    LoginSerializerOut,
    ManageUserGetSerializerIn,
    ManageUserGetSerializerOut,
    ManageUserPatchSerializerIn,
)
from recipe_menu import service_layer as services
from recipe_menu.adapters import repository
from recipe_menu.domain import model as domain_model


class RegisterAPIView(APIView):

    authentication_classes = []

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
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response(
            UserSerializerOut(instance).data, status=status.HTTP_201_CREATED
        )


class LoginAPIView(APIView):

    authentication_classes = []

    @extend_schema(
        request=LoginSerializerIn,
        responses={
            200: LoginSerializerOut,
        },
        methods=["POST"],
    )
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializerIn(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            credentials = services.login(
                email=serializer.data["email"],
                password=serializer.data["password"],
                repo=repository.UserRepository(),
            )

        except (
            domain_model.InvalidCredentialsError,
            domain_model.UserNotExist,
        ) as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response(
            credentials,
            status=status.HTTP_200_OK,
        )


class ManageUserAPIView(APIView):

    authentication_classes = [JWTStatelessUserAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ManageUserGetSerializerIn,
        responses={
            200: ManageUserGetSerializerOut,
            401: ManageUserGetSerializerIn.invalid_token_msg,
        },
        methods=["GET"],
    )
    def get(self, request, *args, **kwargs):
        serializer = ManageUserGetSerializerIn(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            user = services.retrieve_user(
                id=request.user.id,
                repo=repository.UserRepository(),
            )

        except domain_model.UserNotExist as exc:
            return Response({"detail": exc.message}, status=exc.status_code)

        return Response(
            ManageUserGetSerializerOut(user).data, status=status.HTTP_200_OK
        )

    @extend_schema(
        request=ManageUserPatchSerializerIn,
        responses={
            200: "OK",
            401: ManageUserPatchSerializerIn.invalid_token_msg,
        },
        methods=["PATCH"],
    )
    def patch(self, request, *args, **kwargs):
        serializer = ManageUserPatchSerializerIn(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.update_user(
            id=request.user.id,
            update_fields={
                "name": serializer.validated_data.get("name"),
                "password": serializer.validated_data.get("password"),
            },
            repo=repository.UserRepository(),
        )

        return Response("OK", status=status.HTTP_200_OK)
