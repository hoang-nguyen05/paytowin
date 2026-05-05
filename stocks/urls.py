from django.urls import path

from . import views


app_name = "stocks"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("board-data/", views.board_data, name="board_data"),
    path("watch/add/", views.add_watch, name="add_watch"),
    path("watch/<int:pk>/delete/", views.delete_watch, name="delete_watch"),
    path("symbol/<str:symbol>/", views.symbol_detail, name="symbol_detail"),
]

