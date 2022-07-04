import random
from typing import List

from rest_framework.response import Response
from rest_framework.test import (
    APITestCase,
    APIRequestFactory,
    force_authenticate,
)
from rest_framework import status
from django.contrib.auth.models import User
from django.urls import reverse

from api.clients import views
from api.clients import serializers
from clients.models import Profile


class ClientTests(APITestCase):
    """Юнит-тесты для проверки работы с пользователями"""

    def setUp(self) -> None:
        """
        Метод установки тестовых данных.

        Создадим тестовый набор пользователей для работы
        тестов, описанных ниже.
        """

        self.users = self.__generate_test_users(5)
        self.factory = APIRequestFactory()

    @staticmethod
    def __generate_test_users(count_test_users: int) -> List[User]:
        """
        Метод генерации списка тестовых пользователей.

        :param count_test_users: Количество тестовых пользователей.
        :return:
            Возвращает список с тестовыми пользователям,
            которые еще не сохранены в БД.
        """

        test_users = [
            User(
                username=f'username_{i}',
                password=f'my_VERY_safe_pass_{i}',
                email=f'user{i}@user.com',
            ) for i in range(count_test_users)
        ]

        User.objects.bulk_create(test_users)
        # Т.к. .bulk_create не вызывает метод save у записей
        # модели, а нам нужно знать поле id, запрашиваем
        # только что записанные во временную БД данные.
        test_users = User.objects.all()

        # Создадим тестовые профили.
        for user in test_users:
            new_profile = Profile(
                user=user,
                gender=random.choice(['M', 'F']),
                longitude=random.randint(-180, 180),
                latitude=random.randint(-180, 180),
            )
            new_profile.save()

        return test_users

    def test_user_registration(self) -> None:
        """Тест регистрации пользователя"""

        # Для сравнения кол-ва юзеров после регистрации нового.
        old_count_users = User.objects.count()
        # Вынесем в отдельную переменную юзернем, т.к. по
        # нему поймем, что действительно добавлен был нужный юзер.
        username = 'reg_user'

        url = reverse('api_registration')
        response = self.client.post(url, {
            'username': username,
            'password': 'my_VERY_safe_pass_1',
            'confirm_password': 'my_VERY_safe_pass_1',
            'email': 'reg_user@user.com',
            'first_name': 'reg',
            'last_name': 'user',
            'profile': {
                'gender': 'M',
                'longitude': 100,
                'latitude': -100,
            },
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), old_count_users + 1)
        self.assertEqual(User.objects.filter(username=username)
                         .first().username, username)

    def test_user_detail_view(self) -> None:
        """Тест получения информации о пользователе"""

        current_user = self.users[0]

        url = reverse('api_user_detail', args=(current_user.pk, ))
        view = views.UserDetailView.as_view()

        request = self.factory.get(url)
        force_authenticate(request, current_user)

        response = view(request, pk=current_user.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['pk'], current_user.pk)
        self.assertEqual(response.data['username'], current_user.username)

    def test_user_list_view(self) -> None:
        """Тест получения списка пользователей"""

        current_user = self.users[0]

        url = reverse('api_user_list')
        view = views.UserListView.as_view()

        request = self.factory.get(url)
        force_authenticate(request, current_user)

        response = view(request)

        users = serializers.UserSerializer(response.data, many=True)

        self.assertEqual(users.data, response.data)

    def test_lover_list_view(self) -> None:
        """Тест получения списка влюбленных"""

        current_user = self.users[0]

        url = reverse('api_lovers')
        view = views.LoverListView.as_view()

        request = self.factory.get(url)
        force_authenticate(request, current_user)

        response = view(request)

        users = serializers.UserSerializer(response.data, many=True)

        self.assertEqual(users.data, response.data)

    def test_like_user_view(self) -> None:
        """Тест оценивания юзера другим юзером"""

        current_user = self.users[0]
        liked_user = self.users[1]

        old_count_lovers = liked_user.profile.lovers.count()

        response = self.__user_rated_user(current_user, liked_user)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(liked_user.profile.lovers.count(),
                         old_count_lovers + 1)

    def test_mutual_sympathy(self) -> None:
        """Тест взаимной симпатии"""

        user_1 = self.users[0]
        user_2 = self.users[1]

        # Изначально равно 0.
        old_count_lovers_2 = user_2.profile.lovers.count()

        # user_1 оценивает user_2.
        # После этого у user_2 будет 1 поклонник.
        response_1 = self.__user_rated_user(user_1, user_2)

        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        self.assertEqual(user_2.profile.lovers.count(), old_count_lovers_2 + 1)

        # user_2 оценивает в ответ user_1.
        # После этого отправляются письма с сообщением о взаимной симпатии,
        # а счетчики влюбленных обнуляются.
        response_2 = self.__user_rated_user(user_2, user_1)

        self.assertEqual(response_1.status_code, status.HTTP_200_OK)
        self.assertEqual(user_1.profile.lovers.count(), 0)
        self.assertEqual(user_2.profile.lovers.count(), 0)

    def __user_rated_user(self, lover: User, beloved: User) -> Response:
        """Метод имитации оценки одного пользователя другим"""

        url = reverse('api_like_user', args=(beloved.pk,))
        view = views.LikeUserView.as_view()

        request = self.factory.post(url)
        force_authenticate(request, lover)

        response = view(request, pk=beloved.pk)

        return response
