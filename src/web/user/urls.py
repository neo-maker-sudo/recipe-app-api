from django.urls import path
from . import views


app_name = "user"


urlpatterns = [
    path("", views.RegisterAPIView.as_view(), name="create"),
]
