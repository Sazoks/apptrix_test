from django.urls import (
    path,
    include,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework_swagger.views import get_swagger_view

from .clients import views


urlpatterns = [
    path('list/', views.UserListView.as_view(), name='api_user_list'),
    path('clients/', include('api.clients.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('docs/', get_swagger_view(title='Date me please API')),
]
