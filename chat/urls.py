from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('chat/', views.chat, name='chat'),
    path('chat_view/', views.chat_view, name='chat_view'),
    path('clear_chat/', views.clear_chat, name='clear_chat'),
    path('chat_history/', views.chat_history, name='chat_history'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
]