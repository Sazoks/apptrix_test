from django.urls import path
from . import views

urlpatterns = [
    path('', views.UserListView.as_view(), name='api_user_list'),
    path('me/lovers/', views.LoverListView.as_view(), name='api_lovers'),
    path('<int:pk>/match/', views.LikeUserView.as_view(), name='api_like_user'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='api_user_detail'),
    path('create/', views.RegisterView.as_view(), name='api_registration'),
]
