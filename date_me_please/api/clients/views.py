from django.template.loader import render_to_string
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework import views
from rest_framework import status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.request import Request

from .serializers import (
    RegisterSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    """Класс-контроллер для регистрации пользователя"""

    queryset = User.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = RegisterSerializer


class UserDetailView(generics.RetrieveAPIView):
    """
    Класс-контроллер для предоставления информации
    о пользователе.
    """

    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer


class UserListView(generics.ListAPIView):
    """Класс-контроллер списка пользователей"""

    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.get_queryset()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data)


class LikeUserView(views.APIView):
    """Класс-контроллер оценки пользователя"""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request, *args, **kwargs) -> Response:
        """Метод для оценки пользователя другим пользователем"""

        # Текущий пользователь и пользователь, которого оценили.
        current_user = request.user
        liked_user = User.objects.filter(pk=kwargs['pk']).first()

        # Если пользователя не существует, возвращаем ошибку.
        if liked_user is None:
            return Response(data={'msg': 'Такого пользователя нет'},
                            status=status.HTTP_404_NOT_FOUND)

        # Если пользователь пытается оценить сам себя
        if current_user.pk == liked_user.pk:
            return Response(data={'msg': 'Вы не можете оценить себя'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Если пользователь уже оценивал этого пользователя, сообщаем об этом.
        if current_user.profile in liked_user.profile.lovers.all():
            return Response(data={'msg': 'Вы уже оценили этого пользователя'},
                            status=status.HTTP_403_FORBIDDEN)

        # Совпадение симпатий.
        if liked_user.profile in current_user.profile.lovers.all():
            # Отправляем пользователям письма.
            # current_user.email_user(
            #     subject=render_to_string('clients/subject_template.txt'),
            #     message=render_to_string(
            #         template_name='clients/message_template.txt',
            #         context={
            #             'username': liked_user.username,
            #             'email': liked_user.email,
            #         }
            #     )
            # )
            # liked_user.email_user(
            #     subject=render_to_string('clients/subject_template.txt'),
            #     message=render_to_string(
            #         template_name='clients/message_template.txt',
            #         context={
            #             'username': current_user.username,
            #             'email': current_user.email,
            #         }
            #     )
            # )
            return Response(data={'lovers_email': liked_user.email})

        # Добавляем текущего пользователя в список оценивших.
        liked_user.profile.lovers.add(current_user.profile)

        return Response(data={'msg': f'Вы оценили {liked_user.username}'})


class LoverListView(generics.ListAPIView):
    """Класс-контроллер списка оценивших пользователей"""

    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        lovers = [lover_profile.user for lover_profile in
                  request.user.profile.lovers.all()]
        serializer = UserSerializer(lovers, many=True)
        return Response(serializer.data)
