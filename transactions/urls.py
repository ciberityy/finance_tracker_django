from django.contrib.auth.views import LoginView,LogoutView
from django.urls import path
from . import views

urlpatterns =[
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path("dashboard/", views.dashboard, name="dashboard"),
    path('add_transaction/', views.add_transaction, name='add_transaction'),
    path('add_category/', views.add_category, name='add_category'),
    path('view_categories/', views.view_categories, name='view_categories')
]