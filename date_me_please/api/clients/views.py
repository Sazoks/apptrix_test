import smtplib

from django.template.loader import render_to_string
from django.contrib.auth.models import User
from django.db.models.functions import (
    Sin,
    Cos,
    ACos,
    Abs,
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
    UserSerializer,
)
from clients.models import Profile


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

    def filter_distance(self, queryset, name, max_distance):
        """
        Метод фильтрации пользователей по заданному расстоянию.

        Каждому пользователю генерируем поле, обозначающее его
        расстояние до текущего пользователя.
        """

        # Координаты текущего пользователя.
        lat = self.request.user.profile.latitude
        lon = self.request.user.profile.latitude

        # Радиус Земли.
        EARTH_RADIUS = 6371

        # С помощью функций СУБД и вычисляем для каждой записи расстояния
        # до текущего пользователя.
        queryset = User.objects.select_related('profile').annotate(
            distance_to_user=ACos(
                Sin(lat) * Sin(F('profile__latitude')) +
                Cos(lat) * Cos(F('profile__latitude')) *
                Cos(Abs(lon - F('profile__longitude')))
            ) * EARTH_RADIUS
        ).filter(distance_to_user__lte=max_distance)

        return queryset


class UserListView(generics.ListAPIView):
    """Класс-контроллер списка пользователей"""

    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer
    filterset_class = UserFilter

    def get_queryset(self):
        return User.objects.exclude(pk=self.request.user.pk)

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
        """Метод для отправки списка оценивших пользователей"""

        lovers = [lover_profile.user for lover_profile in
                  request.user.profile.lovers.all()]
        serializer = self.serializer_class(lovers, many=True)
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
