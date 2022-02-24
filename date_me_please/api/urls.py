from django.urls import (
    path,
    include,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.schemas import get_schema_view
from rest_framework_swagger.views import get_swagger_view

from .clients import views


urlpatterns = [
    path('list/', views.UserListView.as_view(), name='api_user_list'),
    path('clients/', include('api.clients.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('doc/', get_swagger_view(title='Date me please API')),
]
