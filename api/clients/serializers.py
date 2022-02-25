from pathlib import Path

from rest_framework import serializers
from rest_framework import validators
from rest_framework_simplejwt.tokens import (
    RefreshToken,
    TokenError,
)
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from clients.models import Profile
from date_me_please.settings import BASE_DIR
from clients.watermark import set_watermark


class LogoutSerializer(serializers.Serializer):
    """Сериализатор для рефреш-токена"""

    refresh = serializers.CharField()
    default_error_messages = {
        'bad_token': _('Токен уже истек или невалиден.'),
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail('bad_token')


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для модели профиля пользователя"""

    class Meta:
        """Класс настроек сериализатора"""

        model = Profile
        fields = ('avatar', 'gender',
                  'longitude', 'latitude')


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для API регистрации"""

    email = serializers.EmailField(
        required=True,
        validators=[
            validators.UniqueValidator(queryset=User.objects.all()),
        ],
        label=_('Эл. почта'),
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        label=_('Пароль'),
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
        label=_('Подтверждение пароля'),
    )
    first_name = serializers.CharField(
        required=True,
        label=_('Настоящее имя'),
    )
    last_name = serializers.CharField(
        required=True,
        label=_('Фамилия'),
    )
    profile = ProfileSerializer(label=_('Профиль'))

    class Meta:
        """Класс настроект сериализатора"""

        model = User
        fields = ('username', 'password', 'confirm_password',
                  'email', 'first_name', 'last_name', 'profile')

    def validate(self, attrs: dict) -> dict:
        """Метод валидации данных"""

        # Проверяем пароли на совпадение.
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'password': 'Пароли должны совпадать.'
            })

        return attrs

    def create(self, validated_data: dict) -> User:
        """Метод записи данных в БД"""

        # Сначала создаем пользователя в БД.
        new_user = User(
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            email=validated_data['email'],
        )
        new_user.set_password(validated_data['password'])
        new_user.save()

        # Затем создаем и связываем профиль пользователя.
        profile_data = validated_data['profile']
        new_profile = Profile.objects.create(
            user=new_user,
            avatar=profile_data['avatar'] if 'avatar' in
                                             profile_data.keys() else None,
            gender=profile_data['gender'],
            longitude=profile_data['longitude'],
            latitude=profile_data['latitude'],
        )

        # Если пользователь загрузил аватарку, обработаем ее.
        if 'avatar' in profile_data.keys():
            set_watermark(str(BASE_DIR) + str(new_profile.avatar.url),
                          BASE_DIR / 'staticfiles/clients/img/watermark.png',
                          (0, 0))

        return new_user


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользовательских данных"""

    profile = ProfileSerializer(read_only=True)
    distance_to_user = serializers.FloatField(required=False)

    class Meta:
        """Класс настроек сериализатора"""

        model = User
        fields = ('pk', 'username', 'first_name',
                  'last_name', 'email', 'profile',
                  'distance_to_user')
