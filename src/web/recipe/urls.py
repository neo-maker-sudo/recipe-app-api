from django.urls import path
from . import views

app_name = "recipe"

urlpatterns = [
    path("recipes/", views.RecipeListAPIView.as_view(), name="recipe-list"),
    path(
        "recipes/<int:recipe_id>/",
        views.RecipeDetailAPIView.as_view(),
        name="recipe-detail",
    ),
    path("tags/", views.TagsListAPIView.as_view(), name="tag-list"),
    path(
        "tags/<int:tag_id>/",
        views.TagDetailAPIView.as_view(),
        name="tag-detail",
    ),
]
