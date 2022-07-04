import smtplib
from decouple import config

from django.conf import settings
from django.utils.translation import gettext as _
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
    LogoutSerializer,
    UserSerializer,
)
from .filters import UserFilter


class RegisterView(generics.CreateAPIView):
    """Класс-контроллер для регистрации пользователя"""

    queryset = User.objects.all()
    permission_classes = (AllowAny, )
    serializer_class = RegisterSerializer


class LogoutView(generics.GenericAPIView):
    """Класс-контроллер для выхода из системы с использованием JWT"""

    serializer_class = LogoutSerializer
    permission_classes = (IsAuthenticated, )

    def post(self, request: Request, *args, **kwargs) -> Response:
        """Добавление токена в черный список"""

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserDetailView(generics.RetrieveAPIView):
    """
    Класс-контроллер для предоставления информации о пользователе
    """

    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer


class UserListView(generics.ListAPIView):
    """Класс-контроллер списка пользователей"""

    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer
    filterset_class = UserFilter

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Метод для отправки отфильтрованного списка пользователей"""

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)


class LoverListView(generics.ListAPIView):
    """Класс-контроллер списка оценивших пользователей"""

    queryset = User.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer

    def get(self, request: Request, *args, **kwargs) -> Response:
        """Метод для полуения списка оценивших пользователей"""

        lovers = [lover_profile.user for lover_profile in
                  request.user.profile.lovers.all()]
        serializer = self.serializer_class(lovers, many=True)
        return Response(serializer.data)


class LikeUserView(views.APIView):
    """Класс-контроллер оценки пользователя"""

    permission_classes = (IsAuthenticated, )

    @staticmethod
    def __send_love(beloved: User, lover: User) -> None:
        """Метод отправки письма со взаимной симпатией"""

        # FIXME:
        #  Этот способ отправки сообщения, как по-мне, - костыль, хоть и
        #  рабочий. Необходимо разобраться, почему не работает стандартный
        #  способ отправки сообщений.
        server = smtplib.SMTP('smtp.gmail.com', 25)
        server.connect("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()

        EMAIL_HOST_USER = config('EMAIL_HOST_USER')
        EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

        text = f'From: my_apptrix_test@test.com\n' \
               f'Subject: Есть взаимная симпатия!\n' \
               f'Вы понравились {lover.username}!\n' \
               f'Почта участника: {lover.email}.'.encode('utf-8')

        server.sendmail(EMAIL_HOST_USER, beloved.email, text)
        server.quit()

    def post(self, request: Request, *args, **kwargs) -> Response:
        """Метод для оценки пользователя другим пользователем"""

        # Текущий пользователь и пользователь, которого оценили.
        current_user = request.user
        liked_user = User.objects.filter(pk=kwargs['pk']).first()

        # Если пользователя не существует, возвращаем ошибку.
        if liked_user is None:
            return Response(data={'msg': 'Такого пользователя нет.'},
                            status=status.HTTP_404_NOT_FOUND)

        # Если пользователь пытается оценить сам себя
        if current_user.pk == liked_user.pk:
            return Response(data={'msg': 'Вы не можете оценить себя.'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Если пользователь уже оценивал этого пользователя, сообщаем об этом.
        if current_user.profile in liked_user.profile.lovers.all():
            return Response(data={'msg': 'Вы уже оценили этого пользователя.'},
                            status=status.HTTP_403_FORBIDDEN)

        # Совпадение симпатий.
        # Эта ситуация возникает, когда текущий пользователь оценил
        # пользователя, который уже есть в списке тех, кто оценил
        # текущего пользователя.
        if liked_user.profile in current_user.profile.lovers.all():
            # Отправляем пользователям письма.
            self.__send_love(current_user, liked_user)
            self.__send_love(liked_user, current_user)

            # Т.к. взаимная симпатия достигнута, можно больше не отслеживать,
            # кто кого оценил. Удаляем связь пользователей.
            current_user.profile.lovers.remove(liked_user.profile)

            return Response(data={
                'msg': _('Есть взаимная симпатия!'),
                'lovers_email': liked_user.email
            })

        # Добавляем текущего пользователя в список оценивших.
        liked_user.profile.lovers.add(current_user.profile)

        return Response(data={'msg': f'Вы оценили {liked_user.username}.'},)
