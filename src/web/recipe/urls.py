from django.urls import path
from . import views

app_name = "recipe"

urlpatterns = [
    path("", views.RecipeListAPIView.as_view(), name="recipe-list"),
]
