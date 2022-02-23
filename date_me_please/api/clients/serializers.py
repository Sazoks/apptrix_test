from rest_framework import serializers
from rest_framework import validators
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from clients.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для модели профиля пользователя"""

    class Meta:
        """Класс настроек сериализатора"""
        model = Profile
        fields = ('avatar', 'gender')


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для API регистрации"""

    email = serializers.EmailField(
        required=True,
        validators=[validators.UniqueValidator(queryset=User.objects.all())],
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    confirm_password = serializers.CharField(
        write_only=True,
        required=True,
    )
    profile = ProfileSerializer()

    class Meta:
        """Класс настроект сериализатора"""
        model = User
        fields = ('username', 'password', 'confirm_password',
                  'email', 'profile')

    def validate(self, attrs):
        """Метод валидации"""

        # Проверяем пароли на совпадение.
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'password': 'Пароли должны совпадать.'})

        return attrs

    def create(self, validated_data):
        """Метод записи данных в БД"""

        # Сначала создаем пользователя в БД.
        new_user = User(
            username=validated_data['username'],
            email=validated_data['email'],
        )
        new_user.set_password(validated_data['password'])
        new_user.save()

        # Затем создаем и связываем профиль пользователя.
        profile_data = validated_data['profile']
        Profile.objects.create(
            user=new_user,
            gender=profile_data['gender'],
        )

        return new_user
