from django.urls import path

from . import views


app_name = "finance"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("stats/", views.StatsView.as_view(), name="stats"),
    path("profile/", views.ProfileUpdateView.as_view(), name="profile"),
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/add/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.CategoryUpdateView.as_view(), name="category_update"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),
    path("transactions/", views.TransactionListView.as_view(), name="transaction_list"),
    path("transactions/", views.TransactionListView.as_view(), name="transactions"),
    path("transactions/add/", views.TransactionCreateView.as_view(), name="transaction_create"),
    path("transactions/<int:pk>/edit/", views.TransactionUpdateView.as_view(), name="transaction_update"),
    path("transactions/<int:pk>/delete/", views.TransactionDeleteView.as_view(), name="transaction_delete"),
    path("budgets/", views.BudgetListView.as_view(), name="budget_list"),
    path("budgets/", views.BudgetListView.as_view(), name="budgets"),
    path("budgets/add/", views.BudgetCreateView.as_view(), name="budget_create"),
    path("budgets/<int:pk>/edit/", views.BudgetUpdateView.as_view(), name="budget_update"),
    path("budgets/<int:pk>/delete/", views.BudgetDeleteView.as_view(), name="budget_delete"),
    path("categories/", views.CategoryListView.as_view(), name="categories"),
    path("goals/", views.SavingGoalListView.as_view(), name="goal_list"),
    path("goals/add/", views.SavingGoalCreateView.as_view(), name="goal_create"),
    path("goals/<int:pk>/edit/", views.SavingGoalUpdateView.as_view(), name="goal_update"),
    path("goals/<int:pk>/delete/", views.SavingGoalDeleteView.as_view(), name="goal_delete"),
    path("goals/<int:pk>/add-saving/", views.SavingGoalAddView.as_view(), name="goal_add_saving"),
]

