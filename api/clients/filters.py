from django.contrib.auth.models import User
from django.db.models import QuerySet
from django.db.models.functions import (
    Sin, Cos, ATan2,
    Abs, Sqrt, Power,
    Radians,
)
from django.db.models import F
from django_filters import rest_framework as filters
from clients.models import Profile


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
            distance_to_user=ATan2(
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
                ,
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
