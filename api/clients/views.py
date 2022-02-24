import os
import smtplib

from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.db.models.functions import (
    Sin, Cos, ATan,
    Abs, Sqrt, Power,
    Radians,
)
from django.db.models import F

from rest_framework import generics
from rest_framework import views
from rest_framework import status
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.request import Request
from django_filters import rest_framework as filters

from .serializers import (
    RegisterSerializer,
    LogoutSerializer,
    UserSerializer,
)
from clients.models import Profile


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


class UserFilter(filters.FilterSet):
    """Фильтр для пользователей"""

    gender = filters.ChoiceFilter(
        field_name='profile__gender',
        choices=Profile.Gender.choices,
    )
    distance_to_user = filters.NumberFilter(
        label='Максимальная дистанция',
        method='filter_distance',
    )

    class Meta:
        """Класс настроект фильтра"""

        model = User
        fields = ('first_name', 'last_name',
                  'gender', 'distance_to_user')

    def filter_distance(self, queryset: QuerySet,
                        name: str, max_distance: int) -> QuerySet:
        """
        Метод фильтрации пользователей по заданному расстоянию.

        Каждому пользователю генерируем поле, обозначающее его
        расстояние до текущего пользователя в километрах.
        """

        # Широта и долгота текущего пользователя.
        lat = self.request.user.profile.latitude
        lon = self.request.user.profile.longitude

        # Радиус Земли.
        EARTH_RADIUS = 6372

        # С помощью функций СУБД вычисляем для каждой
        # записи расстояния до текущего пользователя.
        # Т.к. сферическая теорема косинусов имеет проблемы
        # с маленькими расстояниями, было принято решение
        # использовать формулу гаверсинусов с модификацией для антиподов.
        # А еще я никогда столько страшных слов не слышал.
        queryset = User.objects.select_related('profile').annotate(
            distance_to_user=ATan(
                Sqrt(
                    Power(
                        Cos(Radians(F('profile__latitude'))) *
                        Sin(Abs(Radians(lon) - Radians(F('profile__longitude')))), 2
                    ) +
                    Power(
                        Cos(Radians(lat)) * Sin(Radians(F('profile__latitude'))) -
                        Sin(Radians(lat)) * Cos(Radians(F('profile__latitude'))) *
                        Cos(Abs(Radians(lon) - Radians(F('profile__longitude')))), 2
                    )
                )
                /
                (
                    Sin(Radians(lat)) * Sin(Radians(F('profile__latitude'))) +
                    Cos(Radians(lat)) * Cos(Radians(F('profile__latitude'))) *
                    Cos(Abs(
                        Radians(lon) -
                        Radians(F('profile__longitude'))
                    ))
                )
            ) * EARTH_RADIUS
        ).filter(distance_to_user__lte=max_distance)

        return queryset


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

    def __send_love(self, beloved: User, lover: User) -> None:
        """Метод отправки письма со взаимной симпатией"""

        # FIXME:
        #  Этот способ отправки сообщения, как по-мне, - костыль, хоть и рабочий
        #  Необходимо разобраться, почему не работает стандартный
        #  способ отправки сообщений.
        server = smtplib.SMTP('smtp.gmail.com', 25)
        server.connect("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.ehlo()

        EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
        EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

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
        # Эта ситуация возникает, когда текущий пользователь оценил пользователя,
        # который уже есть в списке тех, кто оценил текущего пользователя.
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

        return Response(data={'msg': f'Вы оценили {liked_user.username}.'})